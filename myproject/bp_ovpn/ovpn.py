"""
    Main views to response to request and Blueprint implemented.
"""
from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort
from flask import session
from flask import current_app as app
from flask import jsonify
from flask import send_file
from flask import jsonify

import datetime
import re
import os
import subprocess
import platform
import pathlib
import psycopg2
from random import randint

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import ImmutableMultiDict

from myproject.bp_auth.auth import login_required
from myproject.db import get_cur, get_db

from myproject.context import logger
from common.utils.bp_ovpn import OvpnUtils
from myproject.context import DBSession as dbs
from sqlalchemy import select
from sqlalchemy import update
from orm.ovpn import OfSystemConfig

from flask_paginate import Pagination, get_page_args, get_page_parameter

ovpn_bp = Blueprint("ovpn", __name__)

####################################################################################
# Blueprint context processor
####################################################################################
@ovpn_bp.context_processor
def cp_ovpn_services():
    """ context processor of ovpn services list

    Returns:
        dict: k, v for variable and value
    """
    servers = OvpnUtils.get_all_openvpn_services(managed=1)
    openvpn_server_list = {}
    if servers:
        for server in servers:
            openvpn_server_list.update({server.server_name: str(server.id)})
    print(servers)
    return dict(OPENVPN_SERVER_LIST=openvpn_server_list)

####################################################################################
# Main dashboard
####################################################################################
@ovpn_bp.route("/", methods=("POST", "GET"))
@login_required
def index():
    
    """ 
    @summary: Main dashboard page
    @return: Main page templates
    """
    sys_info = OvpnUtils.get_system_info()
    context = {'system_info': sys_info}
    if request.method == "POST":
        if request.form.get('action', '') == "db_refresh":
            return jsonify(context)
    else:
        return render_template("ovpn/dashboard.html", system_info=sys_info)

@ovpn_bp.route("/XXXXXXXXXXXXX")
@login_required
def index1():
    """ 
    @summary: Main dashboard page
    @return: Main page templates
    """
    cur = get_cur()
    
    # online clients
    cur.execute(" select count(*) from tunovpnclients where status=1")
    online_num = cur.fetchone()
    print(online_num)
    
    session["online_num"] = online_num['count']
    
    # total clients
    cur.execute(" select count(*) from tunovpnclients")
    clients_num = cur.fetchone()
    session["clients_num"] = clients_num['count']

    # boss clients
    cur.execute("select count(*) from tunovpnclients where cn like 'boss-%'")
    boss_num = cur.fetchone()
    session["boss_num"] = boss_num['count']
    
    # legacy clients
    cur.execute("select count(*) from tunovpnclients where cn not like 'boss-%'")
    legacy_num = cur.fetchone()
    session["legacy_num"] = legacy_num['count']
    
    # user priviledge
    user_id = session["user_id"]
    cur.execute("select user_type from tb_user where user_id = %s", (user_id,))
    user_type = cur.fetchone()
    session["user_type"] = user_type["user_type"]

    # top 5 scores
    # cur.execute( "select sc.id as id, sc.score as score, st.student_no as student_no,"
    #             " st.student_name as student_name, co.course_no as course_no, co.course_name as course_name"
    #             " from tb_score sc, tb_student st, tb_course co where sc.course_no = co.course_no and sc.student_no = st.student_no"
    #             " order by sc.score desc limit 10" )
    cur.execute('select * from tunovpnclients where status = 1 order by changedate desc limit 5')
    topOnline = cur.fetchall()
    
    return render_template("ovpn/dashboard.html", topOnline=topOnline)

####################################################################################
# introduction view
####################################################################################


@ovpn_bp.route("/introduction")
@login_required
def introduction():
    """
    @summary: introduction page
    @return: template: introduction template
    """
    return render_template("ovpn/introduction.html")

####################################################################################
# ovpn services overview views
####################################################################################
@ovpn_bp.route("/servers/", methods=("POST", "GET"), defaults={'page': 1})
@ovpn_bp.route("/servers/<int:page>/", methods=("POST", "GET"))
@login_required
def servers(page):
    """
    @summary: ovpn service page, get -> list ovpn service, post -> add or delete ovpn service
    @return: template: template ovpn/servers.html
    """
    if request.method == "POST":
        
        form_args = request.form.to_dict()
        
        if request.form.get('action', None) == 'action_add_ovpn_server':
            logger.info("Get the new openvpn server from POST, call to add new service.")
            result = OvpnUtils.add_openvpn_service(form_args)
            flash(result[0], result[1])
            return redirect(url_for("ovpn.servers"))
        
        if request.form.get('action', None) == 'action_delete_ovpn_server':
            result = OvpnUtils.delete_openvpn_service(form_args)
            flash(result[0], result[1])
            return redirect(url_for("ovpn.servers"))
        
        if request.form.get('action', None) in ('stop_ovpn_service', "start_ovpn_service"):
            logger.debug("Post request to start/stop ovpnvpn service.")
            server_id = request.form.get('s_uuid', None)
            op = request.form.get("action", None)
            if server_id:
                server = OvpnUtils.get_openvpn_service_by_id(server_id)
                if not server:
                    message = "UUID has not been found in record!"
                    return {"result": "danger", 'message': message}
                
                if op.startswith("start"):
                    action = 'start'
                elif op.startswith("stop"):
                    action = 'stop'
                
                if action in ["start", "stop", "restart"]:
                    res = OvpnUtils.change_openvpn_running_status(server=server, op=action)
                    if res:
                        message = 'OpenVPN service {} successfully.'.format(action)
                        result = "success"
                    else:
                        message = 'OpenVPN service failed to {}!'.format(action)
                        result = "danger"
                else:
                    message = "Operation not allowed."
                    result = "danger"
                return {"result": result, 'message': message}
            else:
                message = "Please provide a valid uuid!"
                return {"result": "danger", 'message': message}
        
        return "BAD request!", 400
    else:
        # GET request
        page_size = int(session.get("page_size", 50))
        page = int(page)
        
        # if q and q.strip():
        #     ss = OvpnUtils.search_openvpn_services(q.strip())
        # else:
        #     ss = OvpnUtils.get_all_openvpn_services()
        ss = OvpnUtils.get_all_openvpn_services()
        total = len(ss.all())
        print(total)
        servers = ss.limit(page_size).offset((page-1)*page_size)
        return_servers = []
        
        
        return_servers = []
        if not platform.system().startswith("Linux"):
            for server in servers:
                server.running_status = 0
                return_servers.append(server)
        else:
            for server in servers:            
                status = OvpnUtils.get_openvpn_running_status(server)
                if status:
                    server.running_status = status["status"]
                else:
                    server.running_status = 0
                return_servers.append(server)
        pagination = Pagination(page=page, total=total, per_page=page_size)
        return render_template("ovpn/servers.html", servers=return_servers, pagination=pagination)

