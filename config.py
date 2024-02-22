class Config(object):
    pass
    # DEBUG = True
    # DEVELOPMENT = True
    # SECRET_KEY = 'do-i-really-need-this'
    # FLASK_HTPASSWD_PATH = '/secret/.htpasswd'
    # FLASK_SECRET = SECRET_KEY
    # DB_HOST = 'database' # a docker link


class ProductionConfig(Config):
    DEVELOPMENT = False
    DEBUG = False
    SECRET_KEY = "96f8bcfb789054901969a5f406ea6a97"
    
    # session age
    SESSION_COOKIE_AGE = 120
    
    # postgres configurations 
    PG_DATABASE_USER="mgmt"
    PG_DATABASE_PASSWORD = 'rootroot'
    PG_DATABASE_DB = 'mgmtdb'
    PG_DATABASE_HOST = '127.0.0.1'
    PG_DATABASE_PORT = 5432
    
    # data
    SQL_FILE = 'schema.sql'
    
    # version
    VERSION = 'v1.1.0'

    # Log file locations
    # LOGFILE = 'D:\stmt_flask.log'
    LOGFILE = 'stmt_flask.log'
    
    # ---------------------------------------------------------------------------------------------------------------------------
    # All the followings, use DB sysconfig instead
    
    """
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
    """
    
    # sub_dirs
    # TUN_DIR = 'tun-ovpn-files'
    # TAP_DIR = 'tap-ovpn-files'
    # EASYRSA = 'easyrsa'
    # GENERIC_CLIENT = 'generic-ovpn'
    # REQ = "reqs"
    # REQ_DONE = "reqs-done"
    # VALIDATED = "validated"
    
    # VPN_SCRIPT_DIR, in the same dir with this project, usually in /opt.
    # VPN_SCRIPT_DIR = 'vpntool'
    
    # servers dirs
    # APACHE_ROOT = "C:\\Users\\nick_\\Downloads\\Apache-RemotePRO\\Apache-RemotePRO" # DB
    # IP_REMOTE = 'service.carel-remote.com' # DB
    # IP_PORT = '443' # DB
    # PROXY_PREFIX = 'PVP' # DB
