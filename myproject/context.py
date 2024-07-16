import os

"""
    LOGGING
"""

import common.logging.logutil as logutil
logutil.remove_log_handlers()
logger = logutil.get_logger(log_name='tableau_embedding_server', log_path='/var/log/temb', loglevel=logutil.DEBUG,
                            options={'dd_enabled': os.environ.get('DATADOG_TRACE_ENABLED', '').lower() == 'true',
                                     'dd_clean': True})


"""
    DATABASE
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from carelds.temb.app.config import config_object, tableauAuth, assert_tableau_authed
engine = create_engine(config_object.SQLALCHEMY_DATABASE_URI, pool_size=20, pool_recycle=600, pool_pre_ping=True, pool_reset_on_return='rollback', pool_timeout=15)
DBSession = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False))


"""
    SINGLETONS
"""
from carelds.temb.app.common.auth import Auth, Tableau
auth_ = Auth(config_object.SECRET_KEY, DBSession, 'auth.login_get')
tableau_ = Tableau(tableauAuth, assert_authed=assert_tableau_authed)