@ovpn_bp.route("/server/<server_id>/update", methods=("POST", "GET"))
@login_required
def server_update(server_id):
    """
    @summary: ovpn service update page
    @return: template: template ovpn/servers.html
    """
    ovpn_service = OvpnUtils.get_openvpn_service_by_id(server_id)
    if not ovpn_service:
        return render_template('404.html'), 404
    
    if request.method == "POST":        
        form_args = request.form.to_dict()
        form_args.update({"uuid": server_id})
        logger.info("Update the ovpn service by the post args: " + str(form_args))
        result = OvpnUtils.update_openvpn_service(form_args)
        flash(result[0], result[1])
        # return redirect(url_for("ovpn.servers"))
        return redirect(request.referrer)
    else:
        servers = OvpnUtils.get_all_openvpn_services()
        return render_template("ovpn/server_update.html", server=ovpn_service)


@ovpn_bp.route("/server/<server_id>/config", methods=("POST", "GET"))
@login_required
def server_config(server_id):
    """
    @summary: ovpn service config page
    @return: template: template ovpn/server_config.html
    """
    ovpn_service = OvpnUtils.get_openvpn_service_by_id(server_id)
    if not ovpn_service:
        return render_template('404.html'), 404
    
    if request.method == "POST" and request.form.get('action', None) == 'action_add_ovpn_server':        
        form_args = request.form.to_dict()
        logger.info("Get the add new openvpn server from POST, call to add new service.")
        result = OvpnUtils.add_openvpn_service(form_args)
        flash(result[0], result[1])
        return redirect(url_for("ovpn.servers"))
    else:
        servers = OvpnUtils.get_all_openvpn_services()
        user_id = session.get("user_id", None)
        user = OvpnUtils.get_user_by_id(user_id)
        return render_template("ovpn/server_config.html", servers=servers, log_size=user.page_size)

####################################################################################
# ovpn service detail views
####################################################################################
@ovpn_bp.route("/<server_id>/clients", methods=("POST", "GET"))
@login_required
def clients(server_id):
    """
    @summary: ovpn clients page, get -> list ovpn service, post -> add or delete ovpn service
    @return: template: template ovpn/clients.html
    """
    ovpn_service = OvpnUtils.get_openvpn_service_by_id(server_id)
    if not ovpn_service:
        return render_template('404.html'), 404
    
    if request.method == "POST":
        form_args = request.form.to_dict()
        logger.debug("route clients get POST data: {}".format(str(form_args)))
        
        if request.form.get('action', None) == 'action_list_ovpn_clients':
            form_args['ovpn_service'] = ovpn_service
            form_args['group'] = session['group']
            logger.debug("|route: clients, POST| get the clients list")            
            data = OvpnUtils.get_openvpn_clients_list(form_args)
                       
            return jsonify(data)
             
        return "BAD request!", 400
    
    if request.method == "GET":
        return render_template("ovpn/clients.html", ovpn_service=ovpn_service)
    else:
        return "Unsupported method", 400
    
    
@ovpn_bp.route("/<server_id>/generate_cert", methods=("POST", "GET"))
@login_required
def generate_cert(server_id):
    ovpn_service = OvpnUtils.get_openvpn_service_by_id(server_id)
    if not ovpn_service:
        return render_template('404.html'), 404
    
    if request.method == "POST":
        form_args = request.form.to_dict()
        # generate by cn name
        if request.form.get('action', None) == 'generate_cert_by_cn':
            form_args['ovpn_service'] = ovpn_service
            form_args['group'] = session['group']
            logger.debug("|route: generate_cert, POST| generate cert by cn")            
            data = OvpnUtils.get_plain_certs_list(form_args)
                       
            return jsonify(data)
    
    elif request.method == "GET":
        return render_template("ovpn/generate_cert.html", ovpn_service=ovpn_service)

@ovpn_bp.route("/<server_id>/plain_certs", methods=("POST", "GET"))
@login_required
def plain_certs(server_id):
    ovpn_service = OvpnUtils.get_openvpn_service_by_id(server_id)
    if not ovpn_service:
        return render_template('404.html'), 404
    
    if request.method == "POST":
        form_args = request.form.to_dict()
        logger.debug("route plain_certs get POST data: {}".format(str(form_args)))
        
        if request.form.get('action', None) == 'action_list_ovpn_plain_certs':
            form_args['ovpn_service'] = ovpn_service
            form_args['group'] = session['group']
            logger.debug("|route: plain_certs, POST| get the clients list")            
            data = OvpnUtils.get_plain_certs_list(form_args)
                       
            return jsonify(data)
             
        return "BAD request!", 400
    elif request.method == "GET":
        return render_template("ovpn/plain_certs.html", ovpn_service=ovpn_service)
    else:
        return "Unsupported method", 400
    
@ovpn_bp.route("/<server_id>/encrypt_certs", methods=("POST", "GET"))
@login_required
def encrypt_certs(server_id):
    ovpn_service = OvpnUtils.get_openvpn_service_by_id(server_id)
    if not ovpn_service:
        return render_template('404.html'), 404
    
    if request.method == "POST":
        form_args = request.form.to_dict()
        logger.debug("route encrypt_certs get POST data: {}".format(str(form_args)))
        
        if request.form.get('action', None) == 'action_list_ovpn_encrypt_certs':
            form_args['ovpn_service'] = ovpn_service
            form_args['group'] = session['group']
            logger.debug("|route: plain_certs, POST| get the clients list")            
            data = OvpnUtils.get_encrypt_certs_list(form_args)
                       
            return jsonify(data)
             
        return "BAD request!", 400
    elif request.method == "GET":
        return render_template("ovpn/encrypt_certs.html", ovpn_service=ovpn_service)
    else:
        return "Unsupported method", 400
    
    
@ovpn_bp.route("/<server_id>/reqs", methods=("POST", "GET"))
@login_required
def reqs(server_id):
    ovpn_service = OvpnUtils.get_openvpn_service_by_id(server_id)
    if not ovpn_service:
        return render_template('404.html'), 404
    
    if request.method == "POST":
        form_args = request.form.to_dict()
        logger.debug("route reqs get POST data: {}".format(str(form_args)))
        
        if request.form.get('action', None) == 'action_list_ovpn_reqs':
            form_args['ovpn_service'] = ovpn_service
            form_args['group'] = session['group']
            logger.debug("|route: reqs, POST| get the req files list")            
            data = OvpnUtils.get_reqs_list(form_args)
                       
            return jsonify(data)
             
        return "BAD request!", 400
    elif request.method == "GET":
        return render_template("ovpn/reqs.html", ovpn_service=ovpn_service)
    else:
        return "Unsupported method", 400


