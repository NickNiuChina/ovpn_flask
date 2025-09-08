import logging


class Config(object):
    pass
    # DEBUG = True
    # DEVELOPMENT = True
    # SECRET_KEY = 'do-i-really-need-this'
    # FLASK_HTPASSWD_PATH = '/secret/.htpasswd'
    # FLASK_SECRET = SECRET_KEY
    # DB_HOST = 'database' # a docker link


class TestConfig(Config):
    pass


class ProductionConfig(Config):
    
    HOST = '0.0.0.0'
    PORT = 5000
    
    DEVELOPMENT = False
    DEBUG = False
    SECRET_KEY = "96f8bcfb789054901969a5f406ea6a97"
    
    # session age
    SESSION_COOKIE_AGE = 120
    
    # postgres configurations 
    # PG_DATABASE_USER="mgmt"
    # PG_DATABASE_PASSWORD = 'rootroot'
    # PG_DATABASE_DB = 'mgmtdb'
    # PG_DATABASE_HOST = '127.0.0.1'
    # PG_DATABASE_PORT = 5432
    # sqlalchemy URI
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://postgres:postgres@localhost:5432/ovpn_flask'
    
    # data
    SQL_FILE = 'schema.sql'
    
    # version
    VERSION = 'v0.00.001'

    # Log file locations
    # LOGFILE = 'D:\stmt_flask.log'
    LOG_LEVEL = logging.DEBUG
    LOGFILE = 'stmt_flask.log'
    LOG_FILE = 'ovpn_flask_mgmt.log'
    LOG_DIR = '/var/log'
    
    # ---------------------------------------------------------------------------------------------------------------------------
    # All the followings, use DB sysconfig instead

    OVPN = {
        'CAREL_OVPN':
            {
                'TUN': 'enabled', 
                'TAP': 'enabled', 
            },
        'SHIELD_OVPN':
            {
                'TUN': 'enabled', 
                'TAP': 'disabled', 
            },       
        'SG_OVPN':
            {
                'TUN': 'disabled', 
                'TAP': 'enabled', 
            },
        'DEV_OVPN':
            {
                'TUN': 'enabled', 
                'TAP': 'enabled', 
            }
    }
    
    # sub_dirs
    # DIR_TUN = 'tun-ovpn-files'
    # DIR_TAP = 'tap-ovpn-files'
    # DIR_EASYRSA = 'easyrsa'
    # DIR_GENERIC_CLIENT = 'generic-ovpn'
    # DIR_REQ = "reqs"
    # DIR_REQ_DONE = "reqs-done"
    # DIR_VALIDATED = "validated"
    
    # VPN_SCRIPT_DIR, in the same dir with this project, usually in /opt.
    # VPN_SCRIPT_DIR = 'vpntool' #
    
    # servers dirs
    # APACHE_ROOT = "C:\\Users\\nick_\\Downloads\\Apache-RemotePRO\\Apache-RemotePRO" # DB
    # IP_REMOTE = 'service.carel-remote.com' # DB
    # IP_PORT = '443' # DB
    # PROXY_PREFIX = 'PVP' # DB
