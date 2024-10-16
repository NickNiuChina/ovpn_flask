import platform
import datetime
import psutil
import subprocess
import time


from myproject.context import logger
from orm.ovpn import OvpnServers
from myproject.context import DBSession as dbs
from sqlalchemy import select, update, delete


class OvpnUtils(object):
    """Ovpn utils
        
    """
    
    OVPN_SERVER_INT_COL = ['startup_type', 'learn_address_script', 'managed', 'learn_address_script', 'management_port']
    
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
    
    @classmethod
    def get_openvpn_version(cls, executor=None) -> str:
        """ Get OpenVPN version

        Args:
            executor (str, optional): Cmd to get openvpn version. Defaults to None.

        Returns:
            str: OpenVPN version string
        """
        if not platform.system().startswith("Linux"):
            # logger.info("This app is not running on linux platform now. Skip get openvpn version.")
            return ""
        try:            
            if not executor:
                res = subprocess.run(["openvpn", '--version'], capture_output = True, shell=False)
                output = res.stdout.decode("utf-8")
                lout = output.split("\n")[0]
                version = "-".join(str(x) for x in lout.split()[0:3])
                if version:
                    return version
                else:
                    return ""
            else:
                return ""
        except:
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
        
        ovpn_service = OvpnUtils.get_openvpn_service_by_id(uuid)
        if not ovpn_service:
            return "UUID not found", 'danger'
        
        try:
            logger.info("Try to delete ovpn service uuid: {}".format(uuid))
            dbs.delete(ovpn_service)
            dbs.commit()
            logger.error("Successfully delete ovpn service: {}".format(uuid))
            category = 'success'
            return "New openvpn service has beed added successfully.", category
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
    def get_all_openvpn_services(cls, filter_ovpn_server=None) -> str:
        """
        Get all OpenVPN services
        """
        logger.info("Retrieve all openvpn services from database now.")
        try:
            logger.info("Try to write new ovpn service to db.")
            servers = dbs.query(OvpnServers).all()
            return servers
        except Exception as e:
            dbs.rollback()
            logger.error(e)
            return e
        
    @classmethod
    def get_openvpn_service_by_id(cls, id=None) -> str:
        """
        Get OpenVPN service by id
        """
        logger.info("Get the ovpnserice by id: " + id)
        try:
            server = dbs.scalars(select(OvpnServers).where(OvpnServers.id == id)).first()
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
        results = {}
        if not platform.system().startswith("Linux"):
            logger.info("This app is not running on linux platform now. Skip get openvpn running status.")
            return results
        if not server:
            return results
        startup_service = server.startup_service
        if not startup_service:
            return results       
        if str(server.startup_type) == "1":
            try:
                res = subprocess.run(["systemctl", "is-active", "--quiet", startup_service], capture_output = True)
                if res.returncode == 0:
                    results.update({"status": 1})
                    return results
                else:
                    results.update ({"status": 0})
            except Exception as e:
                logger.error("Failed to get openvpn running status: {}".format(str(e)))
                results.update({"status": 0})
                return results
            
        else:
            try:
                res = subprocess.run([startup_service, "status"], capture_output = True)
                if res.returncode == 0:
                    results.update({"status": 1})
                    return results
                else:
                    results.update ({"status": 0})
            except:
                results.update({"status": 0})
                return results