@ovpn_bp.route("/<server_id>/zip_certs", methods=("POST", "GET"))
@login_required
def zip_certs(server_id):
    ovpn_service = OvpnUtils.get_openvpn_service_by_id(server_id)
    if not ovpn_service:
        return render_template('404.html'), 404
    
    if request.method == "POST":
        form_args = request.form.to_dict()
        logger.debug("route reqs get POST data: {}".format(str(form_args)))
        
        if request.form.get('action', None) == 'action_list_ovpn_zip_certs':
            form_args['ovpn_service'] = ovpn_service
            form_args['group'] = session['group']
            logger.debug("|route: zip_certs, POST| get the zip files list")            
            data = OvpnUtils.get_zip_certs_list(form_args)
                       
            return jsonify(data)
             
        return "BAD request!", 400
    elif request.method == "GET":
        return render_template("ovpn/zip_certs.html", ovpn_service=ovpn_service)
    else:
        return "Unsupported method", 400    
    
@ovpn_bp.route("/<server_id>/server_logs", methods=("POST", "GET"))
@login_required
def server_logs(server_id):
    ovpn_service = OvpnUtils.get_openvpn_service_by_id(server_id)
    if not ovpn_service:
        return render_template('404.html'), 404
    return render_template("ovpn/plain_certs.html", ovpn_service=ovpn_service)

####################################################################################
# refresh proxy config button view
####################################################################################
@ovpn_bp.route("/refresh/proxyConfig", methods=("POST", "GET"))
@login_required
def refreshProxyConfig():
    """
    @summary: refresh all proxy config and restart Apache
    @return: refreshed page
    """
    # db cursor
    conn = get_db()    
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

    previousUrl = request.referrer
    
    # system configs
    sql = "select * from sysconfig"
    
    try:
        cur.execute(sql)    
        # js console result
        result = "success"
        message = "All good"
    except Exception as e:
        result = "danger"
        message = "Error: " + str(e)
        flash(message, result)
        return redirect(previousUrl)          
    urls = []

    try:
        IP_REMOTE = app.config['IP_REMOTE']
        IP_PORT = app.config['IP_PORT']    
        PROXY_PREFIX = app.config['PROXY_PREFIX']
        APACHE_ROOT = app.config['DIR_APACHE_ROOT']
        APACHE_SUB = app.config['DIR_APACHE_SUB']
    except Exception as e:
        flash("Error: KeyError " + str(e), "danger")
        return redirect(previousUrl)
    
    # previous URL
    previousUrl = request.referrer
         
    # Apache config files
    proxyConfigFile = pathlib.Path(APACHE_ROOT, APACHE_SUB, 'reverse_proxy_local.conf')
    proxyConfigTemplate = pathlib.Path(APACHE_ROOT, APACHE_SUB, 'boss.template')
    
    if not proxyConfigFile.exists() or not proxyConfigTemplate.exists():
        flash("Error: Apache config directory does not exist!!", "danger")
        return redirect(previousUrl)

    # erease config file
    with open(proxyConfigFile, 'w') as fp:
        fp.truncate()
    # read the proxy config template 
       
    with open(proxyConfigTemplate, 'r') as fp:
        targetConfig = [p.strip() for p in fp.read().split('\n\n')][0]
           
    for table in ['tunovpnclients', 'ovpnclients']:
        sql = "select * from {table}".format(table=table)
        cur.execute(sql)
        count = cur.rowcount
    
        ovpnClients = cur.fetchall()
        
        for ovpnClient in ovpnClients:
            url = ''
            ip = ovpnClient['ip']
            # config proxy if not
            if len(ovpnClient['url']) < 10:
                # need to setup proxyConfig, set url to: len("RVRP@9801456451909-0xc0a8788a@") - 30 // len(9801456451909) - 13
                sql = "update {table} set url=%s where cn=%s".format(table=table)
                IP_CODED = generateUrl(PROXY_PREFIX, ip)
                url = PROXY_PREFIX + '@' + IP_CODED + '@'
                try:
                    cur.execute(sql, (IP_CODED, ovpnClient['cn']))
                    conn.commit()
                    result = 'success'
                    update = 'yes'
                except Exception as e:
                    message=str(e)
                    result = "danger"   
            else:
                IP_CODED = ovpnClient['url']
                update = 'no'
                url = PROXY_PREFIX + '@' + IP_CODED +'@'
            
            urls.append(url)
            flag = 0          

            newConfig = targetConfig 
            newConfig = newConfig.replace("__IP_LOCALE__", ip)
            newConfig = newConfig.replace("__PROXY_PREFIX__", PROXY_PREFIX)
            newConfig = newConfig.replace("__IP_CODED__", IP_CODED)
            newConfig = newConfig.replace("__IP_REMOTE__", IP_REMOTE)
            newConfig = newConfig.replace("__IP_PORT__", IP_PORT)
                
            with open(proxyConfigFile, 'a') as fp:
                fp.write("\n")
                fp.write(newConfig)
                fp.write("\n")
            
    flash(message, result)
    return redirect(previousUrl)     
    # return {"result": result, 'urls': urls, 'message': message}


####################################################################################
# tips view
####################################################################################

@ovpn_bp.route("/tips")
@login_required
def tips():
    """
    @summary: tips page
    @return: tips template
    """
    return render_template("ovpn/tips.html")


####################################################################################
# OVPN status views
####################################################################################
 
@ovpn_bp.route("/<any(tun,tap):mode>ClientsStatus")
@login_required
def clientsStatus(mode):
    """
    @summary: clientsStatus page
    @param mode: tun or tap mode 
    @return: clientsStatus template
    """
    
    if mode.lower() == 'tun':
        MODE = 'tun'
    else:
        MODE = 'tap'        
    
    return render_template("ovpn/{}ClientsStatus.html".format(MODE))

@ovpn_bp.route("/<any(tun,tap):mode>ClientsStatus/update/storename", methods=("GET", "POST"))
@login_required
def updateStoreName(mode):
    """
    @summary: clientsStatus page update storename
    @param mode: tun or tap mode
    @return: result
    """
    
    if mode.lower() == 'tun':
        table = 'tunovpnclients'
    else:
        table = 'ovpnclients'    
    
    if request.method == "POST":
        cn = request.values.get('cn')
        newstorename = request.values.get('newstorename')
    cur = get_cur()
    conn = get_db()
    sql = "select * from {table} where cn=%s".format(table=table)
    cur.execute(sql, (cn,))
    res = cur.rowcount
    
    if res:
        pass
    else:
        result = "cn not found"
    
    sql = "update {table} set storename=%s where cn=%s".format(table=table)    
    cur.execute(sql, (newstorename, cn))
    res = cur.rowcount
    conn.commit()
    if res:
        result = "success"
    else:
        result = "Error when update storename"
       
    return {"result": result}


