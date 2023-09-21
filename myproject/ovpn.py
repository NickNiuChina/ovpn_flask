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

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from myproject.auth import login_required
from myproject.db import get_cur, get_db
#from MySQLdb._mysql import result

bp = Blueprint("ovpn", __name__, url_prefix='/')

####################################################################################
# test pages
####################################################################################
@bp.route("/test", methods=('GET', 'POST'))
def test():
    """
    test page
        This is for test purpose only.

    Returns:
        list: flask will take the list or dict and turns to jason automatically.
    """
    return "Hello 世界！", 200

####################################################################################
# Main page
####################################################################################
@bp.route("/")
@login_required
def index():
    """ 
    @summary: Main page
    @return: Main page templates and recently 5 launched clients
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
    
    return render_template("ovpn/main.html", topOnline=topOnline)

####################################################################################
# introduction view
####################################################################################

@bp.route("/introduction")
@login_required
def introduction():
    """
    @summary: introduction page
    @return: template: introduction template
    """
    return render_template("ovpn/introduction.html")

####################################################################################
# tips view
####################################################################################

@bp.route("/tips")
@login_required
def tips():
    """tips page

    Returns:
        template: tips template
    """
    return render_template("ovpn/tips.html")


####################################################################################
# OVPN status views
####################################################################################
 
@bp.route("/<any(tun,tap):mode>ClientsStatus")
@login_required
def clientsStatus(mode):
    """
    tun or tap clientsStatus page

    Returns:
        template: tun or tap clientsStatus template
    """
    
    if mode.lower() == 'tun':
        MODE = 'tun'
    else:
        MODE = 'tap'        
    
    return render_template("ovpn/{}ClientsStatus.html".format(MODE))
 
@bp.route("/list/<any(tun,tap):mode>ClientsStatus", methods=("GET", "POST"))
@login_required
def listClientsStatus(mode):
    """
    List tunclientsStatus
        
    Returns:
        objects: all list from 'tunovpnclients' table
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

