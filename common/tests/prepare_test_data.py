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

if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] not in ["add", "remove"]):
    print("""
    Usage:
        python {} add/remove
    """.format(sys.argv[0]))
    exit(1)
users = dbsession.query(User).all()
if len(sys.argv) < 2 or sys.argv[1] == "add":
    for i in range(201):
        user = 'user' + str(i)
        u = dbsession.query(dbsession.query(User).filter(User.username == user).exists()).scalar()
        if not u:
            dbsession.add(User(
                username='user' + str(i),
                password=generate_password_hash(user),
                name='user' + str(i),
                email='user{}@example.com'.format(str(i)),
                group_id=dbsession.scalar(select(UserGroup).where(UserGroup.group == 'ADMIN')).id
            ))
    dbsession.commit()

else:
    for i in range(201):
        user = 'user' + str(i)
        u = dbsession.scalars(select(User).where(User.username == user)).one()
        if u:
            dbsession.delete(u)
    dbsession.commit()
