import platform
import datetime
import psutil
import subprocess
import time


from myproject.context import logger
from orm.ovpn import OvpnServers


class OvpnUtils(object):
    """Ovpn utils
        
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
    def add_openvpn_service(cls, new_ovpn_server=None) -> str:
        """ Add OpenVPN server

        Args:
            new_ovpn_server (dict): New openvpn server info in a dict

        Returns:
            tuple: result and flask flash message
        """
        category = None
        if not new_ovpn_server:
            category = 'danger'
            return ("Error: {}".format("No new config posted!"), category)
        # OvpnServers.https://stackoverflow.com/questions/26141183/insert-a-list-of-dictionary-using-sqlalchemy-efficiently
        return ("Failed to add new openvpn server: {}".format(None), 'danger')
