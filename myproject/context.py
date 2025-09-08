import os
import platform
from pathlib import Path
from config import ProductionConfig

"""
    LOGGING
"""

import common.logging.logutil as logutil
logutil.remove_log_handlers()

system_type = platform.system()
if system_type.startswith("Window"):
    log_path = str(Path(os.path.realpath(__file__)).parents[1]) + "\\logs"
else:
    log_path = ProductionConfig.LOG_DIR
logger = logutil.get_logger(log_name=ProductionConfig.LOG_FILE or 'ovpn_flask_mgmt', log_path=log_path, loglevel=ProductionConfig.LOG_LEVEL)


"""
    DATABASE
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config import ProductionConfig
engine = create_engine(ProductionConfig.SQLALCHEMY_DATABASE_URI, pool_size=20, pool_recycle=600, pool_pre_ping=True, pool_reset_on_return='rollback', pool_timeout=15)
DBSession = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False))


"""
    SINGLETONS
"""
# from carelds.temb.app.common.auth import Auth, Tableau
# auth_ = Auth(config_object.SECRET_KEY, DBSession, 'auth.login_get')
# tableau_ = Tableau(tableauAuth, assert_authed=assert_tableau_authed)