import click
from flask.cli import with_appcontext
from myproject.context import logger
from orm.ovpn import OfUser, OfGroup, OfSystemConfig
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
    
    
    # table: om_group
    new_groups = []
    logger.info("- Check the user_group table now.")
    for group in ['ADMIN', 'SUPER', 'USER', "GUEST" ]:
        result = dbsession.scalar(select(OfGroup).where(OfGroup.name == group))
        logger.debug("Check group: {} {}".format(group, str(result)))
        if not result:
            logger.debug(f"Add group to db {group}")
            new_groups.append(OfGroup(name=group))
    if new_groups:
        dbsession.add_all(new_groups)
        dbsession.commit()
    
    # table: om_users 
    logger.info("- Check the user table now")
    result = dbsession.scalar(select(OfUser).where(OfUser.username == 'super'))
    if not result:
        logger.debug(f"Add super user to db")
        dbsession.add(OfUser(
            username='super', 
            password=generate_password_hash('super'), 
            name='super', 
            email='super@example.com', 
            group_id=dbsession.scalar(select(OfGroup).where(OfGroup.name == 'SUPER')).id
            ))
        dbsession.commit()
        
    # table: om_users 
    logger.info("- Check the user table now")
            
    logger.info("- Check the system_config table now")
    system_config_dict = {
        'CUSTOMER_SITE': 'Un-named', 
        'DIR_APACHE_ROOT': '/etc/apache2',
        'DIR_APACHE_SUB': 'site-enabled',
        "DIR_EASYRSA": '',
        "DIR_GENERIC_CLIENT": 'generic',
        "DIR_REQ": 'reqs',
        "DIR_REQ_DONE": 'reqs-done',
        #"DIR_TAP": '',
        #"DIR_TUN": '',
        "DIR_VALIDATED": 'validated',
        "DIR_VPN_SCRIPT": 'vpn_tool_script',
        "IP_PORT": '',
        "IP_REMOTE": '',
        "PROXY_PREFIX": ''
    }
    new_items = []
    for item in system_config_dict.keys():
        result = dbsession.scalar(select(OfSystemConfig).where(OfSystemConfig.item == item))
        logger.debug("Check item: {} {}".format(item, str(result)))
        if not result:
            logger.debug(f"Add item to db: {item}")
            new_items.append(OfSystemConfig(item=item, ivalue=system_config_dict[item]))
    if new_items:
        dbsession.add_all(new_items)
        dbsession.commit()
        
    logger.info("Sqlalchemy tables initialize done")
    
@click.command("prepare-data")
# @with_appcontext
@click.argument('action')
# @click.option('--toduhornot', is_flag=True, help='prints "duh..."')
def prepare_data_command(action):
    """
    Add or delete data to database for test purpose.
    
        add:\n
            add test data\n
        delete:\n
            delete test data
    """
    prepare_data(action)


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.cli.add_command(prepare_data_command)
    
from myproject.context import engine, DBSession as dbsession
from orm.ovpn import Base   
 
def prepare_data(action="add"):
    if action not in ("add", "delete"):
        logger.warning("Run command |prepare-data| without correct action: add or delete")
        return
    
    if action == "add":
        """Add test data."""
        
        # table: om_group
        logger.debug("- Check the om_group table group: TEST")
        group = "TEST"
        result = dbsession.scalar(select(OfGroup).where(OfGroup.name == group))
        logger.debug("Check group: {} {}".format(group, str(result)))
        if not result:
            logger.info(f"Add group to db {group}")
            dbsession.add(OfGroup(name=group))
            dbsession.commit()
        else:
            logger.debug("- Om_group table group: TEST has been added before!")        
            
        # table: om_users 
        logger.info("- Check the user table now")
        logger.info("- Check the test 1-1000 users list")
        for i in range(1, 1001):
            username = "test{}".format(str(i))
            result = dbsession.scalar(select(OfUser).where(OfUser.username == username))
            if not result:
                logger.debug("Add test user: {} to db".format(username))
                dbsession.add(OfUser(
                    username=username, 
                    password=generate_password_hash(username), 
                    name=username, 
                    email='{}@example.com'.format(username), 
                    group_id=dbsession.scalar(select(OfGroup).where(OfGroup.name == 'TEST')).id
                    ))
                dbsession.commit()
        
        # table: ovpn_servers
        logger.debug("- Check the ovpn_servers table, ovpn service: test1 ")
        
        # table: ovpn_clients 
        logger.debug("- Check the ovpn_clients table, ovpn clients: test1-1000")
            
        logger.info("Test data added done!")
    else:
        pass