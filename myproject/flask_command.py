import click
from flask.cli import with_appcontext
from myproject.context import logger
from orm.ovpn import OfUser, OfGroup, OfSystemConfig, OvpnServers, OvpnClients
from sqlalchemy import select
from werkzeug.security import generate_password_hash
import uuid
import ipaddress

Stress_Num = 1000

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
        for i in range(1, Stress_Num+1):
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
        logger.info("- Check the ovpn_servers table now")
        service = "test1"
        result = dbsession.scalar(select(OvpnServers).where(OvpnServers.server_name == service))
        if not result:
            logger.debug("Add test ovpn service: {} to db".format(service))
            dbsession.add(OvpnServers(
                server_name=service, 
                configuration_dir='/etc/openvpn/test1', 
                configuration_file='test1.conf', 
                status_file='test1-status.log',
                log_file_dir='/var/log/',
                log_file='test1.log',
                startup_service='test1-ovpn.service',
                certs_dir='easyrsa',
                management_port=33333,
                management_password='123456789'
                ))
            dbsession.commit()
                    
        # table: ovpn_clients 
        logger.debug("- Check the ovpn_clients table, ovpn clients: test1-1000")
        service = "test1"
        result = dbsession.scalar(select(OvpnServers).where(OvpnServers.server_name == service))
        logger.debug("Check ovpn service: {}".format(service))
        if not result:
            logger.info(f"Add ovpn service to db ovpn_servers: test1")
            dbsession.add(OvpnServers(
                server_name=service, 
                configuration_dir='/etc/openvpn/test1', 
                configuration_file='test1.conf', 
                status_file='test1-status.log',
                log_file_dir='/var/log/',
                log_file='test1.log',
                startup_service='test1-ovpn.service',
                certs_dir='easyrsa',
                management_port=33333,
                management_password='123456789'
                ))
            dbsession.commit()
        else:
            logger.debug("- ovpn_clients table: ovpn servcie test1 has been added")        
            
        logger.debug("- Check the ovpn_clients table now")
        logger.info("- Check the fake test clients: test1-1000 ")
        start_ip = ipaddress.ip_address('10.168.0.0')
        for i in range(1, Stress_Num+1):
            start_ip = start_ip + 1
            site_name = "test{}".format(str(i))
            cn = "test-{}".format(str(uuid.uuid4()))
            result = dbsession.scalar(select(OvpnClients).where(OvpnClients.site_name == site_name))
            if not result:
                logger.debug("Add test client site_name: {} to db".format(site_name))
                dbsession.add(OvpnClients(
                    server_id=dbsession.scalar(select(OvpnServers).where(OvpnServers.server_name == 'test1')).id, 
                    site_name=site_name, 
                    cn=cn, 
                    ip=start_ip.exploded              
                    ))
                dbsession.commit()
                            
        logger.info("Test data added done!")
    else:
        """Delete test data."""
        
        # table: om_users 
        logger.info("- Check the user table now")
        logger.info("- Check the test 1-1000 users list")
        for i in range(1, Stress_Num+1):
            username = "test{}".format(str(i))
            result = dbsession.scalar(select(OfUser).where(OfUser.username == username))
            if result:
                logger.debug("Delete test user: {}".format(username))
                dbsession.delete(result)
                dbsession.commit()
                        
        # table: om_group
        logger.debug("- Check the om_group table group: TEST")
        group = "TEST"
        result = dbsession.scalar(select(OfGroup).where(OfGroup.name == group))
        logger.debug("Check group: {} {}".format(group, str(result)))
        if result:
            logger.info(f"Delete group from db {group}")
            dbsession.delete(result)
            dbsession.commit()    
                    
        # table: ovpn_clients 
        logger.debug("- Check the ovpn_clients table, ovpn clients: test1-1000") 
        logger.debug("- Check the ovpn_clients table now")
        for i in range(1, Stress_Num+1):
            site_name = 'test{}'.format(str(i))
            result = dbsession.scalar(select(OvpnClients).where(OvpnClients.site_name == site_name))
            if result:
                logger.debug("Delete test client site_name: {}".format(site_name))
                dbsession.delete(result)
                dbsession.commit()

        # table: ovpn_servers
        logger.debug("- Check the ovpn_servers table, ovpn service: test1 ")
        logger.info("- Check the ovpn_servers table now")
        service = "test1"
        result = dbsession.scalar(select(OvpnServers).where(OvpnServers.server_name == service))
        if result:
            logger.debug("Delete test ovpn service: {}".format(service))
            dbsession.delete(result)
            dbsession.commit()
                                        
        logger.info("Test data deleted done!")