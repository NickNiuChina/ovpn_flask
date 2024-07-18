import click
from flask.cli import with_appcontext
from myproject.context import logger


def init_db():
    """Clear existing data and create new tables."""
    from myproject.context import engine
    from orm.ovpn import Base
    logger.debug("Run the flask command: initialize-db")
    # click.echo("Sqlalchemy tables initialized done.")
    logger.info("Sqlalchemy tables initialize started")
    Base.metadata.create_all(engine)
    logger.info("Sqlalchemy tables initialize done")
    
@click.command("initialize-db")
@with_appcontext
def init_db_command():
    """Create new tables for sqlalchemy"""
    init_db()


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.cli.add_command(init_db_command)