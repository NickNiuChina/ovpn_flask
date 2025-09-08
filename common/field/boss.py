import re
import time
import requests
import warnings
from typing import List

from carelds.common.logging.logutil import get_logger

re_varid = re.compile('<var.*idvariable="(?P<idvar>[0-9]+).*')
re_var_by_code = re.compile('<var.* code="(?P<var_code>[^"]+)".* iddevice="(?P<device_id>[0-9]+)".* idvariable="(?P<var_id>[0-9]+)".* '
                            'description="(?P<var_desc>[^"]+)".* devaddr="(?P<device_add>[0-9.]+)".*')
re_varval = re.compile('.*<variable.* value="(?P<val>[0-9.]+)".* type="(?P<vartype>[0-9]+)" idvar="(?P<idvar>[0-9]+)".*'
                       ' readwrite="(?P<rw>[0-9.]+)".* shortdescr="(?P<var_desc_short>[^"]+)".* longdescr="(?P<var_desc_long>[^"]*)".*')
re_nav = re.compile('.*".{0,20}Boss.{0,20} not available".*')
re_device = re.compile('<device iddevice="(?P<device_id>[0-9]+)".* devdescr="(?P<device_desc>[^"]+)".* devaddr="(?P<device_addr>[0-9.]+)".+')
re_url = re.compile('(https|http|)[/:]*(?P<hostname>[^/]+).*')


class BossDevice:
    def __init__(self, device_id: int, device_desc: str, device_addr: str, boss_instance: 'BossConnector'):
        self.device_id = int(device_id)
        self.device_desc = str(device_desc)
        self.device_addr = str(device_addr)
        self.boss = boss_instance

    def get_parameters(self, parameter_codes: list = None) -> List['BossParameter']:
        """
        Search a device parameter matching the provided code (short_description)
        Args:
            parameter_codes: code(s) to search

        Returns: found parameter(s) as a list

        """
        return self.boss.get_parameters(device_id=self.device_id, short_descriptions=parameter_codes)

    def get_variable_by_code(self, variable_code: str) -> 'BossVariable':
        """
        Search a device variable matching the provided code
        Args:
            variable_code: variable code to search

        Returns: found variable

        """
        return self.boss.get_variable_by_code(device_addr=self.device_addr, var_code=variable_code)

    def __dict__(self):
        return {'device_id': self.device_id, 'device_desc': self.device_desc, 'device_addr': self.device_addr, 'boss': self.boss}

    def __repr__(self):
        return str(self.__dict__())


class BossParameter:
    def __init__(self, variable_id: int, param_long_desc: str, param_short_desc: str,
                 variable_type: int, rw: int, device_instance: BossDevice,
                 boss_instance: 'BossConnector', value=None):
        self.variable_id = int(variable_id)
        self.param_long_desc = str(param_long_desc)
        self.param_short_desc = str(param_short_desc)
        self.boss = boss_instance
        self.value = value
        self.variable_type = int(variable_type)
        self.rw = int(rw)
        self.device = device_instance

    def set_value(self, value: float):
        """
        Set this parameter value. The change is applied on the remote Boss installation but this BossVariable object
        will not reflect the change.
        Args:
            value: the value to set

        """
        if self.rw == 1:
            raise PermissionError(f'Variable/parameter "{self.variable_code}" is not writeable')
        self.boss.set_parameter(var_id=self.variable_id, value=value)

    def get_parameter(self) -> 'BossParameter':
        """
        Get an updated local instance of this BossVariabile by reading from remote Boss installation

        Returns: an updated instance of this parameter

        """
        return self.boss.get_parameters(device_id=self.device.device_id, short_descriptions=[self.param_short_desc])[0]

    def __dict__(self):
        return {'variable_id': self.variable_id, 'variable_long_desc': self.param_long_desc,
                'variable_short_desc': self.param_short_desc, 'value': self.value,
                'variable_type': self.variable_type, 'access': self.rw}

    def __repr__(self):
        return str({**self.__dict__(), **{'access': 'r' if self.rw == 1 else 'rw', 'variable_type': 'digital'
                    if self.variable_type == 1 else 'analog' if self.variable_type == 2 else 'integer'
                    if self.variable_type == 3 else 'unknown'}})


