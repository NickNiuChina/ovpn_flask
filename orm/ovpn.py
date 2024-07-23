from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String
from typing import Optional
from typing import List
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy import UniqueConstraint

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, ForeignKeyConstraint, Integer, \
    SmallInteger, Text, UniqueConstraint, text, Numeric, Date, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50))
    password: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(40))
    email: Mapped[str] = mapped_column(String(100))
    group_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_group.id")
    )
    log_size: Mapped[int] = mapped_column(Integer)
    page_size: Mapped[int] = mapped_column(Integer)
    status: Mapped[int] = mapped_column(Integer)
    
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r})"
    

class UserGroup(Base):
    __tablename__ = "user_group"
    __table_args__ = (
        UniqueConstraint('group'),
    )
    
    id: Mapped[int] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group: Mapped[str] = mapped_column(String(50))
    
    def __repr__(self) -> str:
        return f"Group(id={self.id!r}, group={self.group!r})"
