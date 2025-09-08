import platform
import datetime
import psutil
import subprocess
import time

from werkzeug.security import generate_password_hash
from myproject.context import logger
from orm.ovpn import OvpnServers, OfUser, OfGroup, OvpnClients, OfSystemConfig
from myproject.context import DBSession as dbs
from sqlalchemy import select, update, delete, or_, desc, asc
from uuid import UUID
import pathlib


class OvpnUtils(object):
    """Ovpn utils
        
    """
    
    OVPN_SERVER_INT_COL = ['startup_type', 'learn_address_script', 'managed', 'learn_address_script', 'management_port']
    USER_ADD_INT_COL = ['line_size', 'page_size']
    USER_UPDATE_INT_COL = ['line_size', 'page_size', 'status']
    FAKE_PASSWORD = '_PASSWORD_'

    """
        Common methods
    """

    @classmethod
    def get_system_info(cls) -> dict:
        """Get system info

        Returns:
            dict: system information
        """
        system_type = platform.system()
        system_info = {
            "system_type": system_type,
            "system_version": platform.release(),
            "system_time": datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
            "cpu_cores": psutil.cpu_count(),
        }
        boot_time_timestamp = psutil.boot_time()
        current_time_timestamp = time.time()
        uptime_seconds = current_time_timestamp - boot_time_timestamp
        uptime_minutes = uptime_seconds // 60
        uptime_hours = uptime_minutes // 60
        uptime_days = uptime_hours // 24
        uptime_str = f"{int(uptime_days)} days,{int(uptime_hours % 24)}:{int(uptime_minutes % 60)}:{int(uptime_seconds % 60)}"

        load_avg = psutil.getloadavg()
        memory_total = round(psutil.virtual_memory().total/1024/1024, 1)
        memory_used = round(psutil.virtual_memory().used/1024/1024, 1)
        memory_percent = psutil.virtual_memory().percent
        swap_total = round(psutil.swap_memory().total/1024/1024, 1)
        swap_used = round(psutil.swap_memory().used/1024/1024, 1)
        swap_percent = round(psutil.swap_memory().percent, 1)

        if system_type.startswith("Linux"):
            openvpn_version = cls.get_openvpn_version()
        else:
            openvpn_version = "NA"
        system_information = platform.platform()

        system_info.update(
            {
                "system_uptime": uptime_str,
                "load_avg": load_avg,
                "memory_total": memory_total,
                "memory_used": memory_used,
                "memory_percent": memory_percent,
                "swap_total": swap_total,
                "swap_used": swap_used,
                "swap_percent": swap_percent,
                "openvpn_version": openvpn_version,
                "system_information": system_information
            }
        )
        # print(system_info)
        return system_info
    
    
    """
        OpenVPN services methods
    """
    
    @classmethod
    def get_openvpn_version(cls, executor=None) -> str:
        """ Get OpenVPN version

        Args:
            executor (str, optional): Cmd to get openvpn version. Defaults to None.

        Returns:
            str: OpenVPN version string
        """
        logger.debug("Trying to get the openvpn software version.")
        if not platform.system().startswith("Linux"):
            # logger.info("This app is not running on linux platform now. Skip get openvpn version.")
            return ""
        try:
            if not executor:
                logger.debug("About to run openvpn command")
                res = subprocess.run(["/usr/sbin/openvpn", '--version'], capture_output=True, shell=False)
                logger.debug("Openvpn command error: ".format(res.stderr))
                output = res.stdout.decode("utf-8")
                logger.debug("Read command output: {}".format(output))
                lout = output.split("\n")[0]
                version = "-".join(str(x) for x in lout.split()[0:3])
                if version:
                    return version
                else:
                    return ""
            else:
                return ""
        except Exception as e:
            logger.debug("Get openvpn version error: {}".format(str(e)))
            return ""
        
    @classmethod
    def add_openvpn_service(cls, new_ovpn_server=None) -> tuple:
        """ Add OpenVPN server

        Args:
            new_ovpn_server (dict): New openvpn server info in a dict

        Returns:
            tuple: result and flask flash message
        """
        logger.info("Add new openvpn service now...")
        category = None
        if not new_ovpn_server:
            logger.error("Did not receive the new openvpn service config, POST argrs error.")
            category = 'danger'
            return "Error: {}".format("No new config posted!"), category
        # remove the action from dict
        new_ovpn_server.pop('action', None)
        
        for key in OvpnUtils.OVPN_SERVER_INT_COL:
            new_ovpn_server[key] = int(new_ovpn_server[key])
                
        try:
            logger.info("Try to write new ovpn service to db.")
            
            dbs.add(OvpnServers(**new_ovpn_server))
            dbs.commit()
            logger.error("Failed to save the openvpn to database.")
            category = 'success'
            return "New openvpn service has beed added successfully.", category
        except Exception as e:
            dbs.rollback()
            logger.error(e)
            return "Failed to add new openvpn server: {}".format(e.__dict__['orig']), 'danger'

    @classmethod
    def delete_openvpn_service(cls, form_args=None) -> tuple:
        """ Delete OpenVPN server

        Args:
            form_args (dict): Posted openvpn service uuid

        Returns:
            tuple: result and flask flash message
        """
        logger.info("Delete openvpn service now...")
        category = None
        if not form_args:
            logger.error("Did not receive the openvpn service uuid, POST argrs error.")
            category = 'danger'
            return "Error: {}".format("No new config posted!"), category
        # remove the action from dict
        form_args.pop('action', None)
        uuid = form_args.pop('service_uuid', None).strip()

        try:
            service_uuid = UUID(uuid, version=1)
        except ValueError:
            return "Please input valid UUID", "danger"

        ovpn_service = OvpnUtils.get_openvpn_service_by_id(uuid)
        if not ovpn_service:
            return "UUID not found", 'danger'

        try:
            logger.info("Try to delete ovpn service uuid: {}".format(uuid))
            dbs.delete(ovpn_service)
            dbs.commit()
            logger.error("Successfully delete ovpn service: {}".format(uuid))
            category = 'success'
            return "New openvpn service has been deleted successfully.", category
        except Exception as e:
            dbs.rollback()
            logger.error(e)
            return "Failed to delete new openvpn server: {}".format(e), 'danger'

    @classmethod
    def update_openvpn_service(cls, updated_ovpn_server=None) -> tuple:
        """ Update OpenVPN service

        Args:
            updated_ovpn_server (dict): New openvpn server config from a dict

        Returns:
            tuple: result and flask flash message
        """
        logger.info("Update openvpn service ...")
        category = None
        if not updated_ovpn_server:
            logger.error("Did not receive the new openvpn service config, POST args error.")
            category = 'danger'
            return "Error: {}".format("No new config posted!"), category

        # remove the action from dict
        updated_ovpn_server.pop('action', None)
        
        for key in OvpnUtils.OVPN_SERVER_INT_COL:
            updated_ovpn_server[key] = int(updated_ovpn_server[key])
            
        try:
            logger.info("Try to update the ovpn service config.")
            target_id = updated_ovpn_server.pop('uuid', None)
            # stmt = (
            #     update(OvpnServers).where(OvpnServers.id == target_id).values(**updated_ovpn_server)
            # )
            service_query = dbs.query(OvpnServers).filter_by(id=target_id)
            # dbs.execute(stmt)
            service_query.update(updated_ovpn_server)
            logger.info("###############################################$$$$$$$$$$$$$$$$$$$$")
            dbs.commit()
            logger.info("Successfully update the ovpn service config, id: " + str(target_id))
            category = 'success'
            return ("Openvpn service has beed updated successfully.", category)
        except Exception as e:
            dbs.rollback()
            logger.error(e)
            return ("Failed to add new openvpn server: {}".format(e), 'danger')

    @classmethod
    def get_all_openvpn_services(cls, **filters) -> str:
        """
        Get all OpenVPN services
        """
        logger.info("Retrieve all openvpn services from database now.")
        try:
            logger.info("Try to run query ovpn services")
            servers = dbs.query(OvpnServers).filter_by(**filters).order_by(OvpnServers.server_name)
            return servers
        except Exception as e:
            dbs.rollback()
            logger.error(e)
            return e

    @classmethod
    def search_openvpn_services(cls, q=None) -> str:
        """
        Get all OpenVPN services
        """
        logger.info ("Search openvpn services by query string: {}".format(str(q)))
        try:
            logger.info("Try query services from db.")
            servers = dbs.query(OvpnServers).filter((OvpnServers.server_name.like(q)))
            return servers
        except Exception as e:
            dbs.rollback()
            logger.error(e)
            return e
        
    @classmethod
    def get_openvpn_service_by_id(cls, uuid=None) -> str:
        """
        Get OpenVPN service by id
        """
        logger.info("Get the ovpn service by id: " + str(uuid))
        try:
            server = dbs.scalars(select(OvpnServers).where(OvpnServers.id == str(uuid))).first()
            logger.debug("server uuid: " + str(uuid))
            logger.debug("server: " + str(server))
            return server
        except Exception as e:
            dbs.rollback()
            logger.error(e)
            return None

    @classmethod
    def get_openvpn_running_status(cls, server=None) -> dict:
        """ Get OpenVPN running status

        Args:
            server (server, optional): A server instance which has an openvpn server information.

        Returns:
            dict: Running status info, dict format.
        """
        logger.debug("Trying to get openvpn running status")
        results = {}
        if not platform.system().startswith("Linux"):
            logger.info("This app is NOT running on linux platform now. Skip get openvpn running status.")
            return results
        if not server:
            return results
        startup_service = server.startup_service
        if not startup_service:
            return results       
        if str(server.startup_type) == "1":
            try:
                res = subprocess.run(["/usr/bin/systemctl", "is-active", "--quiet", startup_service], shell=False, capture_output = True)
                if res.returncode == 0:
                    logger.debug("returned code: {}, service: {}".format(res.returncode, startup_service))
                    results.update({"status": 1})
                    return results
                else:
                    logger.debug("returned code: {}".format(res.returncode))
                    logger.error("Openvpn service is NOT running.")
                    results.update ({"status": 0})
            except Exception as e:
                logger.error("Failed to get openvpn running status: {}".format(str(e)))
                results.update({"status": 0})
                return results
            
        else:
            try:
                res = subprocess.run([startup_service, "status"], shell=True, capture_output = True)
                if res.returncode == 0:
                    results.update({"status": 1})
                    return results
                else:
                    results.update ({"status": 0})
            except:
                results.update({"status": 0})
                return results

    @classmethod
    def change_openvpn_running_status(cls, server=None, op=None) -> bool:
        """ Change OpenVPN running status

        Args:
            server (server, optional): _description_. Defaults to None.
            op (str, optional): the operation type, start, restart, stop. Defaults to None.

        Returns:
            bool: Bool
        """
        if not platform.system().startswith("Linux"):
            logger.info("This app is not running on linux platform now. Skip start/stop openvpn service.")
            return False
        if not server or not op:
            return False
        startup_service = server.startup_service
        if not startup_service:
            return False
        if op not in ['start', 'stop', 'restart']:
            return False   
        if str(server.startup_type) == "1":
            try:
                res = subprocess.run(["/usr/bin/systemctl", op, startup_service], capture_output=True)
                logger.info("Run system command now: {} {} {}".format("/usr/bin/systemctl", op, startup_service))
                if res.returncode == 0:
                    logger.info("Successfully {} the openvpn service.".format(op))
                    return True
                else:
                    logger.info("Failed to {} the openvpn service.".format(op))
                    return False
            except Exception as e:
                logger.error("Failed to {} ovpn service: {}".format(op, str(e)) )
                return False
            
        else:
            try:
                res = subprocess.run([startup_service, op], capture_output = True)
                if res.returncode == 0:
                    return True
                else:
                    return False
            except:
                return False


    """
        OpenVPN service detail methods
    """

    @classmethod
    def get_openvpn_clients_list(cls, args=None) -> dict:
        """
        @args:

            {
                'draw': '1', 
                'columns[0][data]': '', 
                'columns[0][name]': '', 
                'columns[0][searchable]': 'true', 
                'columns[0][orderable]': 'true', 
                'columns[0][search][value]': '', 
                'columns[0][search][regex]': 'false', 
                .........
                'order[0][column]': '5', 
                'order[0][dir]': 'desc', 
                'start': '0', 
                'length': '100', 
                'search[value]': '', 
                'search[regex]': 'false', 
                'action': 'action_list_ovpn_clients', 
                'ovpn_server_uuid': 'd8949edf-0a70-4a8a-9e63-5afc2e4f2a66'
            }
        
        @summary: 
            Get OpenVPN clients by post parameters and then sort|search|order

        @return:
            data = {
                'recordsFiltered': recordsFiltered,
                'recordsTotal': recordsTotal,
                'draw': draw,
                'data': [ d for d in results.values() ],
                "privs_group": group,
                'pageLength': user.page_size
            }
        """
        logger.debug("Get post args: {}".format(str(args)))
        if not args:
            return {}
        draw = args.get('draw')
        start = args.get('start')
        length = args.get('length')
        searchValue = args.get('search[value]')
        order_col = args.get("order[0][column]")
        order_direction = args.get("order[0][dir]")
        ovpn_service = args.get('ovpn_service')
        group = args.get('group')
        
        all_clients = dbs.query(OvpnClients).filter_by(server_id=ovpn_service.id)
        
        # order by 
        # https://stackoverflow.com/questions/5874579/dynamic-order-by-clause-using-sqlalchemys-sql-expression-language
        sort_columns = ("site_name", "cn", "ip", "toggle_time", "expire_date", "status")
        sort_column = sort_columns[int(order_col)]
        sort_dir = order_direction  # or "asc"
        sort = asc(sort_column) if sort_dir == "desc" else desc(sort_column)
        
        if searchValue and searchValue.strip():
            searchVar = f'%{searchValue.strip()}%'
            f_clients = dbs.query(OvpnClients).filter(OvpnClients.server_id==args.get("ovpn_server_uuid")).filter(
                or_(
                    OvpnClients.site_name.ilike(searchVar),
                    OvpnClients.cn.ilike(searchVar),
                    OvpnClients.ip.ilike(searchVar)
                    )
            ).order_by(sort)
        else:
            f_clients = dbs.query(OvpnClients).filter(OvpnClients.server_id==args.get("ovpn_server_uuid")).order_by(sort)
        
        target_clients = f_clients.limit(length).offset(start)
    
        data = {
            'recordsFiltered': f_clients.count(),
            'recordsTotal': all_clients.count(),
            'draw': draw,
            'data': [z.toDict() for z in target_clients], #[ d for d in results.values() ],
            "privs_group": group,
            # 'pageLength': user.page_size
        }
        # logger.debug('Ovpn clients list post request result: {}'.format(str(data)))
        return data

    def get_plain_certs_list(args):
        draw = args.get('draw')
        group = args.get('group')
        order_direction = args.get("order[0][dir]")
        searchValue = args.get('search[value]').strip()
        start = int(args.get('start'))
        length = int(args.get('length'))   
             
        cert_root = dbs.scalar(select(OfSystemConfig).where(OfSystemConfig.item == "DIR_CERT_ROOT")).ivalue.strip()
        logger.debug(f"Certs root: {cert_root}")
        system_type = platform.system()
        logger.debug(f"System: {system_type}")
        if system_type.startswith("Window"):
            cert_root = "D:/tmp/ovpn_flask"
            logger.debug(f"Set certs root DIR: {cert_root}")
        ovpn_service = args.get('ovpn_service')
        
        # server_name = ovpn_service.server_name
        certs_dir = ovpn_service.certs_dir
        # server_id = ovpn_service.id
        
        # extension: .conf
        suffix = ".conf"
        sub_dir = dbs.scalar(select(OfSystemConfig).where(OfSystemConfig.item == "DIR_PLAIN_CERTS")).ivalue.strip()
        
        t_path = pathlib.Path(cert_root, certs_dir, sub_dir)
        logger.debug( "Check system path: " + t_path.absolute().as_posix())
        plain_certs = []
        if t_path.exists():
            for f in list(t_path.iterdir()):
                if f.is_file() and (f.name.endswith((".conf", ".ovpn"))):
                    plain_certs.append(
                            {
                            "cert_name": f.name, 
                            "cert_size": round(f.stat().st_size/1024, 1),
                            "create_time": datetime.datetime.fromtimestamp(f.stat().st_ctime).strftime("%Y-%m-%d_%H:%M:%S")
                            }
                        )
        if order_direction == "asc":
            plain_certs = sorted(plain_certs, key=lambda x: x['cert_name'])
        else:
            plain_certs = (sorted(plain_certs, key=lambda x: x['cert_name'], reverse=True))  
        if searchValue and searchValue.strip():
            f_plain_certs = []
            for plain_cert in plain_certs:
                if plain_cert["cert_name"].upper().find(searchValue.upper()) >= 0:
                    f_plain_certs.append(plain_cert)
        else:
            f_plain_certs = plain_certs
            
        t_plain_certs = f_plain_certs[start: start+length]  
        if not plain_certs:
            failed = 1
        else:
            failed = 0
           
        data = {
            'recordsFiltered': len(f_plain_certs),
            'recordsTotal': len(plain_certs),
            'draw': draw,
            'data': t_plain_certs,
            "privs_group": group,
            "failed": failed
            # 'pageLength': user.page_size
        }
        
        return data


    def get_encrypt_certs_list(args):
        draw = args.get('draw')
        group = args.get('group')
        order_direction = args.get("order[0][dir]")
        searchValue = args.get('search[value]').strip()
        start = int(args.get('start'))
        length = int(args.get('length'))   
             
        cert_root = dbs.scalar(select(OfSystemConfig).where(OfSystemConfig.item == "DIR_CERT_ROOT")).ivalue.strip()
        logger.debug(f"Certs root: {cert_root}")
        system_type = platform.system()
        logger.debug(f"System: {system_type}")
        if system_type.startswith("Window"):
            cert_root = "D:/tmp/ovpn_flask"
            logger.debug(f"Set certs root DIR: {cert_root}")
        ovpn_service = args.get('ovpn_service')
        
        # server_name = ovpn_service.server_name
        certs_dir = ovpn_service.certs_dir
        # server_id = ovpn_service.id
        
        # extension: .conf
        suffix = ".p7mb64"
        sub_dir = dbs.scalar(select(OfSystemConfig).where(OfSystemConfig.item == "DIR_ENCRYPT_CERTS")).ivalue.strip()
        
        t_path = pathlib.Path(cert_root, certs_dir, sub_dir)
        logger.debug( "Check system path: " + t_path.absolute().as_posix())
        plain_certs = []
        if t_path.exists():
            for f in list(t_path.iterdir()):
                if f.is_file() and (f.name.endswith((".p7mb64", ))):
                    plain_certs.append(
                            {
                            "cert_name": f.name, 
                            "cert_size": round(f.stat().st_size/1024, 1),
                            "create_time": datetime.datetime.fromtimestamp(f.stat().st_ctime).strftime("%Y-%m-%d_%H:%M:%S")
                            }
                        )
        if order_direction == "asc":
            plain_certs = sorted(plain_certs, key=lambda x: x['cert_name'])
        else:
            plain_certs = (sorted(plain_certs, key=lambda x: x['cert_name'], reverse=True))  
        if searchValue and searchValue.strip():
            f_plain_certs = []
            for plain_cert in plain_certs:
                if plain_cert["cert_name"].upper().find(searchValue.upper()) >= 0:
                    f_plain_certs.append(plain_cert)
        else:
            f_plain_certs = plain_certs
            
        t_plain_certs = f_plain_certs[start: start+length]  
        if not plain_certs:
            failed = 1
        else:
            failed = 0
           
        data = {
            'recordsFiltered': len(f_plain_certs),
            'recordsTotal': len(plain_certs),
            'draw': draw,
            'data': t_plain_certs,
            "privs_group": group,
            "failed": failed
            # 'pageLength': user.page_size
        }
        
        return data    
    
    def get_reqs_list(args):
        draw = args.get('draw')
        group = args.get('group')
        order_direction = args.get("order[0][dir]")
        searchValue = args.get('search[value]').strip()
        start = int(args.get('start'))
        length = int(args.get('length'))   
             
        cert_root = dbs.scalar(select(OfSystemConfig).where(OfSystemConfig.item == "DIR_CERT_ROOT")).ivalue.strip()
        logger.debug(f"reqs root: {cert_root}")
        system_type = platform.system()
        logger.debug(f"System: {system_type}")
        if system_type.startswith("Window"):
            cert_root = "D:/tmp/ovpn_flask"
            logger.debug(f"Set certs root DIR: {cert_root}")
        ovpn_service = args.get('ovpn_service')
        
        # server_name = ovpn_service.server_name
        certs_dir = ovpn_service.certs_dir
        # server_id = ovpn_service.id
        
        # extension: .req
        suffix = ".req"
        sub_dir = dbs.scalar(select(OfSystemConfig).where(OfSystemConfig.item == "DIR_REQS")).ivalue.strip()
        
        t_path = pathlib.Path(cert_root, certs_dir, sub_dir)
        logger.debug( "Check system path: " + t_path.absolute().as_posix())
        plain_certs = []
        if t_path.exists():
            for f in list(t_path.iterdir()):
                if f.is_file() and (f.name.endswith((suffix, ))):
                    plain_certs.append(
                            {
                            "cert_name": f.name, 
                            "cert_size": round(f.stat().st_size/1024, 1),
                            "create_time": datetime.datetime.fromtimestamp(f.stat().st_ctime).strftime("%Y-%m-%d_%H:%M:%S")
                            }
                        )
        if order_direction == "asc":
            plain_certs = sorted(plain_certs, key=lambda x: x['cert_name'])
        else:
            plain_certs = (sorted(plain_certs, key=lambda x: x['cert_name'], reverse=True))  
        if searchValue and searchValue.strip():
            f_plain_certs = []
            for plain_cert in plain_certs:
                if plain_cert["cert_name"].upper().find(searchValue.upper()) >= 0:
                    f_plain_certs.append(plain_cert)
        else:
            f_plain_certs = plain_certs
            
        t_plain_certs = f_plain_certs[start: start+length]  
        if not plain_certs:
            failed = 1
        else:
            failed = 0
           
        data = {
            'recordsFiltered': len(f_plain_certs),
            'recordsTotal': len(plain_certs),
            'draw': draw,
            'data': t_plain_certs,
            "privs_group": group,
            "failed": failed
            # 'pageLength': user.page_size
        }
        
        return data       
    

    def get_zip_certs_list(args):
        draw = args.get('draw')
        group = args.get('group')
        order_direction = args.get("order[0][dir]")
        searchValue = args.get('search[value]').strip()
        start = int(args.get('start'))
        length = int(args.get('length'))   
             
        cert_root = dbs.scalar(select(OfSystemConfig).where(OfSystemConfig.item == "DIR_CERT_ROOT")).ivalue.strip()
        logger.debug(f"reqs root: {cert_root}")
        system_type = platform.system()
        logger.debug(f"System: {system_type}")
        if system_type.startswith("Window"):
            cert_root = "D:/tmp/ovpn_flask"
            logger.debug(f"Set certs root DIR: {cert_root}")
        ovpn_service = args.get('ovpn_service')
        
        # server_name = ovpn_service.server_name
        certs_dir = ovpn_service.certs_dir
        # server_id = ovpn_service.id
        
        # extension: .req
        suffix = ".zip"
        sub_dir = dbs.scalar(select(OfSystemConfig).where(OfSystemConfig.item == "DIR_ZIP_CERTS")).ivalue.strip()
        
        t_path = pathlib.Path(cert_root, certs_dir, sub_dir)
        logger.debug( "Check system path: " + t_path.absolute().as_posix())
        plain_certs = []
        if t_path.exists():
            for f in list(t_path.iterdir()):
                if f.is_file() and (f.name.endswith((suffix, ))):
                    plain_certs.append(
                            {
                            "cert_name": f.name, 
                            "cert_size": round(f.stat().st_size/1024, 1),
                            "create_time": datetime.datetime.fromtimestamp(f.stat().st_ctime).strftime("%Y-%m-%d_%H:%M:%S")
                            }
                        )
        if order_direction == "asc":
            plain_certs = sorted(plain_certs, key=lambda x: x['cert_name'])
        else:
            plain_certs = (sorted(plain_certs, key=lambda x: x['cert_name'], reverse=True))  
        if searchValue and searchValue.strip():
            f_plain_certs = []
            for plain_cert in plain_certs:
                if plain_cert["cert_name"].upper().find(searchValue.upper()) >= 0:
                    f_plain_certs.append(plain_cert)
        else:
            f_plain_certs = plain_certs
            
        t_plain_certs = f_plain_certs[start: start+length]  
        if not plain_certs:
            failed = 1
        else:
            failed = 0
           
        data = {
            'recordsFiltered': len(f_plain_certs),
            'recordsTotal': len(plain_certs),
            'draw': draw,
            'data': t_plain_certs,
            "privs_group": group,
            "failed": failed
            # 'pageLength': user.page_size
        }
        
        return data        
    
    
    """
        Users method
    """

    @classmethod
    def get_user_by_id(cls, uid=None) -> str:
        """
        Get OpenVPN service by id
        """
        logger.info("Get the user by uuid: " + str(uid))
        try:
            user = dbs.scalars(select(OfUser).where(OfUser.id == uid)).first()
            user.password = OvpnUtils.FAKE_PASSWORD
            logger.debug('user: ' + str(user))
            logger.debug("password: " + user.password)
            return user
        except Exception as e:
            dbs.rollback()
            logger.error(str(e))
            return None

    @classmethod
    def get_all_users(cls, **filters) -> str:
        """
        Get all users
        """
        logger.info("Retrieve all users services from database now.")
        try:
            logger.info("Try to run query users")
            users = dbs.query(OfUser).filter_by(**filters).order_by(OfUser.username)
            return users
        except Exception as e:
            dbs.rollback()
            logger.error(e)
            return e

    @classmethod
    def add_user(cls, new_user=None) -> tuple:
        """ Add user

        Args:
            new_user (dict): New user info in a dict

        Returns:
            tuple: result and flask flash message
        """
        logger.info("Add new user now...")
        category = None
        if not new_user:
            logger.error("Did not receive the new user config, POST argrs error.")
            category = 'danger'
            return "Error: {}".format("No new config posted!"), category
        # remove the action from dict
        new_user.pop('action', None)

        for key in OvpnUtils.USER_ADD_INT_COL:
            new_user[key] = int(new_user[key])

        # password encrypt
        new_user["password"] = generate_password_hash(new_user["password"])

        # group to group_id
        group = new_user.pop('group', "ADMIN")
        new_user["group_id"] = dbs.scalar(select(OfGroup).where(OfGroup.name == group)).id

        try:
            logger.info("Try to write new ovpn service to db.")

            dbs.add(OfUser(**new_user))
            dbs.commit()
            logger.error("Failed to save the user to database.")
            category = 'success'
            return "New user has been added successfully.", category
        except Exception as e:
            dbs.rollback()
            logger.error(e)
            return "Failed to add new user: {}".format(e), 'danger'

    @classmethod
    def delete_user(cls, form_args=None) -> tuple:
        """ Delete user

        Args:
            form_args (dict): Posted user uuid

        Returns:
            tuple: result and flask flash message
        """
        logger.info("Delete user now...")
        category = None
        if not form_args:
            logger.error("Did not receive the user uuid, POST argrs error.")
            category = 'danger'
            return "Error: {}".format("No new config posted!"), category
        # remove the action from dict
        form_args.pop('action', None)
        uuid = form_args.pop('user_uuid', None).strip()

        try:
            user_uuid = UUID(uuid, version=1)
        except ValueError:
            return "Please input valid UUID", "danger"

        user = OvpnUtils.get_user_by_id(uuid)
        if not user:
            return "UUID not found in record", 'danger'

        try:
            logger.info("Try to delete user uuid: {}".format(uuid))
            dbs.delete(user)
            dbs.commit()
            logger.error("Successfully delete user: {}".format(uuid))
            category = 'success'
            return "User has been deleted successfully.", category
        except Exception as e:
            dbs.rollback()
            logger.error(e)
            return "Failed to delete User: {}".format(e), 'danger'


    @classmethod
    def update_user(cls, updated_user=None) -> tuple:
        """ Update OpenVPN service

        Args:
            updated_ovpn_server (dict): New openvpn server config from a dict

        Returns:
            tuple: result and flask flash message
            {
                'email': 'user0@example.com', 
                'group': 'ADMIN', 
                'line_size': '300', 
                'name': 'user0', 
                'page_size': '50', 
                'password': '', 
                'status': '1', 
                'username': 'user0', 
                'uuid': '6fe6a84c-6118-4b14-b0db-6b2e72ea12a1' -
            }   
        """
        logger.info("Update user now.")
        category = None
        if not updated_user:
            logger.error("Did not receive the new user config, POST args error.")
            category = 'danger'
            return "Error: {}".format("No new config posted!"), category

        # remove the action from dict if there is
        updated_user.pop('action', None)
        
        for key in OvpnUtils.USER_UPDATE_INT_COL:
            updated_user[key] = int(updated_user[key])
            
        try:
            logger.info("Try to update the user config.")
            target_id = updated_user.pop('uuid', None)
            
            new_password = updated_user.pop('password', OvpnUtils.FAKE_PASSWORD)
            if new_password != OvpnUtils.FAKE_PASSWORD:
                updated_user['password'] = generate_password_hash(new_password)
            # group to group_id
            
            group = updated_user.pop('group', "ADMIN")
            updated_user["group_id"] = dbs.scalar(select(OfGroup).where(OfGroup.name == group)).id
                        
            # stmt = (
            #     update(OvpnServers).where(OvpnServers.id == target_id).values(**updated_ovpn_server)
            # )
            user_query = dbs.query(OfUser).filter_by(id=target_id)
            # dbs.execute(stmt)
            user_query.update(updated_user)
            logger.info("###############################################$$$$$$$$$$$$$$$$$$$$")
            dbs.commit()
            logger.info("Successfully update the ovpn service config, id: " + str(target_id))
            category = 'success'
            return ("User has beed updated successfully. new user: {}".format(updated_user), category)
        except Exception as e:
            dbs.rollback()
            logger.error(e)
            return ("Failed to update  user: {}".format(e), 'danger')