class BossVariable:
    def __init__(self, variable_code: str, variable_id: int, device_instance: BossDevice, boss_instance: 'BossConnector'):
        self.variable_code = variable_code
        self.variable_id = int(variable_id)
        self.device = device_instance
        self.boss = boss_instance

    def get_parameter(self) -> BossParameter:
        """
        Get the parameter bound to this variable

        Returns: an updated instance of the bounded parameter

        """
        return self.boss.get_parameters(device_id=self.device.device_id, variable_ids=[self.variable_id])[0]


class BossConnector:
    """
        Proxy to a Boss supervisor XML API
    """

    def __init__(self, host: str, user: str, psw: str, language: str = 'EN_en', request_try_count: int = 3,
                 logger=get_logger('boss_connector'), enforce_ssl_security: bool = False, wait_time: int = 2000):
        """
        Constructor for a BossConnector object
        Args:
            host: hostname, should not contain schema (http(s)://) neither the path (/boss/servlet...)
            user: user to login
            psw: password to login
            language: language to use when calling the boss (default 'EN_en')
            request_try_count: the retries to perform when errors occurs (default 3)
            logger: a logger instance. By default uses a dedicated stdout-only logger.
            enforce_ssl_security: if True, verify https certificate and CA whenever a request is sent to the boss device
            wait_time: time to wait before checking variable value set success, in ms (default 2000)
        """
        m_url = re_url.match(host)
        if host is None:
            raise ValueError('Invalid boss URL provided')
        self.host = m_url.group('hostname')
        self.BOSS_URL = f'https://{host}/boss/servlet/MasterXML'
        self.BOSS_USER = user
        self.BOSS_PASS = psw
        self.LANG = language
        self.traffic = 0
        self.retries = request_try_count
        self.logger = logger
        self.version = 1
        self.enforce_ssl_security = enforce_ssl_security
        self.wait_time = wait_time


    def get_device(self, device_addr: str = None, device_id: int = None):
        """
        Get device details given its address or id
        Args:
            device_addr: device address
            device_id: device id

        Returns: (BossDevice) device details

        """
        for t in range(self.retries):
            try:
                # Call Boss endpoint for device list
                def _request():
                    return requests.post(self.BOSS_URL, data=f"""<requests>
                                    <login userName="{self.BOSS_USER}" password="{self.BOSS_PASS}" />
                                    <request type="devsList" language="{self.LANG}">
                                        <element iddevices="-1" />
                                    </request>
                                </requests>
                                """, verify=self.enforce_ssl_security)
                if self.enforce_ssl_security:
                    r = _request()
                else:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        r = _request()

                # Parse output
                for line in r.text.splitlines():
                    m = re_device.match(line)
                    if m is not None and (m.group('device_addr') == device_addr or m.group('device_id') == str(device_id)):
                        return BossDevice(device_id=m.group('device_id'), device_addr=m.group('device_addr'), device_desc=m.group('device_desc'), boss_instance=self)
                    m = re_nav.match(line)
                    if m is not None:
                        self.logger.warning('Connection to supervisor has failed')
                        raise RuntimeError('Boss not available')
            except RuntimeError:
                if t >= self.retries - 1:
                    self.logger.error(f'Connection to supervisor has failed after {self.retries} retries')
                    raise
                time.sleep(2)
        return None


    def get_devices(self) -> list:
        """
        List all devices on this supervisor

        Returns: list of BossDevice objects
        """
        for t in range(self.retries):
            try:
                # Call Boss endpoint for device list
                def _request():
                    return requests.post(self.BOSS_URL, data=f"""<requests>
                                                <login userName="{self.BOSS_USER}" password="{self.BOSS_PASS}" />
                                                <request type="devsList" language="{self.LANG}">
                                                    <element iddevices="-1" />
                                                </request>
                                            </requests>
                                            """, verify=self.enforce_ssl_security)
                if self.enforce_ssl_security:
                    r = _request()
                else:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        r = _request()

                devices = list()
                # Parse output
                for line in r.text.splitlines():
                    m = re_device.match(line)
                    if m is not None:
                        devices.append(BossDevice(device_id=m.group('device_id'), device_addr=m.group('device_addr'),
                                                  device_desc=m.group('device_desc'), boss_instance=self))
                    m = re_nav.match(line)
                    if m is not None:
                        self.logger.warning('Connection to supervisor has failed')
                        raise RuntimeError('Boss not available')
                return devices
            except RuntimeError:
                if t >= self.retries - 1:
                    self.logger.error(f'Connection to supervisor has failed after {self.retries} retries')
                    raise
                time.sleep(2)


    def get_var_id(self, device_addr: str, var_code: str) -> int:
        """
        Get variable Id given device address and model variable code
        Args:
            device_addr: device address
            var_code: variable code

        Returns: variable id

        """
        for t in range(self.retries):
            try:
                # Call boss specifying device address and variable code
                def _request():
                    return requests.post(self.BOSS_URL, data=f"""<requests>
                        <login userName="{self.BOSS_USER}" password="{self.BOSS_PASS}" />
                        <request type="getVariablesInform" language="{self.LANG}" >
                            <var devaddr="{device_addr}" code="{var_code}" />
                        </request>
                    </requests>
                    """, verify=self.enforce_ssl_security)
                if self.enforce_ssl_security:
                    r = _request()
                else:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        r = _request()

                # Parse the output
                for line in r.text.splitlines():
                    m = re_varid.match(line)
                    if m is not None:
                        return int(m.groups()[0])
                    m = re_nav.match(line)
                    if m is not None:
                        self.logger.warning('Connection to supervisor has failed')
                        raise RuntimeError('Boss not available')
            except RuntimeError:
                if t >= self.retries - 1:
                    self.logger.error(f'Connection to supervisor has failed after {self.retries} retries')
                    raise
                time.sleep(2)
        return None


    def get_variable_by_code(self, device_addr: str, var_code: str):
        for t in range(self.retries):
            try:
                # Call boss specifying device address and variable code
                def _request():
                    return requests.post(self.BOSS_URL, data=f"""<requests>
                        <login userName="{self.BOSS_USER}" password="{self.BOSS_PASS}" />
                        <request type="getVariablesInform" language="{self.LANG}" >
                            <var devaddr="{device_addr}" code="{var_code}" />
                        </request>
                    </requests>
                    """, verify=self.enforce_ssl_security)
                if self.enforce_ssl_security:
                    r = _request()
                else:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        r = _request()

                # Parse the output
                for line in r.text.splitlines():
                    m = re_var_by_code.match(line)
                    if m is not None:
                        return BossVariable(variable_id=m.group('var_id'), variable_code=m.group('var_code'),
                                            device_instance=self.get_device(device_addr=device_addr), boss_instance=self)

                    m = re_nav.match(line)
                    if m is not None:
                        self.logger.warning('Connection to supervisor has failed')
                        raise RuntimeError('Boss not available')
            except RuntimeError:
                if t >= self.retries - 1:
                    self.logger.error(f'Connection to supervisor has failed after {self.retries} retries')
                    raise
                time.sleep(2)
        return None


    def get_parameters(self, device_id: int = None, device_addr: str = None, short_descriptions: list = None, variable_ids: list = None) -> list:
        """
            Get parameters list of a device (device specified by "device_id" or "device_addr")
            If "short_descriptions" list is set, only parameters that match one of the provided short descriptions are returned.
            If "short_descriptions" is a string, then only the parameter that match the description is returned
            If "variable_ids" list is set, only parameters with matching "id variable" field are returned
            If "variable_ids" is an integer, then only the parameter matching that "id variable" is returned

            Args:
                device_id: device id
                device_addr: device address
                short_descriptions: list of parameter codes to match
                variable_ids: list of variables ids to match

            Returns: parameters list
        """

        device = self.get_device(device_addr=device_addr, device_id=device_id)
        if device is not None:
            device_id = device.device_id
        else:
            return ValueError('Could not find a device given the specified device address')

        for t in range(self.retries):
            parameters = list()
            try:
                def _request():
                    ids_variable = "-1" if variable_ids is None else \
                        ','.join([str(v) for v in variable_ids]) if isinstance(variable_ids, list) else \
                        str(variable_ids)
                    return requests.post(self.BOSS_URL, data=f"""<requests>
                            <login userName="{self.BOSS_USER}" password="{self.BOSS_PASS}" />
                            <request type="paramList" language="{self.LANG}">
                                <element idDevice="{device_id}" idsVariable="{ids_variable}" />
                            </request>
                        </requests>
                        """, verify=self.enforce_ssl_security)
                if self.enforce_ssl_security:
                    r = _request()
                else:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        r = _request()

                for line in r.text.splitlines():
                    m = re_varval.match(line)
                    if m is not None:
                        if short_descriptions is not None and m.group('var_desc_short') not in \
                                ([str(s) for s in short_descriptions] if isinstance(short_descriptions, list) else [str(short_descriptions)]):
                            continue

                        try:
                            var_value = float(m.group('val'))
                        except:
                            var_value = m.group('val')

                        var = BossParameter(variable_id=m.group('idvar'), param_short_desc=m.group('var_desc_short'),
                                            param_long_desc=m.group('var_desc_long'), variable_type=m.group('vartype'),
                                            rw=m.group('rw'), boss_instance=self, device_instance=device, value=var_value)
                        parameters.append(var)
                    m = re_nav.match(line)
                    if m is not None:
                        self.logger.warning('Connection to supervisor has failed')
                        raise RuntimeError('Boss not available')
            except RuntimeError:
                if t >= self.retries - 1:
                    self.logger.error(f'Connection to supervisor has failed after {self.retries} retries')
                    raise
                time.sleep(2)
            return parameters
        return None


    def set_parameter(self, var_id: str = None, device_addr: str = None, var_code: str = None, value: float = None) -> float:
        """
        Get parameter value
        If "var_id" is None, it will be derived from "device_addr" and "var_code"

        Args:
            var_id: variable id
            device_addr: device address.
            var_code: variable code.
            value: value to set

        Returns: written value

        """
        if var_id is None and device_addr is not None and var_code is not None:
            var_id = self.get_var_id(device_addr, var_code)

        if var_id is None:
            raise ValueError('"var_id" is None and could not obtain it from "device_addr" and "var_code"')

        re_set = re.compile('<variable id="' + str(var_id) + '" state="(?P<state>(ok|[0-9]+))".+')
        for t in range(self.retries):
            try:
                def _request():
                    return requests.post(self.BOSS_URL, data=f"""<requests>
                        <login userName="{self.BOSS_USER}" password="{self.BOSS_PASS}" />
                        <request type="setParam" waittime="{self.wait_time}">
                            <element idVariable="{var_id}" value="{value}" />
                        </request>
                    </requests>
                    """, verify=self.enforce_ssl_security)
                if self.enforce_ssl_security:
                    r = _request()
                else:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        r = _request()

                for line in r.text.splitlines():
                    m = re_set.match(line)
                    if m is not None:
                        if m.groups()[0] != 'ok':
                            self.logger.warning('Parameter set check timed out')
                        return value
                    m = re_nav.match(line)
                    if m is not None:
                        self.logger.warning('Connection to supervisor has failed')
                        raise RuntimeError('Boss not available')
                raise RuntimeError('An error occurred while setting the parameter')
            except RuntimeError:
                if t >= self.retries - 1:
                    self.logger.error(f'Connection to supervisor has failed after {self.retries} retries')
                    raise
                time.sleep(2)

    def get_var_value(self, device_addr: str, var_code: str) -> float:
        """
        Read variable value
        Args:
            device_addr: device address
            var_code: variable code

        Returns: read value

        """
        for t in range(self.retries):
            try:
                def _request():
                    return requests.post(self.BOSS_URL, data=f"""<requests>
                            <login userName="{self.BOSS_USER}" password="{self.BOSS_PASS}" />
                            <request type="getVariablesValues" language="EN_en" >
                                <var devaddr="{device_addr}" code="{var_code}"/>
                            </request>
                        </requests>
                        """, verify=self.enforce_ssl_security)
                if self.enforce_ssl_security:
                    r = _request()
                else:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        r = _request()

                self.traffic += len(r.content)
                _re_varval = re.compile('<var code="' + var_code + '" value="(?P<value>[0-9.]+)">')
                for line in r.text.splitlines():
                    m = _re_varval.match(line)
                    if m is not None:
                        return float(m.groups()[0])
                    m = re_nav.match(line)
                    if m is not None:
                        self.logger.warning('Connection to supervisor has failed')
                        raise RuntimeError('Boss not available')
            except RuntimeError as err:
                if t >= self.retries - 1:
                    self.logger.error(f'Connection to supervisor has failed after {self.retries} retries')
                    raise
                time.sleep(2)