def ip2hex(ip):
    """
        @summary: turn ip to hex
        @param ip: ip address
        @return: hex ip prefixed '0x' like: 0x115ff0861
    """
    l = ip.split('.')
    return '0x{:02x}{:02x}{:02x}{:02x}'.format(*map(int, l))


def generateUrl(PROXY_PREFIX, ip):
    """
        @summary: generate BOSS URL
        @param PROXY_PREFIX: PROXY_PREFIX from db
        @param ip: ip address
        @return: boss url like: RVRP@9801456451909-0xc0a8788a@
    """
    hexIp = ip2hex(ip)
    n = 13
    randomIntAddress = ''.join(["{}".format(randint(0, 9)) for num in range(0, n)])    
    return '{}-{}'.format(randomIntAddress, hexIp)

@ovpn_bp.route("/check<any(Tun,Tap):mode>ProxyConfig", methods=("POST",))
@login_required
def checkProxyConfig(mode):
    """
    @summary: Check a proxy if configured, configure it if not and open a new page to show configure for check
    @param mode: tun or tap 
    @return: result with result and url and some other info
    """
    
    if mode.lower() == 'tun':
        table = 'tunovpnclients'
        MODE="Tun"
    else:
        table = 'ovpnclients'    
        MODE="tap"
        
    if request.method == "POST":
        cn = request.values.get('cn').strip()
    
    conn = get_db()    
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    
    sql = "select * from {table} where cn=%s".format(table=table)
    cur.execute(sql, (cn,))
    res = cur.rowcount

    ovpnClient = cur.fetchone()

    url = ''
    ip = ovpnClient['ip']

    try:
        sql = "select * from sysconfig"
        cur.execute(sql)
    except Exception as e:
        message = "DB ERROR: " + str(e)
        result = "danger"
        return {"result": result, 'message': message}
    
    try:
        IP_REMOTE = app.config['IP_REMOTE']
        IP_PORT = app.config['IP_PORT']    
        PROXY_PREFIX = app.config['PROXY_PREFIX']
        APACHE_ROOT = app.config['DIR_APACHE_ROOT']
        APACHE_SUB = app.config['DIR_APACHE_SUB']
    except Exception as e:
        message = "Error: KeyError " + str(e)
        result = "danger"
        return {"result": result, 'message': message}       
    
    result='success'
    message='all good'
    
    # config proxy if not
    if len(ovpnClient['url']) < 10:
        # need to setup proxyConfig, set url to: len("RVRP@9801456451909-0xc0a8788a@") - 30 // len(9801456451909) - 13
        sql = "update {table} set url=%s where cn=%s".format(table=table)
        IP_CODED = generateUrl(PROXY_PREFIX,ip)
        url = PROXY_PREFIX + '@' + IP_CODED +'@'
        try:
            cur.execute(sql,(IP_CODED, cn))
            conn.commit()
            result='success'
            update='yes'
        except Exception as e:
            message=str(e)
            result = "danger"   
    else:
        IP_CODED = ovpnClient['url']
        update = 'no'
        url = PROXY_PREFIX + '@' + IP_CODED +'@'
    
    proxyConfigFile = pathlib.Path(APACHE_ROOT, APACHE_SUB, 'reverse_proxy_local.conf')
    proxyConfigTemplate = pathlib.Path(APACHE_ROOT, APACHE_SUB, 'boss.template')
    
    if not proxyConfigFile.exists() or not proxyConfigTemplate.exists():
        message = "Apache config file does not exited!!"
        result = "danger"
        return {"result": result, 'message': message}
    
    flag = 0
    
    with open(proxyConfigFile, 'r') as fp:
        lst = [p.strip() for p in fp.read().split('\n\n')]
    
    for lc in lst:
        if re.findall(ip, lc):
            flag = 1
            break
    
    if not flag:
        with open(proxyConfigTemplate, 'r') as fp:
            newConfig = [p.strip() for p in fp.read().split('\n\n')]
            newConfig = newConfig[0].replace("__IP_LOCALE__", ip)
            newConfig = newConfig.replace("__PROXY_PREFIX__", PROXY_PREFIX)
            newConfig = newConfig.replace("__IP_CODED__", IP_CODED)
            newConfig = newConfig.replace("__IP_REMOTE__", IP_REMOTE)
            newConfig = newConfig.replace("__IP_PORT__", IP_PORT)
        
        with open(proxyConfigFile, 'a') as fp:
            fp.write("\n")
            fp.write(newConfig)
            fp.write("\n")
    return {"result": result, 'url': url, 'message': message, 'update': update}


@ovpn_bp.route("/show<any(Tun,Tap):mode>ProxyConfig/<cn>", methods=("POST","GET"))
@login_required
def showProxyConfig(mode,cn):
    """
    @summary: Return the Proxy config from Apache config files
    @param mode: tun or tap mode 
    @param: cn name from URL
    @return: cn proxy config from Apache config files
    """
    
    if mode.lower() == 'tun':
        table = 'tunovpnclients'
        MODE="Tun"
    else:
        table = 'ovpnclients'    
        MODE="tap"
        
    conn = get_db()    
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    
    sql = "select * from {table} where cn=%s".format(table=table)
    cur.execute(sql, (cn,))
    res = cur.rowcount

    ovpnClient = cur.fetchone()

    url = ''
    ip = ovpnClient['ip']

    sql = "select * from sysconfig"
    cur.execute(sql)
    
    try:
        IP_REMOTE = app.config['IP_REMOTE']
        IP_PORT = app.config['IP_PORT']    
        PROXY_PREFIX = app.config['PROXY_PREFIX']
        APACHE_ROOT = app.config['DIR_APACHE_ROOT']
        APACHE_SUB = app.config['DIR_APACHE_SUB']
    except Exception as e:
        return "Error: KeyError " + str(e) 
    
    proxyConfigFile = pathlib.Path(APACHE_ROOT, APACHE_SUB, 'reverse_proxy_local.conf')

    flag = 0
    
    with open(proxyConfigFile, 'r') as fp:
        lst = [p.strip() for p in fp.read().split('\n\n')]
    
    for lc in lst:
        if re.findall(ip, lc):
            flag = 1
            targetConfig = lc
            break
    
    if not flag:
        result = "something wrong"
    else:
        configResult = targetConfig
        
    # restart Apache2
    result = subprocess.run('systemctl restart apache2', capture_output=True, shell=True)
    if result.returncode != 0:
        apacheResult = "Something wrong when restart Apache:<br>" + result.stdout.decode("utf-8") + '<br>'
    else:
        apacheResult = "Apache restarted successfully!<br>"
    return apacheResult + configResult.replace("\n", "<br>")


