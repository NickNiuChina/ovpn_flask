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
# from MySQLdb._mysql import result

from myproject.context import logger
from common.utils.bp_ovpn import OvpnUtils

ovpn_bp = Blueprint("ovpn", __name__)

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
        if request.POST.get('action', '') == "db_refresh":
            return jsonify(context)
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
# ovpn services view
####################################################################################

@ovpn_bp.route("/servers")
@login_required
def servers():
    """
    @summary: ovpn service page
    @return: template: template ovpn/servers.html
    """
    return render_template("ovpn/servers.html")

@ovpn_bp.route("/server/delete")
@login_required
def server_delete():
    """
    @summary: ovpn service page
    @return: template: template ovpn/servers.html
    """
    if request.method != 'POST':
        return HttpResponse("Page not found", status=404)
    else:
        service_uuid = request.POST.get('service_uuid').strip()
        if uuid:
            try:
                sid = uuid.UUID(service_uuid)
            except:
                sid = ''
            if sid:
                server = Servers.objects.filter(id=sid)
                if not server:
                    messages.error(request, "This uuid has not been found in record!")
                    return redirect("ovpn:servers")
                else:
                    Servers.objects.filter(id=sid).delete()
                    messages.success(request, "OpenVPN deleted successfully!")
                    return redirect("ovpn:servers")
            else:
                messages.error(request, "Please provide a valid uuid!")
                return redirect("ovpn:servers")
        else:
            messages.error(request, "UUID is required for this request")
            return redirect("ovpn:servers")

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


@ovpn_bp.route("/list/<any(tun,tap):mode>ClientsStatus", methods=("GET", "POST"))
@login_required
def listClientsStatus(mode):
    """
    @summary: List tunclientsStatus
    @param mode: tun or tap mode
    @return: all list from 'tunovpnclients' or 'ovpnclients' table based on mode
    """
    if mode.lower() == 'tun':
        table = 'tunovpnclients'
    else:
        table = 'ovpnclients'
    
    # arguments
    # post
    if request.method == "POST":
        draw = request.values.get('draw')
        start = request.values.get('start')
        length = request.values.get('length')
        searchValue = request.values.get('search[value]')
        order_col = request.values.get("order[0][column]")
        order_direction = request.values.get("order[0][dir]")
    # get
    if request.method == "GET":
        draw = request.args.get('draw') 
        start = request.args.get('start') 
        length = request.args.get('length') 
        searchValue = request.args.get('search[value]') 
        order_col = request.values.get("order[0][column]")
        order_direction = request.values.get("order[0][dir]")
    print("draw: " + draw)
    print("start: " + start)
    print("length: " + length)
    print("searchValue: " + searchValue)
    print("order_col: " + order_col)   # colum number
    print("order_direction: " + order_direction)  # desc or asc
    # SELECT storename, cn, ip, changedate, expiredate, status from tunovpnclients 
    # WHERE (storename LIKE ? OR cn LIKE ? or ip LIKE ?) 
    # ORDER BY status desc 
    # LIMIT ? OFFSET ?
    query = None

    # prepare sql for tb_student
    # cursor.execute("SELECT * FROM test WHERE text LIKE %s", f"%{param}%") # sql prepare

    columns = ['storename', 'cn', 'ip', 'changedate', 'status']
    query = "SELECT * FROM {}".format(table)
    total_sql = "SELECT * FROM {}".format(table)
    if searchValue:
        query += " WHERE "
        flag = 0 # notify wether OR if needed
        # skip search for changedate and status
        for col in columns[:3]:
            if flag:
                query += " OR UPPER({column}) LIKE UPPER(%s) ".format(column=col)
            else:
                query += " UPPER({column}) LIKE UPPER(%s) ".format(column=col)
                flag += 1
    query += " ORDER BY {0} {1}".format(columns[ int(order_col) - 1 ], order_direction)
    if length:
        query += " LIMIT {0} OFFSET {1}".format(length, start)
    print(__name__ + ": --------sql----------------------")
    print(query)
    print(__name__ + ": --------sql----------------------")
    cur = get_cur()
    
    # total students
    cur.execute(total_sql)
    total = cur.rowcount
    
    # table list
    # query = "SELECT * FROM {}".format(table)
    ftotal = 0
    if searchValue:
        cur.execute(query, [f"%{searchValue}%"] * len(columns[:3]))
        ftotal =  cur.rowcount
    else:
        ftotal = cur.execute(query)
        ftotal = total
    results = cur.fetchall()  # is list

    data = {
        'recordsFiltered': ftotal,
        'recordsTotal': total,
        'draw': draw,
        'privs': session['username'],
        'data': results
    }
    
    print (data)
    return data


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

