import click
from flask.cli import with_appcontext
from myproject.context import logger
from orm.ovpn import User, UserGroup
from sqlalchemy import select
from werkzeug.security import generate_password_hash

def init_db():
    """Clear existing data and create new tables."""
    from myproject.context import engine, DBSession as dbsession
    from orm.ovpn import Base
    logger.debug("Run the flask command: initialize-db")
    # click.echo("Sqlalchemy tables initialized done.")
    logger.info("Sqlalchemy tables initialize started")
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    
    new_groups = []
    logger.info("Check the user_group table now.")
    for group in ['ADMIN', 'SUPER', 'USER', "GUEST" ]:
        result = dbsession.scalar(select(UserGroup).where(UserGroup.group == group))
        logger.debug("Check group: {} {}".format(group, str(result)))
        if not result:
            logger.debug(f"Add group to db {group}")
            new_groups.append(UserGroup(group=group))
    if new_groups:
        dbsession.add_all(new_groups)
        dbsession.commit()
    logger.info("Check the user table now")
    result = dbsession.scalar(select(User).where(User.username == 'super'))
    if not result:
        logger.debug(f"Add super user to db")
        dbsession.add(User(
            username='super', 
            password=generate_password_hash('super'), 
            name='super', 
            email='super@example.com', 
            group_id=dbsession.scalar(select(UserGroup).where(UserGroup.group == 'SUPER')).id
            ))
        dbsession.commit()
    logger.info("Sqlalchemy tables initialize done")
@click.command("initialize-db")
@with_appcontext
def init_db_command():
    """
    Create tables for sqlalchemy if not existed,
    And, create default user or group if not existed.
    """
    init_db()


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.cli.add_command(init_db_command)