@ovpn_bp.route("/showAllProxyConfig", methods=("POST","GET"))
@login_required
def showAllProxyConfigs():
    """
    @summary: return all the proxy config from Apache config file
    @return: all proxy configs 
    """
        
    conn = get_db()    
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    
    sql = "select * from sysconfig"
    try:
        cur.execute(sql)
    except Exception as e:
        return "FATAL ERROR: " + str(e) 
    
    APACHE_ROOT = app.config['DIR_APACHE_ROOT']
    APACHE_SUB = app.config['DIR_APACHE_SUB']
    
    previousUrl = request.referrer

    proxyConfigFile = pathlib.Path(APACHE_ROOT, APACHE_SUB, 'reverse_proxy_local.conf')
    if not proxyConfigFile.exists():
        # print(previousUrl)
        # flash('Apache config directory does not exist!!', 'danger')
        return "Error: Apache config directory does not exist!!"
    
    allProxyConfigs = ''
    with open(proxyConfigFile, 'r') as fp:
        for line in fp:
            allProxyConfigs += line.replace("\n", "<br>")
    
    return "All the current Apache Proxy configs as following: <br><br>" + allProxyConfigs.replace("\n", "<br>")


@ovpn_bp.route("/showProxyConfigTempalte", methods=("POST","GET"))
@login_required
def showProxyConfigTempalte():
    """
    @return: boss proxy config tempalte 
    """
        
    conn = get_db()    
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    
    sql = "select * from sysconfig"
    try:
        cur.execute(sql)
    except Exception as e:
        return "FATAL ERROR " + str(e)
    
    APACHE_ROOT = app.config['DIR_APACHE_ROOT']
    APACHE_SUB = app.config['DIR_APACHE_SUB']

    proxyConfigFile = pathlib.Path(APACHE_ROOT, APACHE_SUB, 'boss.template')
    if not proxyConfigFile.exists():        
        return 'Error: Apache config directory does not exist!!!!'
    
    proxyConfigTempalte = ''
    with open(proxyConfigFile, 'r') as fp:
        for line in fp:
            proxyConfigTempalte += line.replace("\n", "<br>")
    
    return "Boss proxy config template as following: <br><br>" + proxyConfigTempalte.replace("\n", "<br>")

####################################################################################
# OVPN tun/tap mode generate boss clients cert
####################################################################################


@ovpn_bp.route("/generate/boss<any(Tun,Tap):mode>Client")
@login_required
def generateBossClient(mode):
    """
    generate Boss Client file page

    Returns:
        template: generateBossClient template tap/tun
    """
    
    if mode.lower() == 'tun':
        MODE = 'tun'
    else:
        MODE = 'tap'   
    
    return render_template("ovpn/{mode}IssueCert.html".format(mode=MODE))


ALLOWED_EXTENSIONS = {'req',}


def allowed_file(filename):
    """
    Verifiy if the req filename and extension are valid

    Returns:
        True/False
    """
    split_filename = filename.rsplit('.', 1)
    return '.' in filename and len(split_filename[0]) == 36 and split_filename[1].lower() in ALLOWED_EXTENSIONS

@ovpn_bp.route("/generate/<any(tun,tap):mode>Issue/upload", methods=("GET", "POST"))
@login_required
def uploadIssueCert(mode):
    """
    Generate boss cert files by uploaded boss req file

    Returns:
        template: tunIssueCert template with generate result: success/fail
    """
    
    if mode.lower() == 'tun':
        files_dir = app.config['DIR_TUN_FILES']
        mode = 'Tun'
        subdir = "tun-ovpn-files"
    else:
        files_dir = app.config['DIR_TAP_FILES']
        mode = 'Tap'
        subdir = "tap-ovpn-files"
    
    if request.method == 'POST':
        # check if the post request has the file part
        if 'upload_req' not in request.files:
            error = "No file part"
            flash(error, 'danger')
            return (url_for("ovpn.generateBossClient", mode=mode))
        
        file = request.files['upload_req']
        print (" File uploaded: " + file.filename)
        # print ("URL: " + request.url)
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect (url_for("ovpn.generateBossClient", mode=mode))
        if platform.system().startswith("Windows"):
            flash('Probably runs on windows in dev env, not allowed.', 'danger')
            return redirect (url_for("ovpn.generateBossClient", mode=mode)) 
                   
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)            
            file.save(os.path.join(files_dir, app.config['DIR_REQ'] ,filename))
            # bash /opt/ovpn_flask/vpntool/generate-boss-client-cert.sh  carel tun-ovpn-files
            generate_script = os.path.join(app.config["BASE_DIR"], 'vpntool', 'generate-boss-client-cert.sh')    
            result = subprocess.run(["bash", generate_script, files_dir, app.config['SITE_NAME'], subdir], capture_output=True, shell=False)
            # print ("--------------: " + generate_script)
            # print ("--------------: " + files_dir)
            # print ("--------------: " + app.config['SITE_NAME'])
            # print ("--------------: " + files_dir)
            if result.returncode == 0 and re.findall('SELFDEFINEDS', result.stdout.decode('utf-8'), re.MULTILINE):
                flash('Successfully generate cert file!', 'success')
                return redirect (url_for("ovpn.generateBossClient", mode=mode))
            else:
                flash(result.stdout.decode('utf-8'), 'danger')
                return redirect (url_for("ovpn.generateBossClient", mode=mode))   
        else:
            flash('Filename length is not correct, please check!', 'danger')
            return redirect (url_for("ovpn.generateBossClient", mode=mode))

####################################################################################
# OVPN tun generate generic certifications
####################################################################################

@ovpn_bp.route("/generate/generic<any(Tun,Tap):mode>Client")
@login_required
def generateGenericClient(mode):
    """
    generateBossTunClient page

    Returns:
        template: generateBossTunClient template
    """

    if mode.lower() == 'tun':
        MODE = 'tun'
    else:
        MODE = 'tap'         
    
    return render_template("ovpn/{mode}GenericIssueCert.html".format(mode=MODE))

