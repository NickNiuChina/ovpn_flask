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
import sqlalchemy.types as types
from sqlalchemy.sql import func

import datetime


Base = declarative_base()

# https://stackoverflow.com/questions/6262943/sqlalchemy-how-to-make-django-choices-using-sqlalchemy
class ChoiceType(types.TypeDecorator):
    """
    Self-defined the status type
    """
    impl = types.String

    def __init__(self, choices, **kw):
        self.choices = dict(choices)
        super(ChoiceType, self).__init__(**kw)

    def process_bind_param(self, value, dialect):
        return [k for k, v in self.choices.items() if v == value][0]

    def process_result_value(self, value, dialect):
        return self.choices[value]


class User(Base):
    """ 
    User table ORM
    """
    __tablename__ = "users"

    # https://sqlalchemy-utils.readthedocs.io/en/latest/data_types.html#module-sqlalchemy_utils.types.choice
    status_choice = [
        (0, "disabled"),
        (1, "enabled")
    ]

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
    status: Mapped[int] = mapped_column(ChoiceType(status_choice))
    
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r})"
    

class UserGroup(Base):
    """ 
    Group table ORM
    """
    __tablename__ = "user_group"
    __table_args__ = (
        UniqueConstraint('group'),
    )
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group: Mapped[str] = mapped_column(String(50))
    
    def __repr__(self) -> str:
        return f"Group(id={self.id!r}, group={self.group!r})"


class OvpnServers(Base):
    """
    OpenVPN servers table ORM
    """    
    STATUS_CHOICE = {0: "disabled", 1: "enabled"}
    
    __tablename__ = "ovpn_servers"
    __table_args__ = (
        UniqueConstraint('server_name'),
    )
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    server_name: Mapped[str] = mapped_column(String(50))
    configuration_dir: Mapped[str] = mapped_column(String(200))
    configuration_file: Mapped[str] = mapped_column(String(200))
    status_file: Mapped[str] = mapped_column(String(200))
    log_file_dir: Mapped[str] = mapped_column(String(200))
    log_file: Mapped[str] = mapped_column(String(200))
    startup_type: Mapped[int] = mapped_column(ChoiceType({0: "sysv", 1: "systemd"}))
    startup_service: Mapped[str] = mapped_column(String(200))
    certs_dir: Mapped[str] = mapped_column(String(200))
    learn_address_script: Mapped[int] = mapped_column(ChoiceType({0: "disabled", 1: "enabled"}))
    managed: Mapped[int] = mapped_column(ChoiceType({0: "disabled", 1: "enabled"}))
    management_port: Mapped[int] = mapped_column(Integer)
    management_password: Mapped[str] = mapped_column(String(100))
    comment: Mapped[str] = mapped_column(String(1024))
    creation_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    update_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

class OvpnClientList(Base):
    """
    OpenVPN client model
    """
    __tablename__ = "ovpn_clients_list"
    __table_args__ = (
        UniqueConstraint('cn'),
    )
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    server: Mapped[UUID] = mapped_column(
        ForeignKey("ovpn_servers.id")
    )
    site_name: Mapped[str] = mapped_column(String(100))
    cn: Mapped[str] = mapped_column(String(100))
    ip: Mapped[str] = mapped_column(String(100))
    toggle_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
        )
    STATUS_CHOICE = [(0, "offline"), (1, "online")]
    ENABLED_CHOICE = [(0, "disabled"), (1, "enabled")]
    enabled: Mapped[int] = ChoiceType({0: "disabled", 1: "enabled"})
    status: Mapped[int] = ChoiceType({0: "disabled", 1: "enabled"})
    expire_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )  # (1970, 1, 1))
    create_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    update_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ClientListConfig(Base):
    """
    OpenVPN client proxy config model
    """
    __tablename__ = "ovpn_clients_config"

    OS_TYPE_CHOICE = [(0, "Linux"), (1, "Windows"), (2, "MacOS"), (3, "Others")]
    PROXY_CHOICE = [(0, "disabled"), (1, "enabled")]
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ovpn_client: Mapped[UUID] = mapped_column(
        ForeignKey("ovpn_servers.id")
    )
    os_type: Mapped[int] = ChoiceType({0: "Linux", 1: "Windows", 2: "MacOS", 3: "Others"})
    http_proxy: Mapped[int] = ChoiceType({0: "Disabled", 1: "Enabled"})
    https_proxy: Mapped[int] = ChoiceType({0: "Disabled", 1: "Enabled"})
    http_port: Mapped[str] = mapped_column(String(100))
    https_port: Mapped[str] = mapped_column(String(100))
    http_proxy_template: Mapped[str] = mapped_column(String(1024))
    ssh_proxy: Mapped[int] = ChoiceType({0: "Disabled", 1: "Enabled"})
    ssh_proxy_port: Mapped[int] = mapped_column(Integer)
    create_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    update_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    
class OvpnCommonConfig(Base):
    """
    Ovpn common config model
    """
    __tablename__ = "ovpn_common_config"
       
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proxy_server: Mapped[int] = ChoiceType({0: "nginx", 1: "apache"})
    plain_req_file_dir: Mapped[str] = mapped_column(String(200)) # default="plain_reqs")
    encrypt_req_file_dir: Mapped[str] = mapped_column(String(200)) #  default="encrypt_reqs")
    plain_cert_file_dir: Mapped[str] = mapped_column(String(200)) # default='plain_certs')
    encrypt_cert_file_dir: Mapped[str] = mapped_column(String(200)) # default="encrypt_certs")
    zip_cert_dir: Mapped[str] = mapped_column(String(200)) # default="zip_certs")
    
    # Use this method to initial
    @classmethod
    def initial(cls):
        print( cls.__name__ + " model initial method executed!")
        sc = cls.objects.all().first()
        if not sc:
            nc = cls()
            nc.save()

    def __str__(self):
        return '{0.name}({0.username})'.format(self)
    

class SystemCommonConfig(Base):
    """
    System wide common config model
    """
    __tablename__ = "system_config"
       
    site_name: Mapped[str] = mapped_column(String(200), default='Unnamed')