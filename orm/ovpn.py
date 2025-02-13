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
# https://docs.sqlalchemy.org/en/20/core/custom_types.html
# relationship
# https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html


class ChoiceType(types.TypeDecorator):
    """
    Self-defined the status type
    """
    impl = types.Integer
    # cache_ok = True
    
    def __init__(self, choices, **kw):
        self.choices = dict(choices)
        super(ChoiceType, self).__init__(**kw)

    def process_bind_param(self, value, dialect):
        if [k for k, v in self.choices.items() if k == value]:
            return value
        else:
            return 0

    def process_result_value(self, value, dialect):
        # return self.choices[value]
        # if [k for k, v in self.choices.items() if k == value]:
        #     return self.choices[value]
        # else:
        #     return 'disabled'
        return value


class OfGroup(Base):
    """ 
    Group table ORM
    """
    __tablename__ = "om_group"
    __table_args__ = (
        UniqueConstraint('name'),
    )
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50))
    users: Mapped[list["OfUser"]] = relationship(
        "OfUser",
        back_populates="group",
        cascade="all, delete",
    )

    def __repr__(self) -> str:
        return f"Group(id={self.id!r}, group={self.name!r})"


class OfUser(Base):
    """ 
    User table ORM
    """
    __tablename__ = "om_users"
    __table_args__ = (
        UniqueConstraint('username'),
    )

    # https://sqlalchemy-utils.readthedocs.io/en/latest/data_types.html#module-sqlalchemy_utils.types.choice
    status_choice = [
        (0, "disabled"),
        (1, "enabled")
    ]

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50))
    password: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(40))
    email: Mapped[str] = mapped_column(String(100))
    group_id: Mapped[UUID] = mapped_column(
        ForeignKey("om_group.id")
    )
    group: Mapped[OfGroup] = relationship(
        "OfGroup",
        back_populates="users",
    )
    line_size: Mapped[int] = mapped_column(ChoiceType({300: 300, 1000: 1000, 3000: 3000, -1: 'All'}), default=300)
    page_size: Mapped[int] = mapped_column(ChoiceType({50: 50, 100: 100, 200: 200, 500: 500, -1: 'All'}), default=50)
    status: Mapped[int] = mapped_column(ChoiceType({1: "enabled", 0: "disabled"}), default=1)
    
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r})"


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
    startup_type: Mapped[int] = mapped_column(ChoiceType({0: "sysv", 1: "systemd"}), default=1)
    startup_service: Mapped[str] = mapped_column(String(200))
    certs_dir: Mapped[str] = mapped_column(String(200))
    learn_address_script: Mapped[int] = mapped_column(ChoiceType({0: "disabled", 1: "enabled"}), default=1)
    managed: Mapped[int] = mapped_column(ChoiceType({0: "disabled", 1: "enabled"}), default=1)
    management_port: Mapped[int] = mapped_column(Integer)
    management_password: Mapped[str] = mapped_column(String(100))
    comment: Mapped[str] = mapped_column(String(1024), nullable=True)
    creation_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    update_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

class OvpnClients(Base):
    """
    OpenVPN client model
    """
    __tablename__ = "ovpn_clients"
    __table_args__ = (
        UniqueConstraint('cn'),
        UniqueConstraint("server_id", "site_name"),
    )
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    server_id: Mapped[UUID] = mapped_column(
        ForeignKey("ovpn_servers.id")
    )
    site_name: Mapped[str] = mapped_column(String(100), nullable=True)
    cn: Mapped[str] = mapped_column(String(100))
    ip: Mapped[str] = mapped_column(String(100))
    toggle_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
        )
    enabled: Mapped[int] = mapped_column(ChoiceType({0: "disabled", 1: "enabled"}), default=1)
    status: Mapped[int] = mapped_column(ChoiceType({0: "disabled", 1: "enabled"}), default=1)
    expire_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )  # (1970, 1, 1))
    create_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    update_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def toDict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class ClientListConfig(Base):
    """
    OpenVPN client proxy config model
    """
    __tablename__ = "ovpn_client_config"

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
    

class OfSystemConfig(Base):
    """
    System wide common config model
    """
    __tablename__ = "om_system_config"
    
    # id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)   
    item: Mapped[str] = mapped_column(String(50), primary_key=True)
    ivalue: Mapped[str] = mapped_column(String(200), nullable=True)
    category: Mapped[str] = mapped_column(String(50), default='dedicated')