@ovpn_bp.route("/generate/generic<any(Tun,Tap):mode>Client/create", methods=("GET", "POST"))
@login_required
def generateGenericClientCert(mode):
    """
    generateBossTunClientCert URL
    @param param: Post with argument
    @return: template with success or fail
    """
    
    if mode.lower() == 'tun':
        files_dir = app.config['TUN_FILES_DIR']
        subdir = "tun-ovpn-files"
        mode="Tun"
    else:
        files_dir = app.config['TAP_FILES_DIR']
        subdir = "tap-ovpn-files"
        mode="Tap"
    
    cn = request.values.get('new_cn')
    new_cn = cn.strip()
    if platform.system().startswith("Windows"):
        flash('Probably runs on windows in dev env, not allowed.', 'danger')
        return render_template("ovpn/tunGenericIssueCert.html") 
    if not new_cn:
        flash("CN is all space, invalid!", "danger")
        return render_template("ovpn/tunGenericIssueCert.html")    
    pattern = '^[0-9a-zA-Z_-]*$'
    
    if re.match(pattern, new_cn):
        # bash /opt/ovpn_flask/vpntool/generate-generic-client-cert.sh /opt/tun-ovpn-files cn dev tun-ovpn-files
        generate_script = os.path.join(app.config["BASE_DIR"], 'vpntool', 'generate-generic-client-cert.sh')    
        result = subprocess.run(["bash", generate_script, files_dir, new_cn, app.config['SITE_NAME'], subdir], capture_output=True, shell=False)
        print ("--------------: " + generate_script)
        print ("--------------: " + new_cn)
        print ("--------------: " + files_dir)
        print ("--------------: " + app.config['SITE_NAME'])
        print ("--------------: " + subdir)
        if result.returncode == 0 and re.findall('SELFDEFINEDS', result.stdout.decode('utf-8'), re.MULTILINE):
            flash('Successfully generate cert file for cn: ' + new_cn, 'success')
            return redirect (url_for("ovpn.generateBossClient", mode=mode))
        else:
            flash(result.stdout.decode('utf-8'), 'danger')
            return redirect (url_for("ovpn.generateBossClient", mode=mode))  
        return render_template("ovpn/tunGenericIssueCert.html")
        # generate new CN here 
    else:      
        flash("Only a-zA-Z, number, _ allowed, please check!", "danger")
        return render_template("ovpn/tunGenericIssueCert.html")       

####################################################################################
# OVPN tun mode list reqs files
####################################################################################

@ovpn_bp.route("/<any(tun,tap):mode>ReqFileList", methods=("GET", "POST"))
@login_required
def reqFileList(mode):
    """
    Req file list
        
    Returns:
        template: Req file list template
    """
    
    if mode.lower() == 'tun':
        MODE = 'tun'
    else:
        MODE = 'tap'     
    
    
    return render_template("ovpn/{mode}ReqFileList.html".format(mode=MODE))

@ovpn_bp.route("/<any(tun,tap):mode>ReqFiles/list", methods=("GET", "POST"))
@login_required
def reqFiles(mode):
    """
    TUN or TAP mode Req file list
        
    Returns:
        Json: Req file list
        
        fname = pathlib.Path('0036ddf6-a8e9-11ed-9d88-c400addbd0cf.req')
        ctime = datetime.datetime.fromtimestamp(fname.stat().st_ctime, tz=datetime.timezone.utc)
        mtime = datetime.datetime.fromtimestamp(fname.stat().st_mtime, tz=datetime.timezone.utc)
        ctime.strftime('%Y-%m-%d_%H:%M:%S')
    """
    if mode.lower() == 'tun':
        files_dir = pathlib.Path(app.config['TUN_FILES_DIR'])
        reqs_dir = pathlib.Path(app.config['TUN_FILES_DIR'], app.config['REQ_DONE_DIR']) 
    else:
        files_dir = pathlib.Path(app.config['TAP_FILES_DIR'])
        reqs_dir = pathlib.Path(app.config['TAP_FILES_DIR'], app.config['REQ_DONE_DIR']) 
    
    
    draw = request.values.get('draw')
    searchValue = request.values.get('search[value]')
    
    # list -> PosixPath('/opt/tun-ovpn-files/reqs-done/80b7caa2-b998-11ed-b796-c400ad53ffa4.req')
    
    # return none if directory does not exist
    if not files_dir.exists() or not reqs_dir.exists():
        return { 
        "draw": draw,
        "recordsFiltered": 0,
        "recordsTotal": 0,
        "data": []
        }
    
    files = [f for f in reqs_dir.iterdir() 
             if f.is_file() and re.findall('req', f.name)]
    count = len(files)
    
    # prepare return data
    data = []
    searchString = searchValue.strip()
    
    if searchString:
        for file in files:
            if re.findall(searchString, file.name):
                ctime = datetime.datetime.fromtimestamp(file.stat().st_ctime, tz=datetime.timezone.utc)
                data.append([file.name, ctime.strftime('%Y-%m-%d_%H:%M:%S'), "NA"])
    else:
        for file in files:
            ctime = datetime.datetime.fromtimestamp(file.stat().st_ctime, tz=datetime.timezone.utc)
            data.append([file.name, ctime.strftime('%Y-%m-%d_%H:%M:%S'), "NA"])
    
    # Ordering
    data.sort()
    result = {
        "draw": draw,
        "recordsFiltered": count,
        "recordsTotal": count,
        "data": data
        }
    return result

@ovpn_bp.route("/<any(tun,tap):mode>ReqFileList/download/<filename>", methods=("GET", "POST"))
@login_required
def reqFileDownload(mode,filename):
    """
    Req file download
    @param filename: send from the url     
    @return: success or fail
    """

    if mode.lower() == 'tun':
        file_path = os.path.join(app.config['TUN_FILES_DIR'],app.config['REQ_DONE_DIR'], filename)
    else:
        file_path = os.path.join(app.config['TAP_FILES_DIR'],app.config['REQ_DONE_DIR'], filename)
 
    print("You are trying to download: " + file_path, 'success')
    
    return send_file(file_path, as_attachment=True)


@ovpn_bp.route("/<any(tun,tap):mode>ReqFileList/delete", methods=("GET", "POST"))
@login_required
def reqFileDelete(mode):
    """
    Req file delete
    @param filename: send from the url     
    @return: success or fail
    """
    if mode.lower() == 'tun':
        file_dir =  os.path.join(app.config['TUN_FILES_DIR'],app.config['REQ_DONE_DIR'])
    else:
        file_dir =  os.path.join(app.config['TAP_FILES_DIR'],app.config['REQ_DONE_DIR']) 
    
    filename = request.values.get('filename')
    if filename:
        file_path = os.path.join(file_dir, filename)
        print("You are trying to delete: " + file_path, 'success')
        if os.path.exists(file_path):
            os.remove(file_path)
            return {'result':'true'}
        else:
            return {'result': 'File does not existed!'}
    else:
        return {'result': 'No filename provided!'}

####################################################################################
# OVPN tun/tap mode list certs files
####################################################################################

@ovpn_bp.route("/<any(tun,tap):mode>CertFileList", methods=("GET", "POST"))
@login_required
def certFileList(mode):
    """
    Tun cert file list
        
    Returns:
        template: Tun cert file list template
    """
    
    if mode.lower() == 'tun':
        MODE = 'tun'
    else:
        MODE = 'tap'  
    
    return render_template("ovpn/{mode}CertFileList.html".format(mode=MODE))


