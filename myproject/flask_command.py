import click
from flask.cli import with_appcontext
from myproject.context import logger
from orm.ovpn import OfUser, OfGroup, OfSystemConfig, OvpnServers, OvpnClients, OvpnCommonConfig
from sqlalchemy import select
from werkzeug.security import generate_password_hash
import uuid
import ipaddress
import platform
import pathlib
import zipfile

Stress_Num = 1000

def check_db_integrity():
    """
        Check the database integrity.
    """
    from myproject.context import engine, DBSession as dbsession
    from orm.ovpn import Base
    logger.info("Check the database integrity now.")

    # Base.metadata.drop_all(engine)
    logger.debug("Run create all to create table if sone table or all tables not been created before!")
    Base.metadata.create_all(engine)
    
    # table: om_group
    new_groups = []
    logger.info("- Check the om_group table now.")
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
    logger.info("- Check the om_users table now")
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
        
    # table: om_system_config 
    logger.info("- Check the om_system_config table now")
    system_config_dict = {
        'CUSTOMER_SITE': 'Un-named', 
        'DIR_APACHE_ROOT': '/etc/apache2',
        'DIR_APACHE_SUB': 'site-enabled',
        "DIR_EASYRSA": 'easyrsa',
        "DIR_GENERIC_CLIENT": 'generic',
        "DIR_REQ_TMP": 'reqs_tmp',
        "DIR_CERT_ROOT": '/opt/certs_ovpn_flask',
        "DIR_REQS": 'reqs',
        "DIR_PLAIN_CERTS": 'plain_certs',
        "DIR_ENCRYPT_CERTS": 'encrypt_certs',
        "DIR_ZIP_CERTS": 'zip_certs',
        "DIR_VPN_SCRIPT": 'vpn_tool_script',
        "ZIP_EASYRSA": '/opt/certs_ovpn_flask/easyrsa.zip',
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
    
    logger.info("##############################################################")
    logger.info("Check database test data.")
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
        for i in range(1, 3):
            service = "test{}".format(str(i))
            result = dbsession.scalar(select(OvpnServers).where(OvpnServers.server_name == service))
            if not result:
                logger.debug("Add test ovpn service: {} to db".format(service))
                dbsession.add(OvpnServers(
                    server_name=service, 
                    configuration_dir='/etc/openvpn/test{}'.format(str(i)), 
                    configuration_file='test{}.conf'.format(str(i)), 
                    status_file='test{}-status.log'.format(str(i)),
                    log_file_dir='/var/log/',
                    log_file='test{}.log'.format(str(i)),
                    startup_service='test{}-ovpn.service'.format(str(i)),
                    certs_dir='certs-test{}'.format(str(i)),
                    management_port=33000+i,
                    management_password='123456789'
                    ))
                dbsession.commit()
                    
        # table: ovpn_clients 
        logger.debug("- Check the ovpn_clients table, ovpn clients: test1-1000")
        for i in range(1, 3):
            service = "test{}".format(str(i))
            result = dbsession.scalar(select(OvpnServers).where(OvpnServers.server_name == service))
            if not result:
                logger.debug("Add test ovpn service: {} to db".format(service))
                dbsession.add(OvpnServers(
                    server_name=service, 
                    configuration_dir='/etc/openvpn/test{}'.format(str(i)), 
                    configuration_file='test{}.conf'.format(str(i)), 
                    status_file='test{}-status.log'.format(str(i)),
                    log_file_dir='/var/log/',
                    log_file='test{}.log'.format(str(i)),
                    startup_service='test{}-ovpn.service'.format(str(i)),
                    certs_dir='certs-test{}'.format(str(i)),
                    management_port=33000+i,
                    management_password='123456789'
                    ))
                dbsession.commit()
            else:
                logger.debug(f"- ovpn_servers table: ovpn servcie test{i} has been added")        
            
        logger.debug("- Check the ovpn_clients table now")
        logger.info("- Check the fake test clients: test1-1000 ")
        start_ip = ipaddress.ip_address('10.168.0.0')
        for s in range(1, 3):
            for i in range(1, Stress_Num+1):
                start_ip = start_ip + 1
                site_name = "test{}".format(str(i))
                cn = "test-{}".format(str(uuid.uuid4()))
                ts_id = dbsession.scalar(select(OvpnServers).where(OvpnServers.server_name == f"test{s}")).id
                result = dbsession.scalar(select(OvpnClients).where(OvpnClients.site_name == site_name, OvpnClients.server_id == ts_id))
                if not result:
                    logger.debug("Add test client site_name: {} to db".format(site_name))
                    dbsession.add(OvpnClients(
                        server_id=dbsession.scalar(select(OvpnServers).where(OvpnServers.server_name == f'test{s}'.format())).id, 
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
        for i in range(1, Stress_Num*2+1):
            site_name = 'test{}'.format(str(i))
            results = dbsession.scalars(select(OvpnClients).where(OvpnClients.site_name == site_name))
            if results:
                for result in results:
                    logger.debug("Delete test client site_name: {}".format(site_name))
                    dbsession.delete(result)
                    dbsession.commit()

        # table: ovpn_servers
        logger.debug("- Check the ovpn_servers table, ovpn service: test1-2 ")
        logger.info("- Check the ovpn_servers table now")
        for i in range(1, 3):
            service = "test{}".format(str(i))
            results = dbsession.scalars(select(OvpnServers).where(OvpnServers.server_name == service))
            if results:
                for result in results:
                    logger.debug("Delete test ovpn service: {}".format(service))
                    dbsession.delete(result)
                    dbsession.commit()
                                        
        logger.info("Test data deleted done!")

    
    logger.info("##############################################################")
    logger.info("Check ovpn certs test files.")
    cert_root = dbsession.scalar(select(OfSystemConfig).where(OfSystemConfig.item == "DIR_CERT_ROOT")).ivalue.strip()
    logger.debug(f"Certs root: {cert_root}")
    system_type = platform.system()
    logger.debug(f"System: {system_type}")
    if system_type.startswith("Window"):
        cert_root = "D:/tmp/ovpn_flask"
        logger.debug(f"Set certs root DIR: {cert_root}")

    if action == "add":
        """Add cert test files."""    
  
    logger.info("##############################################################")
    if action == "add":
        """Add cert test files."""    
        logger.info("Check ovpn certs test files.")
        cert_root = dbsession.scalar(select(OfSystemConfig).where(OfSystemConfig.item == "DIR_CERT_ROOT")).ivalue.strip()
        logger.debug(f"Certs root: {cert_root}")
        system_type = platform.system()
        logger.debug(f"System: {system_type}")
        if system_type.startswith("Window"):
            cert_root = "D:/tmp/ovpn_flask"
            logger.debug(f"Set certs root DIR: {cert_root}")
            
        for i in range(1, 3):
            logger.debug(f"OpenVPN Service test{i}...")
            server_name = f'test{i}'
            ovpn_service = dbsession.scalar(select(OvpnServers).where(OvpnServers.server_name == server_name))
            certs_dir = ovpn_service.certs_dir
            server_id = ovpn_service.id
            dir_reqs = dbsession.scalar(select(OfSystemConfig).where(OfSystemConfig.item == "DIR_REQS")).ivalue.strip()
            dir_plain_certs = dbsession.scalar(select(OfSystemConfig).where(OfSystemConfig.item == "DIR_PLAIN_CERTS")).ivalue.strip()
            dir_encrypts_certs = dbsession.scalar(select(OfSystemConfig).where(OfSystemConfig.item == "DIR_ENCRYPT_CERTS")).ivalue.strip()
            dir_zip_certs = dbsession.scalar(select(OfSystemConfig).where(OfSystemConfig.item == "DIR_ZIP_CERTS")).ivalue.strip()
            
            clients_us = dbsession.scalars(select(OvpnClients).where(OvpnClients.server_id == server_id))    
                         
            for client_us in clients_us:
                # create .req .conf .p7mb64 files
                for sub_dir in (dir_reqs, dir_plain_certs, dir_encrypts_certs):
                    if sub_dir.find('req') != -1:
                        suffix = '.req'
                    elif sub_dir.find("plain") != -1:
                        suffix = '.conf'
                    else:
                        suffix = ".p7mb64"
                    t_path = pathlib.Path(cert_root, certs_dir, sub_dir)
                    if not t_path.exists():
                        logger.debug("Create DIR: " + t_path.absolute().as_posix())
                        t_path.mkdir(parents=True)                   
                    t_file =  pathlib.Path(cert_root, certs_dir, sub_dir, client_us.cn + suffix)
                    if not t_file.exists():
                        logger.debug("Create file: " + t_file.absolute().as_posix())
                        with t_file.open("w", encoding ="utf-8") as f:
                            f.write("For test purpose: " +client_us.cn + suffix + "\n")

                # create zip files
                suffix = ".zip"
                t_path = pathlib.Path(cert_root, certs_dir, dir_zip_certs)
                if not t_path.exists():
                    logger.debug("Create DIR: " + t_path.absolute().as_posix())
                    t_path.mkdir(parents=True) 
                    
                t_file =  pathlib.Path(cert_root, certs_dir, dir_zip_certs, f"{client_us.cn}{suffix}")
                if not t_file.exists():
                    logger.debug("Create ZIP file: " + t_file.absolute().as_posix())
                with zipfile.ZipFile(t_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(pathlib.Path(cert_root, certs_dir, dir_reqs, f"{client_us.cn}.req").expanduser().resolve(strict=True), f"{client_us.cn}.req")                 
                    zf.write(pathlib.Path(cert_root, certs_dir, dir_plain_certs, f"{client_us.cn}.conf").expanduser().resolve(strict=True), f"{client_us.cn}.conf")                 
                    zf.write(pathlib.Path(cert_root, certs_dir, dir_encrypts_certs, f"{client_us.cn}.p7mb64").expanduser().resolve(strict=True), f"{client_us.cn}.p7mb64")                 
            
    if action == "delete":
        """Delete test cert files."""
        logger.info("Check ovpn certs test dirs to delete them.")
        t_path=pathlib.Path(cert_root)
        if t_path.exists():
            rm_tree(t_path)
        
def rm_tree(pth):
    for child in pth.iterdir():
        if child.is_file():
            logger.debug("Delete file: " + child.absolute().as_posix())
            child.unlink()
        else:
            rm_tree(child)
    pth.rmdir()
