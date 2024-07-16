# coding: utf-8
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, ForeignKeyConstraint, Integer, \
    SmallInteger, Text, UniqueConstraint, text, Numeric, Date, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class DsDevice(Base):
    __tablename__ = 'ds_device'

    device_uid = Column(Text, primary_key=True)
    source_system_id = Column(SmallInteger, nullable=False)
    tenant_id = Column(Text, nullable=False)
    plant_id = Column(Text, nullable=False)
    line_id = Column(Integer)
    model_id = Column(Integer, nullable=False)
    device_id = Column(Integer, nullable=False)
    device_code_name = Column(Text)
    device_lang_description_en = Column(Text)
    is_deleted = Column(Boolean, server_default=text("false"))