@ovpn_bp.route("/<any(tun,tap):mode>CertFiles/list", methods=("GET", "POST"))
@login_required
def certFiles(mode):
    """
    Cert file list
        
    Returns:
        Json: Cert file list
    """
    if mode.lower() == 'tun':
        files_dir = pathlib.Path(app.config['TUN_FILES_DIR'])
        cert_dir = pathlib.Path(app.config['TUN_FILES_DIR'], app.config['VALIDATED_DIR']) 
    else:
        files_dir = pathlib.Path(app.config['TAP_FILES_DIR'])
        cert_dir = pathlib.Path(app.config['TAP_FILES_DIR'], app.config['VALIDATED_DIR']) 
    
    
    draw = request.values.get('draw')
    searchValue = request.values.get('search[value]')
    
    # list -> PosixPath('/opt/tun-ovpn-files/reqs-done/80b7caa2-b998-11ed-b796-c400ad53ffa4.req')
    
    # return none if directory does not exist
    if not files_dir.exists() or not cert_dir.exists():
        return { 
            "draw": draw,
            "recordsFiltered": 0,
            "recordsTotal": 0,
            "data": []
        }
    
    # list -> PosixPath('/opt/tun-ovpn-files/reqs-done/80b7caa2-b998-11ed-b796-c400ad53ffa4.req')
    files = [f for f in cert_dir.iterdir() 
             if f.is_file() and re.findall('p7mb64', f.name)]
    count = len(files)
    
    # prepare return data
    data = []
    searchString = searchValue.strip()
    
    if searchString:
        for file in files:
            if re.findall(searchString, file.name):
                ctime = datetime.datetime.fromtimestamp(file.stat().st_ctime, tz=datetime.timezone.utc)
                data.append([file.name, ctime.strftime('%Y-%m-%d_%H:%M:%S'), "NA"])
    else:
        for file in files:
            ctime = datetime.datetime.fromtimestamp(file.stat().st_ctime, tz=datetime.timezone.utc)
            data.append([file.name, ctime.strftime('%Y-%m-%d_%H:%M:%S'), "NA"])

    # Ordering
    data.sort()
    result = {
        "draw": draw,
        "recordsFiltered": count,
        "recordsTotal": count,
        "data": data
        }
    return result

@ovpn_bp.route("/<any(tun,tap):mode>CertFileList/download/<filename>", methods=("GET", "POST"))
@login_required
def certFileDownload(mode,filename):
    """
    Cert file download
    @param filename: send from the url     
    @return: success or fail
    """
    
    if mode.lower() == 'tun':
        file_path = os.path.join(app.config['TUN_FILES_DIR'],app.config['VALIDATED_DIR'], filename)
    else:
        file_path = os.path.join(app.config['TAP_FILES_DIR'],app.config['VALIDATED_DIR'], filename)
    
    print("You are trying to download: " + file_path, 'success')
    return send_file(file_path,as_attachment=True)


@ovpn_bp.route("/<any(tun,tap):mode>CertFileList/delete", methods=("GET", "POST"))
@login_required
def certFileDelete(mode):
    """
    Cert file delete
    @param filename: send from the url     
    @return: success or fail
    """
    
    if mode.lower() == 'tun':
        file_dir = os.path.join(app.config['TUN_FILES_DIR'],app.config['VALIDATED_DIR'])
    else:
        file_dir = os.path.join(app.config['TAP_FILES_DIR'],app.config['VALIDATED_DIR']) 
    
    filename = request.values.get('filename')
    if filename:
        file_path = os.path.join(file_dir, filename)
        print("You are trying to delete: " + file_path, 'success')
        if os.path.exists(file_path):
            os.remove(file_path)
            return {'result':'true'}
        else:
            return {'result': 'File does not existed!'}
    else:
        return {'result': 'No filename provided!'}


####################################################################################
# OVPN tun mode generic clients files
####################################################################################

@ovpn_bp.route("/<any(tun,tap):mode>GenericCertFileList", methods=("GET", "POST"))
@login_required
def genericCertFileList(mode):
    """
    Tun generic cert file list
        
    Returns:
        template: Tun generic cert file list template
    """

    if mode.lower() == 'tun':
        MODE = 'tun'
    else:
        MODE = 'tap'     
    
    return render_template("ovpn/{mode}GenericCertFileList.html".format(mode=MODE))


@ovpn_bp.route("/<any(tun,tap):mode>GenericCertFiles/list", methods=("GET", "POST"))
@login_required
def genericCertFiles(mode):
    """
    Generic cert file list
        
    Returns:
        Json: Generic cert file list
    """
    if mode.lower() == 'tun':
        files_dir = pathlib.Path(app.config['TUN_FILES_DIR'])
        generic_dir = pathlib.Path(app.config['TUN_FILES_DIR'], app.config['GENERIC_CLIENT_DIR']) 
    else:
        files_dir = pathlib.Path(app.config['TAP_FILES_DIR'])
        generic_dir = pathlib.Path(app.config['TAP_FILES_DIR'], app.config['GENERIC_CLIENT_DIR']) 
    
    
    draw = request.values.get('draw')
    searchValue = request.values.get('search[value]')
    
    # list -> PosixPath('/opt/tun-ovpn-files/reqs-done/80b7caa2-b998-11ed-b796-c400ad53ffa4.req')
    
    # return none if directory does not exist
    if not files_dir.exists() or not generic_dir.exists():
        return { 
            "draw": draw,
            "recordsFiltered": 0,
            "recordsTotal": 0,
            "data": []
        }
    
    # list -> PosixPath('/opt/tun-ovpn-files/reqs-done/80b7caa2-b998-11ed-b796-c400ad53ffa4.req')
    files = [f for f in generic_dir.iterdir() 
             if f.is_file() and re.findall('zip', f.name)]
    count = len(files)
    
    # prepare return data
    data = []
    searchString = searchValue.strip()
    
    if searchString:
        for file in files:
            if re.findall(searchString, file.name):
                ctime = datetime.datetime.fromtimestamp(file.stat().st_ctime, tz=datetime.timezone.utc)
                data.append([file.name, ctime.strftime('%Y-%m-%d_%H:%M:%S'), "NA"])
    else:
        for file in files:
            ctime = datetime.datetime.fromtimestamp(file.stat().st_ctime, tz=datetime.timezone.utc)
            data.append([file.name, ctime.strftime('%Y-%m-%d_%H:%M:%S'), "NA"])

    # Ordering
    data.sort()
    result = {
        "draw": draw,
        "recordsFiltered": count,
        "recordsTotal": count,
        "data": data
        }
    return result

