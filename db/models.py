import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
    text,
)
from sqlalchemy.orm import backref, relationship

from db.db import Base

LAZY_TYPE = 'select'
GUID = Uuid


class StringSize(Enum):
    LENGTH_FILE_NAME: int = 255
    LENGTH_FILE_TYPE: int = 4
    LENGTH_FILE_DESCRIPTION: int = 255
    LENGTH_TAG: int = 30
    LENGTH_255: int = 255
    LENGTH_IP: int = 15


class Storage(Base):
    __tablename__ = 'storages'

    id = Column(GUID, nullable=False, default=uuid.uuid4, unique=True, primary_key=True)
    user_id = Column(GUID, nullable=False)  # Привязка к таблице из API service
    is_public = Column(Boolean, default=False)
    name = Column(String(255), nullable=False)
    path = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=text('NOW()'))
    created_by = Column(GUID, nullable=False)
    # files = relationship('File', backref=backref('storage'), lazy=LAZY_TYPE)
    statistic = relationship('StorageStatistic', backref=backref('storage'), lazy=LAZY_TYPE)


class StorageStatistic(Base):
    __tablename__ = 'storage_statistic'

    id = Column(BigInteger, primary_key=True)
    storage_id = Column(GUID, ForeignKey('storages.id'), nullable=False)
    path = Column(String(StringSize.LENGTH_255), nullable=False)
    files_count = Column(Integer(), nullable=False)
    folders_count = Column(Integer(), nullable=False)
    size = Column(Integer(), nullable=False)
    created_at = Column(DateTime, server_default=text('NOW()'), comment='Record creation time')

    Index('idx_storage_statistic_path_created_at', path, created_at.desc())


class File(Base):
    __tablename__ = 'files'

    id = Column(GUID, nullable=False, default=uuid.uuid4, unique=True, primary_key=True)
    size = Column(Integer)
    name = Column(String(StringSize.LENGTH_FILE_NAME))
    type = Column(String(StringSize.LENGTH_FILE_TYPE))
    note = Column(String(StringSize.LENGTH_FILE_DESCRIPTION), nullable=True, default=None)
    is_public = Column(Boolean, nullable=False, default=False)
    created = Column(DateTime, nullable=False, comment='File creation time')
    created_at = Column(DateTime, server_default=text('NOW()'), comment='Record creation time')
    tags = relationship('Tag', backref=backref('file', lazy=LAZY_TYPE), lazy=LAZY_TYPE)
    emoji = relationship('Emoji', backref='file', lazy=LAZY_TYPE)
    links = relationship('Link', backref='file', lazy=LAZY_TYPE)


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(GUID, nullable=False, default=uuid.uuid4, unique=True, primary_key=True)
    file_id = Column(GUID, ForeignKey('files.id'), nullable=False)
    name = Column(String(StringSize.LENGTH_TAG))
    ip = Column(String(StringSize.LENGTH_IP))
    created_by = Column(GUID)  # Нет связи, т.к. пользователь из другой базы.
    created_at = Column(DateTime, server_default=text('NOW()'), comment='Record creation time')


class Emoji(Base):
    __tablename__ = 'emoji'

    id = Column(GUID, nullable=False, default=uuid.uuid4, unique=True, primary_key=True)
    file_id = Column(GUID, ForeignKey('files.id'), nullable=False)
    name = Column(String(StringSize.LENGTH_TAG))
    created_by = Column(GUID)  # Нет связи, т.к. пользователь из другой базы.
    ip = Column(String(StringSize.LENGTH_IP))
    created_at = Column(DateTime, server_default=text('NOW()'), comment='Record creation time')


class Link(Base):
    __tablename__ = 'links'
    id = Column(GUID, nullable=False, default=uuid.uuid4, unique=True, primary_key=True)
    file_id = Column(GUID, ForeignKey('files.id'), nullable=False)
    created_by = Column(GUID)  # Нет связи, т.к. пользователь из другой базы.
    created_at = Column(DateTime, server_default=text('NOW()'))
    expire_at = Column(DateTime, server_default=text('NOW()'))