@ovpn_bp.route("/list/users", methods=("GET", "POST"))
@login_required
def listUsers():
    """
    List users
        
    Returns:
        objects: all list from user table
    """
    
    # arguments
    # post
    if request.method == "POST":
        draw = request.values.get('draw')
        start = request.values.get('start')
        length = request.values.get('length')
        searchValue = request.values.get('search[value]')
        order_col = request.values.get("order[0][column]")
        order_direction = request.values.get("order[0][dir]")
    # get
    if request.method == "GET":
        draw = request.args.get('draw') 
        start = request.args.get('start') 
        length = request.args.get('length') 
        searchValue = request.args.get('search[value]') 
        order_col = request.values.get("order[0][column]")
        order_direction = request.values.get("order[0][dir]")
    print("draw: " + draw)
    print("start: " + start)
    print("length: " + length)
    print("searchValue: " + searchValue)
    print("order_col: " + order_col)   # colum number
    print("order_direction: " + order_direction)  # desc or asc
    # SELECT storename, cn, ip, changedate, expiredate, status from tunovpnclients 
    # WHERE (storename LIKE ? OR cn LIKE ? or ip LIKE ?) 
    # ORDER BY status desc 
    # LIMIT ? OFFSET ?
    query = None

    # prepare sql for tb_student
    # cursor.execute("SELECT * FROM test WHERE text LIKE %s", f"%{param}%") # sql prepare

    columns = ['user_type', 'username', 'display_name', 'status']
    query = "SELECT * FROM tb_user"
    
    total_sql = "SELECT * FROM tb_user"
    if searchValue:
        query += " WHERE "
        query +=" username LIKE %s or display_name like %s "

    query += " ORDER BY {0} {1}".format(columns[ int(order_col) - 1 ], order_direction)
    if length:
        query += " LIMIT {0} OFFSET {1}".format(length, start)
    print(__name__ + ": --------sql----------------------")
    print(query)
    print(__name__ + ": --------sql----------------------")
    cur = get_cur()
    
    # total students
    cur.execute(total_sql)
    total = cur.rowcount
    
    # table list
    # query = "SELECT * FROM {}".format(table)
    ftotal = 0
    if searchValue:
        cur.execute(query, [f"%{searchValue}%"] * 2)
        ftotal =  cur.rowcount
    else:
        ftotal = cur.execute(query)
        ftotal = total
    results = cur.fetchall()  # is list

    data = {
        'recordsFiltered': ftotal,
        'recordsTotal': total,
        'draw': draw,
        'data': results
    }
    
    print (data)
    return data


@ovpn_bp.route("/users")
@login_required
def adminUser():
    """user admin page

    Returns:
        template: introduction template
    """
    return render_template("ovpn/users.html")

@ovpn_bp.route("/admin/updateUser", methods=("POST",))
@login_required
def updateUser():
    """update-user url

    Returns:
        redirect: Return to user list with failure/success
    """
    user_id = None
    username = None
    password = None
    display_name = None

    if request.method == "POST":
        user_id = request.values.get('user_id')
        user_type = request.values.get('user_type')
        username = request.values.get('username')
        password = request.values.get('password')
        display_name = request.values.get('display_name')
    if any(x is None for x in [username, password]):
        error = "Null value submited, Info: " + str([username, password])
        flash(error, 'danger')
        return redirect(url_for("ovpn.adminUser"))
    
    args = [user_id, user_type, username, password, display_name]    
    cur = get_cur()
    
    # students list
    update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("update tb_user set" 
                " username=%s,"
                " user_type=%s,"
                " password=%s,"
                " display_name=%s,"
                " update_time=%s"
                " where user_id=%s", [username, user_type, generate_password_hash(password), display_name, update_time, user_id])
    result = cur.rowcount
    get_db().commit()
    if result < 1:
        error = "Failed during update user. User: " + username
        flash(error, 'danger')
        return redirect(url_for("ovpn.adminUser"))
    
    success = "User info has just been changed! User: " + str(args)
    flash(success, 'success')
    return redirect(url_for("ovpn.adminUser"))

