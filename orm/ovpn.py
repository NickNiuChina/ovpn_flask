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

from sqlalchemy.types import types

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
    
    id: Mapped[int] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    
    id: Mapped[int] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    comment: Mapped[str] = mapped_column(Text(1024))
    creation_time = models.DateTimeField(default=datetime.datetime.now, null=False, blank=False)
    update_time = models.DateTimeField(auto_now=True, null=False, blank=False)


class ClientList(models.Model):
    """OpenVPN client model"""
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    server = models.ForeignKey(
        Servers,
        verbose_name=_('server'),
        blank=False,
        null=False,
        on_delete=models.CASCADE)
    site_name = models.CharField(max_length=100, null=True, blank=True)
    cn = models.CharField(max_length=100, null=False, blank=False, unique=True)
    ip = models.CharField(max_length=20, null=False, blank=False, unique=True)
    toggle_time = models.DateTimeField(default=now)
    STATUS_CHOICE = [(0, "offline"), (1, "online")]
    ENABLED_CHOICE = [(0, "disabled"), (1, "enabled")]
    enabled = models.IntegerField(choices=ENABLED_CHOICE, default=1)
    status = models.IntegerField(choices=STATUS_CHOICE, default=1)
    expire_date = models.DateField(default=datetime.datetime(1970, 1, 1))
    create_time = models.DateTimeField(_('creation time'), default=now)
    update_time = models.DateTimeField(_('modify time'), default=now)


class ClientListConfig(models.Model):
    """OpenVPN client proxy config model"""
    validate_comma_separated_integer_list = int_list_validator(
        message=_("Enter only digits separated by commas."),
    )
    OS_TYPE_CHOICE = [(0, "Linux"), (1, "Windows"), (2, "MacOS"), (3, "Others")]
    PROXY_CHOICE = [(0, "disabled"), (1, "enabled")]
    
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    ovpn_client = models.ForeignKey(
        ClientList,
        verbose_name=_('ovpn_client'),
        blank=False,
        null=False,
        on_delete=models.CASCADE)
    os_type = models.IntegerField(choices=OS_TYPE_CHOICE, default=0, null=True, blank=True)
    http_proxy = models.IntegerField(choices=PROXY_CHOICE, default=0, null=True, blank=True)
    https_proxy = models.IntegerField(choices=PROXY_CHOICE, default=0, null=True, blank=True)
    http_port = models.CharField(validators=[validate_comma_separated_integer_list], max_length=200, null=True, blank=True)
    https_port = models.CharField(validators=[validate_comma_separated_integer_list], max_length=200, null=True, blank=True)
    http_proxy_template = models.TextField(max_length=2000, null=True, blank=True)
    ssh_proxy = models.IntegerField(choices=PROXY_CHOICE, default=0)
    ssh_proxy_port = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(22), MaxValueValidator(65536)]
    )
    create_time = models.DateTimeField(_('creation time'), default=now)
    update_time = models.DateTimeField(_('modify time'), default=now)
    
    
class SystemCommonConfig(Base):
    """System wide common config model"""
    PROXY_SERVER_CHOICE = [(0, "nginx"), (1, "apache")]
    
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    proxy_server = models.IntegerField(choices=PROXY_SERVER_CHOICE, default=1, null=True, blank=True)
    plain_req_file_dir = models.CharField(max_length=200, null=False, blank=False, default="plain_reqs")
    encrypt_req_file_dir = models.CharField(max_length=200, null=False, blank=False, default="encrypt_reqs")
    plain_cert_file_dir = models.CharField(max_length=200, null=True, blank=False, default='plain_certs')
    encrypt_cert_file_dir = models.CharField(max_length=200, null=False, blank=False, default="encrypt_certs")
    zip_cert_dir = models.CharField(max_length=200, null=False, blank=False, default="zip_certs")
    
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