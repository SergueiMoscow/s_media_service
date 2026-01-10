#!/usr/bin/env bash
set -euo pipefail
source ./.env

# ==================== НАСТРОЙКИ ====================
HOST="http://localhost:8081"
#USER_ID="from .env file"

FILE_PATH="images/test.png"

ORIGINAL_FILENAME="test_photo.png"
NOTE="Test button"
TAGS="test_tag1,test_tag2"
IS_PUBLIC="true"

# ==================== ПРОВЕРКИ ====================
if [[ ! -f "$FILE_PATH" ]]; then
    echo "Ошибка: файл $FILE_PATH не найден!"
    exit 1
fi

# ==================== ЭКРАНИРОВАНИЕ ПАРАМЕТРОВ ====================
# Безопасное URL-кодирование (jq должен быть установлен)
encoded_filename=$(printf '%s' "$ORIGINAL_FILENAME" | jq -sRr @uri 2>/dev/null || echo "$ORIGINAL_FILENAME" | tr ' ' '%20')
encoded_note=$(printf '%s' "$NOTE" | jq -sRr @uri 2>/dev/null || echo "$NOTE" | tr ' ' '%20')
encoded_tags=$(printf '%s' "$TAGS" | jq -sRr @uri 2>/dev/null || echo "$TAGS" | tr ' ' '%20')

# ==================== ЗАГРУЗКА ====================
echo "→ Отправляем файл на $HOST/upload ..."

# Делаем запрос, код статуса в отдельный файл
curl -s \
    -X POST "${HOST}/upload?original_filename=${encoded_filename}&note=${encoded_note}&tags=${encoded_tags}&is_public=${IS_PUBLIC}" \
    -H "X-User-ID: ${USER_ID}" \
    -H "Content-Type: application/octet-stream" \
    --data-binary @"${FILE_PATH}" \
    -o upload_response.body \
    -w "%{http_code}" > upload_response.status

http_code=$(cat upload_response.status)
body=$(cat upload_response.body)

echo "HTTP код: $http_code"

if [[ "$http_code" = "200" ]]; then
    echo "Успех! Ответ сервера:"
    echo "$body" | jq . 2>/dev/null || echo "$body (невалидный JSON)"
else
    echo "Ошибка! Код: $http_code"
    echo "Ответ сервера:"
    echo "$body"
    exit 1
fi

# ==================== ИЗВЛЕЧЕНИЕ ID ====================
file_id=$(echo "$body" | jq -r '.file.id // empty' 2>/dev/null)

if [[ -n "$file_id" && "$file_id" != "null" ]]; then
    echo
    echo "Создан файл с ID: $file_id"
    echo "Проверить можно так:"
    echo "curl -s \"${HOST}/catalog/preview/${file_id}\" -H \"X-User-ID: ${USER_ID}\""
else
    echo "ID файла не найден в ответе"
fi

# ==================== ОЧИСТКА ====================
rm -f upload_response.status upload_response.body

echo
echo "Готово!"