@bp.route("/<any(tun,tap):mode>ClientsStatus/update/storename", methods=("GET", "POST"))
@login_required
def updateStoreName(mode):
    """
    tun or tap clientsStatus page update storename

    Returns:
        result: result:result
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


####################################################################################
# OVPN tun/tap mode generate boss clients cert
####################################################################################

@bp.route("/generate/boss<any(Tun,Tap):mode>Client")
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

@bp.route("/generate/<any(tun,tap):mode>Issue/upload", methods=("GET", "POST"))
@login_required
def uploadIssueCert(mode):
    """
    Generate boss cert files by uploaded boss req file

    Returns:
        template: tunIssueCert template with generate result: success/fail
    """
    
    if mode.lower() == 'tun':
        files_dir = app.config['TUN_FILES_DIR']
        mode = 'Tun'
        subdir = "tun-ovpn-files"
    else:
        files_dir = app.config['TAP_FILES_DIR']
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
            file.save(os.path.join(files_dir, app.config['REQ'] ,filename))
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
                flash('Something wrong, please report!', 'danger')
                return redirect (url_for("ovpn.generateBossClient", mode=mode))   
        else:
            flash('Filename length is not correct, please check!', 'danger')
            return redirect (url_for("ovpn.generateBossClient", mode=mode))

####################################################################################
# OVPN tun generate generic certifications
####################################################################################

@bp.route("/generate/generic<any(Tun,Tap):mode>Client")
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

@bp.route("/generate/generic<any(Tun,Tap):mode>Client/create", methods=("GET", "POST"))
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
    else:
        files_dir = app.config['TAP_FILES_DIR']
        subdir = "tap-ovpn-files"
    
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
        result = subprocess.run(["bash", generate_script, new_cn, files_dir, app.config['SITE_NAME'], subdir], capture_output=True, shell=False)
        # print ("--------------: " + generate_script)
        # print ("--------------: " + files_dir)
        # print ("--------------: " + app.config['SITE_NAME'])
        # print ("--------------: " + files_dir)
        if result.returncode == 0 and re.findall('SELFDEFINEDS', result.stdout.decode('utf-8'), re.MULTILINE):
            flash('Successfully generate cert file for cn: ' + new_cn, 'success')
            return redirect (url_for("ovpn.generateBossClient", mode=mode))
        else:
            flash('Something wrong, please report!', 'danger')
            return redirect (url_for("ovpn.generateBossClient", mode=mode))  
        return render_template("ovpn/tunGenericIssueCert.html")
        # generate new CN here 
    else:      
        flash("Only a-zA-Z, number, _ allowed, please check!", "danger")
        return render_template("ovpn/tunGenericIssueCert.html")       

####################################################################################
# OVPN tun mode list reqs files
####################################################################################

@bp.route("/<any(tun,tap):mode>ReqFileList", methods=("GET", "POST"))
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

@bp.route("/<any(tun,tap):mode>ReqFiles/list", methods=("GET", "POST"))
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
        reqs_dir = pathlib.Path(app.config['TUN_FILES_DIR'], app.config['REQ_DONE']) 
    else:
        files_dir = pathlib.Path(app.config['TAP_FILES_DIR'])
        reqs_dir = pathlib.Path(app.config['TAP_FILES_DIR'], app.config['REQ_DONE']) 
    
    
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

@bp.route("/<any(tun,tap):mode>ReqFileList/download/<filename>", methods=("GET", "POST"))
@login_required
def reqFileDownload(mode,filename):
    """
    Req file download
    @param filename: send from the url     
    @return: success or fail
    """

    if mode.lower() == 'tun':
        file_path = os.path.join(app.config['TUN_FILES_DIR'],app.config['REQ_DONE'], filename)
    else:
        file_path = os.path.join(app.config['TAP_FILES_DIR'],app.config['REQ_DONE'], filename)
 
    print("You are trying to download: " + file_path, 'success')
    
    return send_file(file_path, as_attachment=True)


@bp.route("/<any(tun,tap):mode>ReqFileList/delete", methods=("GET", "POST"))
@login_required
def reqFileDelete(mode):
    """
    Req file delete
    @param filename: send from the url     
    @return: success or fail
    """
    if mode.lower() == 'tun':
        file_dir =  os.path.join(app.config['TUN_FILES_DIR'],app.config['REQ_DONE'])
    else:
        file_dir =  os.path.join(app.config['TAP_FILES_DIR'],app.config['REQ_DONE']) 
    
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

@bp.route("/<any(tun,tap):mode>CertFileList", methods=("GET", "POST"))
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


@bp.route("/<any(tun,tap):mode>CertFiles/list", methods=("GET", "POST"))
@login_required
def certFiles(mode):
    """
    Cert file list
        
    Returns:
        Json: Cert file list
    """
    if mode.lower() == 'tun':
        files_dir = pathlib.Path(app.config['TUN_FILES_DIR'])
        cert_dir = pathlib.Path(app.config['TUN_FILES_DIR'], app.config['VALIDATED']) 
    else:
        files_dir = pathlib.Path(app.config['TAP_FILES_DIR'])
        cert_dir = pathlib.Path(app.config['TAP_FILES_DIR'], app.config['VALIDATED']) 
    
    
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

@bp.route("/<any(tun,tap):mode>CertFileList/download/<filename>", methods=("GET", "POST"))
@login_required
def certFileDownload(mode,filename):
    """
    Cert file download
    @param filename: send from the url     
    @return: success or fail
    """
    
    if mode.lower() == 'tun':
        file_path = os.path.join(app.config['TUN_FILES_DIR'],app.config['VALIDATED'], filename)
    else:
        file_path = os.path.join(app.config['TAP_FILES_DIR'],app.config['VALIDATED'], filename)
    
    print("You are trying to download: " + file_path, 'success')
    return send_file(file_path,as_attachment=True)


@bp.route("/<any(tun,tap):mode>CertFileList/delete", methods=("GET", "POST"))
@login_required
def certFileDelete(mode):
    """
    Cert file delete
    @param filename: send from the url     
    @return: success or fail
    """
    
    if mode.lower() == 'tun':
        file_dir = os.path.join(app.config['TUN_FILES_DIR'],app.config['VALIDATED'])
    else:
        file_dir = os.path.join(app.config['TAP_FILES_DIR'],app.config['VALIDATED']) 
    
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

@bp.route("/<any(tun,tap):mode>GenericCertFileList", methods=("GET", "POST"))
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


@bp.route("/<any(tun,tap):mode>GenericCertFiles/list", methods=("GET", "POST"))
@login_required
def genericCertFiles(mode):
    """
    Generic cert file list
        
    Returns:
        Json: Generic cert file list
    """
    if mode.lower() == 'tun':
        files_dir = pathlib.Path(app.config['TUN_FILES_DIR'])
        generic_dir = pathlib.Path(app.config['TUN_FILES_DIR'], app.config['GENERIC_CLIENT']) 
    else:
        files_dir = pathlib.Path(app.config['TAP_FILES_DIR'])
        generic_dir = pathlib.Path(app.config['TAP_FILES_DIR'], app.config['GENERIC_CLIENT']) 
    
    
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

@bp.route("/<any(tun,tap):mode>GenericCertFileList/download/<filename>", methods=("GET", "POST"))
@login_required
def genericCertFileDownload(mode, filename):
    """
    Generic cert file download
    @mode tun or tap in url
    @param filename: send from the url     
    @return: success or fail
    """
    
    if mode.lower() == 'tun':
        file_dir = os.path.join(app.config['TUN_FILES_DIR'],app.config['GENERIC_CLIENT'])
    else:
        file_dir = os.path.join(app.config['TAP_FILES_DIR'],app.config['GENERIC_CLIENT'])
    
    file_path = os.path.join(file_dir, filename)
    
    print("You are trying to download: " + file_path, 'success')
    return send_file(file_path,as_attachment=True)


@bp.route("/<any(tun,tap):mode>GenericCertFileList/delete", methods=("GET", "POST"))
@login_required
def genericCertFileDelete(mode):
    """
    Generic cert file delete
    @param filename: send from the url     
    @return: success or fail
    """
    
    if mode.lower() == 'tun':
        file_dir = os.path.join(app.config['TUN_FILES_DIR'],app.config['GENERIC_CLIENT'])
    else:
        file_dir = os.path.join(app.config['TAP_FILES_DIR'],app.config['GENERIC_CLIENT'])  
    
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

@bp.route("/list/users", methods=("GET", "POST"))
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


@bp.route("/users")
@login_required
def adminUser():
    """user admin page

    Returns:
        template: introduction template
    """
    return render_template("ovpn/users.html")

@bp.route("/admin/updateUser", methods=("POST",))
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

@bp.route("/admin/getUser", methods=("GET", "POST"))
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

@bp.route("/admin/delete/user", methods=("GET", "POST"))
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
    user = cur.fetchone()
    if user is None:
        error = "您尝试删除的用户不存在: " + username
        flash(error, 'danger')
        return redirect(url_for("ovpn.adminUser"))

    result = cur.execute("delete from tb_user where username = %s", (username,))
    db.commit()
    if result < 1:
        error = "Failed during delete user. User: " + username
        flash(error, 'danger')
        return redirect(url_for("ovpn.adminUser"))
    success = "Delete user successfully. User: " + username
    flash(success, 'success')    
    return redirect(url_for("ovpn.adminUser"))

@bp.route("/admin/user/addStudent", methods=("POST",))
@login_required
def addUser():
    """ add a student user account
        
    Returns:
        result: redirect to user admin page with failure/sucess
    """
    # arguments
    if request.method == "POST":
        username = request.values.get('student_username')
        student_no = request.values.get('student_no')
        password = request.values.get('password')

    # get
    if request.method == "GET":
        username = request.args.get('student_username') 
        student_no = request.args.get('student_no') 
        password = request.args.get('password') 
    
    db = get_db()
    cur = db.cursor()
    result = cur.execute(
        "select * from tb_user where username=%s or student_no=%s",(username, student_no)
    )
    
    if result > 0:
        danger = "Duplicated username or student account has been created before: " + str([username, student_no])
        flash(danger, 'danger')    
        return redirect(url_for("ovpn.adminUser"))
    
    result = cur.execute(
        "select * from tb_student where student_no=%s",(student_no,)
    )
    
    if result < 1:
        danger = "Student info has not been enrolled: " + str([student_no,username,password])
        flash(danger, 'danger')    
        return redirect(url_for("ovpn.adminUser"))
    
    result = cur.execute(
        "insert into tb_user"
        " (user_type, username, password, student_no, status)"
        " VALUES (%s, %s, %s, %s, %s)", (0, username, generate_password_hash(password), student_no, 1)
    )
    db.commit()
    if result < 1:
        danger = "Something wrong when add user. User: " + str([username, student_no])
        flash(danger, 'danger')    
        return redirect(url_for("ovpn.adminUser"))   
    
    success = "Add student user successfully. User: " + str([username, student_no, password, result])
    flash(success, 'success')
    return redirect(url_for("ovpn.adminUser"))

@bp.route("/admin/user/toggle", methods=("GET", "POST"))
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
@bp.route("/system")
@login_required
def systemConfig():
    """system config page

    Returns:
        template: system config template
    """
    return render_template("ovpn/systemConfig.html")       