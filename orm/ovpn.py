from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String
from typing import Optional
from typing import List
from sqlalchemy.dialects.postgresql import UUID
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, ForeignKeyConstraint, Integer, \
    SmallInteger, Text, UniqueConstraint, text, Numeric, Date, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50))
    password: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(40))
    email: Mapped[str] = mapped_column(String(100))
    group: Mapped[List["Address"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    log_size: Mapped[int] = mapped_column(Integer)
    page_size: Mapped[int] = mapped_column(Integer)
    status: Mapped[int] = mapped_column(Integer)
    
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r})"
    

# class UserGroup(Base):
#     __tablename__ = "address"
#     id: Mapped[int] = mapped_column(primary_key=True)
#     email_address: Mapped[str]
#     user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
#     user: Mapped["User"] = relationship(back_populates="addresses")
#     def __repr__(self) -> str:
#         return f"Address(id={self.id!r}, email_address={self.email_address!r})"