@ovpn_bp.route("/admin/getUser", methods=("GET", "POST"))
@login_required
def getUser():
    """admin-user get a user by user_id

    Returns:
        students: students object
    """
    user_id = None
    # post
    if request.method == "POST":
        user_id = request.values.get('user_id')
    # get
    if request.method == "GET":
        user_id = request.args.get('user_id')    
    
    cur = get_db().cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    
    # User object
    cur.execute("select * from tb_user where user_id = %s", (user_id,))
    user = cur.fetchone()
    print(user)
    return jsonify(user)

@ovpn_bp.route("/admin/delete/user", methods=("GET", "POST"))
@login_required
def deleteUser():
    """ delete a user by user info
        
    Returns:
        result: redirect to user admin page with failure/sucess
    """
    # arguments
    # post
    if request.method == "POST":
        username = request.values.get('username')
        # op = request.values.get('op')

    # get
    if request.method == "GET":
        username = request.args.get('username') 
        # op = request.args.get('op') 
    if username == "admin":
        error = "You can not delete admin!"
        flash(error, 'danger')
        return redirect(url_for("ovpn.adminUser"))
    
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT username FROM tb_user where username=%s", (username,)
    )
    if cur.rowcount < 1:
        error = "您尝试删除的用户不存在: " + username
        flash(error, 'danger')
        return redirect(url_for("ovpn.adminUser"))

    cur.execute("delete from tb_user where username = %s", (username,))
    db.commit()
    if cur.rowcount < 1:
        error = "Failed during delete user. User: " + username
        flash(error, 'danger')
        return redirect(url_for("ovpn.adminUser"))
    success = "Delete user successfully. User: " + username
    flash(success, 'success')    
    return redirect(url_for("ovpn.adminUser"))

@ovpn_bp.route("/admin/user/addStudent", methods=("POST",))
@login_required
def addUser():
    """ Add a new user account
        
    Returns:
        result: redirect to user admin page with failure/success
    """
    # arguments
    if request.method == "POST":
        username = request.values.get('username')
        priv = request.values.get('priv')
        password = request.values.get('password')
        displayName = request.values.get('display-name')
        
    # get
    if request.method == "GET":
        username = request.args.get('username') 
        priv = request.args.get('priv') 
        password = request.args.get('password') 
        displayName = request.args.get('display-name')

    if len(username) < 4 or len(password) < 4:
        danger = "Username or password too short!"
        flash(danger, 'danger')    
        return redirect(url_for("ovpn.adminUser"))
    
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "select * from tb_user where username=%s or display_name=%s",(username, displayName)
    )
    
    if cur.rowcount > 0:
        danger = "Duplicated username or display name: " + str([username, displayName])
        flash(danger, 'danger')    
        return redirect(url_for("ovpn.adminUser"))
    
    cur.execute(
        "insert into tb_user"
        " (user_type, username, password, display_name, status)"
        " VALUES (%s, %s, %s, %s, %s)", (int(priv), username, generate_password_hash(password), displayName, 1)
    )
    db.commit()
    if cur.rowcount < 1:
        danger = "Something wrong when add user. User: " + str([username, displayName])
        flash(danger, 'danger')    
        return redirect(url_for("ovpn.adminUser"))   
    
    success = "Add student user successfully. User: " + str([username, displayName, password])
    flash(success, 'success')
    return redirect(url_for("ovpn.adminUser"))


