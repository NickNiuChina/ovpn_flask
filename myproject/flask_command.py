import click
from flask.cli import with_appcontext
from myproject.context import logger
from orm.ovpn import User, UserGroup
from sqlalchemy import select


def init_db():
    """Clear existing data and create new tables."""
    from myproject.context import engine, DBSession as dbsession
    from orm.ovpn import Base
    logger.debug("Run the flask command: initialize-db")
    # click.echo("Sqlalchemy tables initialized done.")
    logger.info("Sqlalchemy tables initialize started")
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    logger.info("Sqlalchemy tables initialize done")
    
    new_groups = []
    for group in ['ADMIN', 'SUPER', 'USER', "GUEST" ]:
        result = dbsession.scalar(select(UserGroup).where(UserGroup.group == group))
        logger.debug("Check group: {} {}".format(group, str(result)))
        if not result:
            logger.debug(f"Add group to db {group}")
            new_groups.append(UserGroup(group=group))
    if new_groups:
        dbsession.add_all(new_groups)
        dbsession.commit() 
    
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