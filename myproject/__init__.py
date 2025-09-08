'''
Flask 的工厂模式
Created on 2023年8月10日
'''
import os
import socket
import re
import sys
import traceback

from flask import Flask
import datetime, time
from flask import session
from flask import g, request, send_from_directory
import config
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response
import flask
from flask import redirect, url_for
from werkzeug.exceptions import InternalServerError


from flask_babel import Babel
from .context import logger
from .context import DBSession as dbsession
from .context import engine

from orm.ovpn import OfSystemConfig
from sqlalchemy import select
from myproject.context import DBSession as dbs


class ReverseProxied(object):
    def __init__(self, app, script_name):
        self.app = app
        self.script_name = script_name

    def __call__(self, environ, start_response):
        environ['SCRIPT_NAME'] = self.script_name
        return self.app(environ, start_response)


def create_app(test_config=None):
    """ create Flask APP
    Args:
        test_config (class, optional): test config object. Defaults to None.

    Returns:
        flask.app.Flask: app
    """

    # Build paths inside the project like this: os.path.join(BASE_DIR, ...)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # TEMPLATES DIR
    TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
    
    # STATIC_DIR
    STATIC_DIR = os.path.join(BASE_DIR, 'static')
    
    app = Flask(__name__, instance_relative_config=True, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
    app.config['JSON_AS_ASCII'] = False 
    app.config.from_object(config.ProductionConfig)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)
        
    # i18n config   
    def get_locale():
        # if a user is logged in, use the locale from the user settings
        user = getattr(g, 'user', None)
        print (user)
        if user is not None:
            if getattr(user, 'locale', None):
                return user.locale
        # get language from session
        # if the user has set up the language manually it will be stored in the session,
        # so we use the locale from the user settings
        try:
            language = session['language']
        except KeyError:
            language = None
        if language is not None:
            return language
        
        # otherwise try to guess the language from the user accept
        # header the browser transmits.  We support de/fr/en in this
        # example.  The best match wins.
        # print("---------------------: " + request.accept_languages.best_match(['zh', 'en']))
        return request.accept_languages.best_match(['zh', 'en'])

    def get_timezone():
        user = getattr(g, 'user', None)
        if user is not None:
            return user.timezone

    # babel = Babel(app, locale_selector=get_locale, timezone_selector=get_timezone)
    babel = Babel(app, locale_selector=get_locale)

    # ensure the instance folder exists or create it
    # try:
    #     os.makedirs(app.instance_path)
    # except OSError:
    #     pass

    # https://dlukes.github.io/flask-wsgi-url-prefix.html
    # for reverse proxy, prefix every url with /ovpn include /static/*
    # app.wsgi_app = DispatcherMiddleware(
    #     Response('Not Found', status=404),
    #     {'/ovpn': app.wsgi_app}
    # )

    # Flask application behind a reverse proxy
    # app.wsgi_app = ReverseProxied(app.wsgi_app, script_name='/ovpn')

    """
    # logging settings to file
    log_level = logging.INFO
    for handler in app.logger.handlers:
        app.logger.removeHandler(handler)

    logdir = os.path.join(BASE_DIR, 'logs')
    if not os.path.exists(logdir):
        os.mkdir(logdir)
    # log_file = os.path.join(logdir, 'app.log')
    log_file = app.config['LOGFILE']
    handler = logging.FileHandler(log_file)
    handler.setLevel(log_level)
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # logging.Formatter(
    #     fmt='%(asctime)s.%(msecs)03d',
    #     datefmt='%Y-%m-%d,%H:%M:%S'
    # )
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)
    """  

    # session expiration time
    @app.before_request
    def make_session_permanent():
        session.permanent = True
        s_age = int(app.config['SESSION_COOKIE_AGE'])
        app.permanent_session_lifetime = datetime.timedelta(minutes=s_age)
    
    # server starttime
    start_datetime = datetime.datetime.now()
    
    """    
    # update config for PLATFORM_NAME
    CURRENT_SERVSER = os.environ.get("CURRENT_SERVSER")
    PLATFORM_NAME = None
    CURRENT_OVPN_SETTING = None
    if CURRENT_SERVSER:
        if re.match('(?i)CAREL', CURRENT_SERVSER):
            PLATFORM_NAME = "Carel OVPN"            
        if re.match('(?i)SG', CURRENT_SERVSER):
            PLATFORM_NAME = "SG OVPN"
        if re.match('(?i)SHIELD', CURRENT_SERVSER):
            PLATFORM_NAME = "Shield OVPN"
    else:
        PLATFORM_NAME = getPlatformName()  
    if PLATFORM_NAME:
        if re.match('(?i)CAREL', PLATFORM_NAME):
            CURRENT_OVPN_SETTING = app.config['OVPN']['CAREL_OVPN']
        if re.match('(?i)SG', PLATFORM_NAME):
            CURRENT_OVPN_SETTING = app.config['OVPN']['SG_OVPN']
        if re.match('(?i)SHIELD', PLATFORM_NAME):
            CURRENT_OVPN_SETTING = app.config['OVPN']['SHIELD_OVPN']
    else:
        PLATFORM_NAME = "DEV OVPN"
        CURRENT_OVPN_SETTING = app.config['OVPN']['DEV_OVPN']
    
    SITE_NAME = ''
    if re.match('(?i)CAREL', PLATFORM_NAME):
        SITE_NAME = "carel"
    if re.match('(?i)SG', PLATFORM_NAME):
        SITE_NAME = "sgovpn"
    if re.match('(?i)SHIELD', PLATFORM_NAME):
        SITE_NAME = "shield" 
    if re.match('(?i)DEV', PLATFORM_NAME):
        SITE_NAME = "dev" 
            
    app.config.update(
        PLATFORM_NAME = PLATFORM_NAME,
        CURRENT_OVPN_SETTING = CURRENT_OVPN_SETTING,
        SITE_NAME = SITE_NAME
    )
    """
    # update config for tun/tap files dir
    PARENT_DIR = os.path.dirname(BASE_DIR)
    TUN_FILES_DIR = os.path.join(PARENT_DIR, 'tun-ovpn-files')
    TAP_FILES_DIR = os.path.join(PARENT_DIR, 'tap-ovpn-files')
    app.config.update(
        TUN_FILES_DIR = TUN_FILES_DIR,
        TAP_FILES_DIR = TAP_FILES_DIR,
        BASE_DIR = BASE_DIR
    )
    logger.debug("*********************************************************************")
    logger.debug("*********************************************************************")
    logger.debug("*********        APP STARTED     *********")
    logger.debug("*********************************************************************")
    logger.debug("*********************************************************************")
    
    # check database integrity
    # if engine.dialect.has_table(engine.connect(), OfSystemConfig.__tablename__):
    #     logger.debug("Looks likes database has been initialized before...")
    #     cs = dbs.scalar(select(OfSystemConfig).where(OfSystemConfig.item == 'CUSTOMER_SITE'))
    #     app.config.update(CUSTOMER_SITE = cs.ivalue.strip(),)
    # else:
    #     logger.info("Database has not been initialized, initial database now...")
    #     from .flask_command import check_db_integrity
    #     check_db_integrity()
    #     logger.info("Database init done.")
    from .flask_command import check_db_integrity
    check_db_integrity()   
    
    # update config CUSTOMER_SITE from db
    cs = dbs.scalar(select(OfSystemConfig).where(OfSystemConfig.item == 'CUSTOMER_SITE'))
    app.config.update(CUSTOMER_SITE = cs.ivalue.strip(),)
    
    # context processors
    @app.context_processor
    def context_processor_func():
        end_datetime = datetime.datetime.now()
        delta = end_datetime - start_datetime
        days = delta.days
        if days < 1:
            days = "<1"
        return dict(
            runningDays=days,
            now=datetime.datetime.now()
            )

    # onlineUsers, not in prod now
    app.onlineUsers = 0
    
    # # register the database command: init-db
    # from myproject import db
    # db.init_app(app)

    # register the flask command: initialize-db
    from myproject import flask_command
    flask_command.init_app(app)

    """
    # test db connect and wait for successful connection
    with app.app_context():
        while True:
            try:
                conn = db.get_db()
                cur = db.get_cur()
                logger.debug("------DEBUG: DB conn ----------------------------")
                logger.debug(conn)
                logger.debug("-------------------------------------------------")
                if conn:
                    break
            except Exception as error:    
                logger.debug("Error: Please check the database connections!!")
                logger.debug("\t", error)
                logger.debug("\tSleep 20s\n")
                time.sleep(20)
            finally:
                logger.debug("------DEBUG: read config from db -----------------")
                cur.execute("select item, ivalue from sysconfig")
                items = {}
                for item in cur.fetchall():
                    logger.debug(item)
                    items[item['item']] = item['ivalue']
                app.config.update(items)

                items = {}
                for k, v in app.config['OVPN'].items():
                    if k == app.config['CUSTOMER_SITE']:
                        items['TUN_MODE'] = v['TUN']
                        items['TAP_MODE'] = v['TAP']
                        app.config.update(items)
                logger.debug("-------------------------------------------------")
    """

    # print the config
    # print("------DEBUG: APP config---------------------------------")
    # for key in app.config.keys():
    #     print("{key: <35}{val: <}".format(key=key + ":", val = str(app.config.get(key))))
    # # print(app.config.keys())
    # print("------APP config---------------------------------")

    """
        VIEW BLUEPRINTS
    """
    from myproject.bp_auth.auth import auth_bp
    from myproject.bp_ovpn.ovpn import ovpn_bp
    from myproject.bp_test.test import test_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(ovpn_bp, url_prefix='/ovpn')
    app.register_blueprint(test_bp, url_prefix='/test')

    # make url_for('index') == url_for('ovpn.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the ovpn blueprint a url_prefix, but for
    # the app the ovpn will be the main index
    # app.add_url_rule("/", endpoint="index")

    """
        GENERAL ENDPOINTS AND REQUEST/RESPONSE HANDLING
    """
    @app.route('/')
    def redict_root():
        """
        Redict "/" to "/ovpn"
        """
        return redirect(url_for("ovpn.index"))

    @app.errorhandler(InternalServerError)
    def error_handler(error: InternalServerError) -> None:
        """
        Handle the error: log the exception and return a 500 response
        Args:
            error: the error object

        """
        if hasattr(sys, 'exception'):
            exc = sys.exception()  # Python >= 3.11
        else:
            exc = sys.exc_info()[1]
            
        exc_summary = traceback.extract_tb(exc.__traceback__)
        logger.error(exc)
        for line in traceback.format_list(exc_summary[-1:-6:-1]):
            logger.error(line)
        return Response('Internal Server Error', 500)

    @app.route('/static/<path:path>')
    def send_static(path: str) -> flask.Response:
        """
        Send static file to web client
        Args:
            path: path to static file

        Returns: Response

        """
        return send_from_directory('static', path)

    @app.teardown_appcontext
    def shutdown_session(exception = None) -> None:
        """
        Rollback and remove database session to avoid pending sessions
        Args:
            exception:
            
        """
        dbsession.rollback() #Rollback any uncommitted database transations
        dbsession.remove() #Remove the current session

    @app.after_request
    def add_header(response: flask.Response) -> flask.Response:
        """
        Perform operations on response headers
        Args:
            response: the original response from endpoint

        Returns: the updated response

        """
        response.cache_control.max_age = 30
        response.cache_control.no_cache = True
        
        return response

    @app.after_request
    def response_details(response: flask.Response) -> flask.Response:
        """
        Log (debug) response status
        Args:
            response: the response object

        Returns: the response (unchanged)

        """
        if 'static/' not in request.url and 'favicon' not in request.url:
            logger.debug(f'{request.method} {response.status} {request.url}')
        return response

    return app


def getPlatformName() -> str:
    """
    @summary: Return which platform this system is running on
    @param: None
    @return: str
    @throws Exception
    """
    fqdn = socket.getfqdn()
    platformName = ''
    if re.match('(?i)CAREL', fqdn):
        platformName = "Carel OVPN"
    if re.match('(?i)SG', fqdn):
        platformName = "SG OVPN"
    if re.match('(?i)SHIELD', fqdn):
        platformName = "Shield OVPN"          
    return platformName