@ovpn_bp.route("/admin/user/toggle", methods=("GET", "POST"))
@login_required
def toggleUser():
    """ toggle a user status
        
    Returns:
        result: redirect to User admin page with failure/sucess
    """
    # arguments
    # post
    if request.method == "POST":
        target_user = request.values.get('target_user')
        user_status = request.values.get('user_status')

    # get
    if request.method == "GET":
        target_user = request.args.get('target_user') 
        user_status = request.args.get('user_status')
    print("userstatus: " + user_status)
    print("target_user: " + target_user)
    if not(user_status == "1" or user_status == "0"):
        error = "Error occurs, user_status: " + user_status
        flash(error, 'danger')
        return redirect(url_for("ovpn.adminUser"))
     
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT username FROM tb_user where username=%s", (target_user,)
    )
    result = cur.rowcount
    if not result:
        error = "The user does not exist: " + target_user
        flash(error, 'danger')
        return redirect(url_for("ovpn.adminUser"))

    if user_status == "1":
        user_status = 0
    else:
        user_status = 1
    update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("update tb_user set status=%s, update_time=%s where username = %s", 
                         (user_status, update_time,target_user)
                         )
    result = cur.rowcount
    db.commit()
    if not result:
        error = "Failed during toggle user status. User: " + target_user
        flash(error, 'danger')
        return redirect(url_for("ovpn.adminUser"))
    
    success = "Toggle user successfully. User: " + target_user
    flash("fffffffffffffffffffffffffffffffffffffffffffffff", 'danger')
    print("########################################################################################################################")    
    return redirect (url_for("ovpn.adminUser"))

####################################################################################
# System management views
####################################################################################

@ovpn_bp.route("/system", methods=("GET", "POST"))
@login_required
def systemConfig():
    """system config page

    Returns:
        template: system config template
    """
    return render_template("ovpn/systemConfig.html")


@ovpn_bp.route("/system/config", methods=("GET", "POST"))
@login_required
def systemConfigs():
    """system config API

    Returns:
        template: system config object from db
    """
    # post
    if request.method == "POST":
        draw = request.values.get('draw')
        
    cur = get_db().cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    
    # sysconfig object
    try:
        cur.execute("select * from sysconfig order by id asc")
        ftotal = cur.rowcount
        configs = cur.fetchall()
    except Exception as e:
        ftotal = 0
        configs = []
    
    data = {
        'recordsFiltered': ftotal,
        'recordsTotal': ftotal,
        'draw': draw,
        'data': configs
    }

    return jsonify(data)


@ovpn_bp.route("/system/updateConfig", methods=("POST",))
@login_required
def systemConfigsUpdate():
    """system config update API

    Returns:
        redict: systemConfig with flash result
    """
    # post
    if request.method == "POST":
        args = request.form
    
    conn = get_db()    
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

    result = "success"
    # UPDATE table_name SET column_name1= value1, column_name2= value2
    sql = "UPDATE sysconfig SET"
    
    flag=0
    
    message = ''
    
    if len(list(args.keys())) < 1:
            message = "Error: no value submited!"
            result = "danger"
            return {"result": result, 'message': str(message)}
    
    for key in list(args.keys()):
        if not args.get(key):
            message = "Error: null value submited!"
            result = "danger"
            return {"result": result, 'message': str(message)}

    sql = "update sysconfig set ivalue=%s where item=%s"  
    if result == "success":
        for key in list(args.keys()):
            try:
                cur.execute(sql, (args.get(key), key))
                app.config.update({key: args.get(key)})
                conn.commit()
            except Exception as e:
                message = e
                result = "danger"
                return {"result": result, 'message': str(message)}
            finally:
                pass
    
    if not message:
        message = "Update successfully!!"
                          
    # return redirect (url_for("ovpn.systemConfig"))
    return {"result": result, 'message': str(message)}


@ovpn_bp.route("/showAppConfig", methods=("POST","GET"))
@login_required
def showAppConfig():
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
def showAppSession():
    """
    @return: Flask app session 
    """
    from flask import jsonify
    return jsonify(session)
