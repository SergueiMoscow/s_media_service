import shutil
from datetime import datetime
from pathlib import Path
from uuid import UUID

from io import BytesIO
from fastapi import UploadFile

from db.models import Storage, StorageStatistic
from repositories.storages import get_storage_for_new_file_by_user
from db.connector import AsyncSession


async def get_full_path_for_new_file(
    user_id: UUID,
    file: UploadFile,
) -> Path:
    """
    Возвращает уникальный полный путь для сохранения нового файла.
    Формат: storage.path / YYYY / MM / filename.ext
    Если файл с таким именем уже существует — добавляет _1, _2 и т.д.
    """
    async with AsyncSession() as session:
        storage: Storage | None = await get_storage_for_new_file_by_user(session=session, user_id=user_id)

    if not storage:
        raise ValueError("No available storage with can_add=True for this user")

    # Базовый путь из хранилища
    base_path = Path(storage.path)

    # Создаём подпапки по текущей дате: YYYY/MM
    now = datetime.now()
    date_path = base_path / now.strftime("%Y") / now.strftime("%m")

    # Оригинальное имя файла
    original_filename = Path(file.filename or "unnamed_file").name
    stem = original_filename.rsplit(".", 1)[0] if "." in original_filename else original_filename
    suffix = "".join(original_filename.rsplit(".", 1)[1:])  # расширение с точкой, если есть
    if suffix:
        suffix = f".{suffix}"

    # Начинаем с оригинального имени
    candidate_path = date_path / original_filename
    counter = 1

    # Проверяем существование файла и генерируем уникальное имя
    while candidate_path.exists():
        new_filename = f"{stem}_{counter}{suffix}"
        candidate_path = date_path / new_filename
        counter += 1

    # Важно: создаём директории, если их нет
    candidate_path.parent.mkdir(parents=True, exist_ok=True)

    return candidate_path


async def save_uploaded_file(
    user_id: UUID,
    file: UploadFile,
) -> dict:
    """
    Сохраняет загруженный файл на диск в соответствующем хранилище.

    Возвращает словарь с информацией о сохранённом файле:
    - full_path: полный путь на диске
    - relative_path: путь относительно корня хранилища (например, "2026/01/photo.jpg")
    - filename: имя файла на диске (с суффиксом при необходимости)
    - size: размер в байтах
    """
    # Получаем уникальный путь для сохранения
    save_path: Path = await get_full_path_for_new_file(user_id=user_id, file=file)

    # Сохраняем файл потоково (эффективно для больших файлов)
    try:
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        # Всегда закрываем файл от FastAPI
        await file.close()

    # Получаем размер сохранённого файла
    file_size = save_path.stat().st_size

    # Обновляем статистику хранилища
    async with AsyncSession() as session:
        async with session.begin():
            storage = await get_storage_for_new_file_by_user(session=session, user_id=user_id)
            if not storage or not storage.statistic:
                # Можно выбросить исключение, если критична целостность
                raise RuntimeError("Storage or statistic not found")

            statistic: StorageStatistic = storage.statistic
            statistic.total_files += 1
            statistic.used_space += file_size

        await session.commit()

    # Формируем относительный путь (для будущей записи в БД и отдачи клиенту)
    base_storage_path = Path(storage.path)
    relative_path = save_path.relative_to(base_storage_path)

    return {
        "storage_id": storage.id,
        "full_path": str(save_path),
        "relative_path": str(relative_path),
        "filename": save_path.name,
        "size": file_size,
        "uploaded_at": datetime.now(),
        "content_type": file.content_type,
    }


async def save_uploaded_file_raw(
    user_id: UUID,
    file_content: bytes,
    original_filename: str,
    content_type: str = "application/octet-stream",
) -> dict:
    if not file_content:
        raise ValueError("Empty file content")
    if not original_filename:
        raise ValueError("Original filename required")

    # Фейковый UploadFile для генерации пути
    fake_file_obj = BytesIO(file_content)
    fake_upload = UploadFile(
        filename=original_filename,
        file=fake_file_obj,
    )

    # Получаем путь
    save_path: Path = await get_full_path_for_new_file(user_id=user_id, file=fake_upload)

    # Сохраняем файл
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(file_content)

    file_size = len(file_content)

    # Обновляем статистику — правильный способ
    async with AsyncSession() as session:
        storage = await get_storage_for_new_file_by_user(session=session, user_id=user_id)
        if not storage:
            raise RuntimeError("No available storage for upload")
        if storage.statistic:
            # raise RuntimeError("Storage statistic not found")
            storage.statistic.total_files += 1
            storage.statistic.used_space += file_size

        # Явно коммитим
        await session.commit()

        # Получаем storage_id после коммита (на всякий случай)
        # await session.refresh(storage)  # опционально, если нужно актуальное состояние
        storage_id = storage.id

    # Относительный путь
    relative_path = save_path.relative_to(Path(storage.path))

    return {
        "full_path": str(save_path),
        "relative_path": str(relative_path),
        "filename": save_path.name,
        "size": file_size,
        "storage_id": storage_id,
        "uploaded_at": datetime.now(),
        "content_type": content_type,
    }
