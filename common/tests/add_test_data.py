import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
working_dir = str(BASE_DIR)
if working_dir not in sys.path:
    sys.path.append(working_dir)

from orm.ovpn import User
from orm.ovpn import UserGroup
from myproject.context import engine, DBSession as dbsession
from orm.ovpn import Base
from werkzeug.security import generate_password_hash

from sqlalchemy import select

users = dbsession.query(User).all()
if len(users) < 20:
    for i in range(201):
        dbsession.add(User(
            username='user' + str(i),
            password=generate_password_hash('user' + str(i)),
            name='user' + str(i),
            email='user{}@example.com'.format(str(i)),
            group_id=dbsession.scalar(select(UserGroup).where(UserGroup.group == 'ADMIN')).id
        ))

    dbsession.commit()
else:
    print("Data should be added before")