@ovpn_bp.route("/<any(tun,tap):mode>GenericCertFileList/download/<filename>", methods=("GET", "POST"))
@login_required
def genericCertFileDownload(mode, filename):
    """
    Generic cert file download
    @mode tun or tap in url
    @param filename: send from the url     
    @return: success or fail
    """
    
    if mode.lower() == 'tun':
        file_dir = os.path.join(app.config['TUN_FILES_DIR'],app.config['GENERIC_CLIENT_DIR'])
    else:
        file_dir = os.path.join(app.config['TAP_FILES_DIR'],app.config['GENERIC_CLIENT_DIR'])
    
    file_path = os.path.join(file_dir, filename)
    
    print("You are trying to download: " + file_path, 'success')
    return send_file(file_path,as_attachment=True)


@ovpn_bp.route("/<any(tun,tap):mode>GenericCertFileList/delete", methods=("GET", "POST"))
@login_required
def genericCertFileDelete(mode):
    """
    Generic cert file delete
    @param filename: send from the url     
    @return: success or fail
    """
    
    if mode.lower() == 'tun':
        file_dir = os.path.join(app.config['TUN_FILES_DIR'],app.config['GENERIC_CLIENT_DIR'])
    else:
        file_dir = os.path.join(app.config['TAP_FILES_DIR'],app.config['GENERIC_CLIENT_DIR'])  
    
    filename = request.values.get('filename')
    if filename:
        file_path = os.path.join(file_dir, filename)
        print("You are trying to delete: " + file_path, 'success')
        if os.path.exists(file_path):
            os.remove(file_path)
            return {'result':'true'}
        else:
            return {'result': 'File does not existed!'}
    else:
        return {'result': 'No filename provided!'}
    
####################################################################################
# user management views
####################################################################################
@ovpn_bp.route("/users", methods=("POST", "GET"), defaults={'page': 1})
@ovpn_bp.route("/users/<int:page>/", methods=("POST", "GET"))
@login_required
def users(page):
    """
        @summary: users page, get -> list users, post -> add or delete user
        @return: template: template ovpn/users.html
        """
    if request.method == "POST":

        form_args = request.form.to_dict()

        if request.form.get('action', None) == 'action_add_user':
            logger.info("Post action: add new user from POST, call to add new user.")
            result = OvpnUtils.add_user(form_args)
            flash(result[0], result[1])
            return redirect(url_for("ovpn.users"))

        if request.form.get('action', None) == 'action_delete_user':
            result = OvpnUtils.delete_user(form_args)
            flash(result[0], result[1])
            return redirect(url_for("ovpn.users"))

        return "BAD request!", 400
    else:
        # GET request
        page_size = int(session.get("page_size", 50))
        page = int(page)

        us = OvpnUtils.get_all_users()
        total = len(us.all())
        users = us.limit(page_size).offset((page - 1) * page_size)

        pagination = Pagination(page=page, total=total, per_page=page_size)
        return render_template("ovpn/users.html", users=users, pagination=pagination)


@ovpn_bp.route("/user/<user_id>/update", methods=("POST", "GET"))
@login_required
def user_update(user_id):
    """update-user url

        get: use update form page
        post: send new user config to update user
        
    Returns:
        redirect: Return to user list with failure/success
    """
    user = OvpnUtils.get_user_by_id(user_id)
    if not user:
        return render_template('404.html'), 404

    if request.method == "POST":
        form_args = request.form.to_dict()
        form_args.update({"uuid": user_id})
        logger.info("Update the ovpn service by the post args: " + str(form_args))
        result = OvpnUtils.update_user(form_args)
        flash(result[0], result[1])
        return redirect(request.referrer)
    else:
        return render_template("ovpn/user_update.html", user=user)


####################################################################################
# System management views
####################################################################################

@ovpn_bp.route("/system", methods=("GET", "POST"))
@login_required
def system_config():
    """system config page

    Returns:
          GET: template, system config template
          POST: update the system config and then redirect to get page with the result
    """
    # POST request
    if request.method == "POST":
        args = request.form
        result = "success"
        message = ''
        
        if len(list(args.keys())) < 1:
            message = "Error: no value submitted!"
            result = "danger"
            flash(message, result)
            return redirect(url_for("ovpn.system_config"))

        if result == "success":
            for key in list(args.keys()):
                try:
                    dbs.execute(
                        update(OfSystemConfig).where(OfSystemConfig.item == key).values(ivalue=args.get(key))
                        )
                    app.config.update({key: args.get(key)})
                    dbs.commit()
                except Exception as e:
                    message = e
                    result = "danger"
                finally:
                    pass
        
        if not message:
            message = "Update successfully!!"
        flash(message, result)      
        return redirect(url_for("ovpn.system_config"))
    
    # GET request
    scs = dbs.scalars(select(OfSystemConfig))
    return render_template("ovpn/system_config.html", scs=scs)


@ovpn_bp.route("/showAppConfig", methods=("POST","GET"))
@login_required
def show_app_config():
    """
    @return: Flask app config 
    """
    config_trs = ''
    for key in app.config.keys():
        # appConfig += "{key: <35}{val: <}".format(key=key + ":", val = str(app.config.get(key))) + '<br>'
        config_trs += "<tr><th>{}</th>\n<th>{}</th></tr>".format(key, str(app.config.get(key)))


    app_config = """
<h1>Flask App current config as following</h1> <br>
<table border="1px">
    <thead>
    <tr>
        <th>Items</th>
        <th>Values</th>
    </tr>
    </thead>
    <tbody>
    {}
    </tbody>
    </table>
""".format(config_trs)

    # return "<h1>Flask App current config as following</h1> <br><br>" + appConfig.replace("\n", "<br>")
    return app_config


@ovpn_bp.route("/showAppSession", methods=("POST","GET"))
@login_required
def show_app_session():
    """
    App session key/value list
    After proxy, the session type is werkzeug.local.LocalProxy, convert it to dict for jsonify.

    @return: Flask app session infos in json
    """
    # logger.info('####################################')
    # logger.info(type(session))
    # logger.info('####################################')
    return jsonify(dict(session))


@ovpn_bp.route("/show_url_map", methods=("POST", "GET"))
@login_required
def show_url_map():
    """
    App URL map

    @return: Flask URL map infos in json
    """
    links = []
    print(app.url_map)
    for rule in app.url_map.iter_rules():
        # print("------: " + str(type(rule)))
        # url = url_for(rule.endpoint, **(rule.defaults or {}))
        # links.append((url, rule.endpoint))
        # if len(rule.defaults) >= len(rule.arguments):
        #     url = url_for(rule.endpoint, **(rule.defaults or {}))
        #     links.append((url, rule.endpoint))
        links.append({rule.endpoint: rule.rule})
    return jsonify(links)
