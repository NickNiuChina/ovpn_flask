import json
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.sql import text

from carelds.common.data.sql import read_device_semantics_tsdb_query, read_device_semantics_query, read_device_query, \
    read_device_tsdb_query
from carelds.common.logging.logutil import get_logger
from carelds.common.utils.database import parse_database_connection_string, build_database_connection_string


class DataInterface:
    
    def __init__(self,
                 connection_url: str,
                 logger=get_logger('data_interface', stdout = True),
                 s3cache=False,
                 s3timeout=90,
                 **kwargs):
        
        self.connection_url_tokens = parse_database_connection_string(connection_url)
        if self.connection_url_tokens is None:
            raise RuntimeError(f"Invalid URL connection string: {connection_url}")
        self.connection_url_tokens['db_catalog'] = kwargs.get('db_catalog', self.connection_url_tokens['db_catalog'])
        self.connection_url_tokens['db_schema'] = kwargs.get('db_schema', self.connection_url_tokens['db_schema'])
        
        self.user = self.connection_url_tokens['user_name']
        self.password = self.connection_url_tokens['user_pass']
        self.backend = self.connection_url_tokens['url_schema']
        self.hostname = self.connection_url_tokens['url_host']
        self.port = self.connection_url_tokens['port']
        self.db_catalog = self.connection_url_tokens['db_catalog']
        self.db_schema = self.connection_url_tokens['db_schema']
        self.connection_url = connection_url
        
        if self.user is None or self.hostname is None or self.backend is None or self.port is None:
            raise RuntimeError("Incomplete URL connection string")
        
        self.logger = logger
        self.s3cache = s3cache
        self.s3timeout = s3timeout
    
    def get_engine(self, db_catalog: str = None):
        """
        Create and return an engine object, calling code should manage its life cycle
        Returns: connection engine

        """
        connstring = build_database_connection_string(**{**self.connection_url_tokens,
                                                         **{'db_catalog': db_catalog}})
        return create_engine(connstring)
    
    def test_connection(self, db_catalog='hive'):
        """
        Check if connection to data source is working
        Returns: True if connection to data source is working

        """
        try:
            self.execute('SELECT 1', db_catalog = db_catalog)
            return True
        except:
            return False
    
    def read_device(self,
                    time_from: datetime,
                    time_to: datetime,
                    device_uid: str,
                    analysis: bool = False,
                    time_column: str = 'time_local',
                    semantics = None,
                    subsemantics: bool =True,
                    dataframe: bool = True,
                    domain: str = 'default',
                    system: int = None,
                    data_source: str = None,
                    live: bool = False):
        """
        Read device data from Trino
        Args:
            time_from: search data from this time onward (inclusive)
            time_to: search data up to this time (exclusive)
            device_uid (str): device to search
            analysis (bool): if True, include analysis outputs
            time_column (str): the time column to use: 'time_local', 'time_utc'. Default 'time_local', set 'None' to let the function decide (utc for Tera, local for RemotePRO)
            semantics (bool): extract this subset of semantics (list of str), if None ignore semantics and extract raw data, if True extract all semantics
            subsemantics (bool): whether to include or not subsemantics (subdevices for semantics)
            dataframe (bool): if True, return pd.DataFrame
            domain (str): semantic domain, default: 'default'
            system (int): source system to read from (as for now, one between: 0, 1 and 2), default None (read from all systems)
            data_source (str): source type, set to 'tsdb' to read from timescale bucket. 'system' parameter will be ignored.
            live: if True, read from live data, applies only to tsdb data source

        Returns:
            a pandas DataFrame with the retrieved data

        """
        if data_source == 'tsdb':
            return self.read_tsdb(time_from = time_from,
                                  time_to = time_to,
                                  device_uid = device_uid,
                                  semantics = semantics,
                                  dataframe = dataframe,
                                  system = system,
                                  live = live)
        
        if time_column not in ('time_local', 'time_utc', None):
            raise ValueError('Explicit time column must be one between "time_local" and "time_utc"')
        
        # Get the query to execute
        if semantics is None:
            query = read_device_query(device_uid = device_uid, time_from = time_from, time_to = time_to,
                                      time_column = time_column, analysis = analysis,
                                      system = system)
        else:
            query = read_device_semantics_query(device_uid = device_uid, time_from = time_from, time_to = time_to,
                                                time_column = time_column, analysis = analysis,
                                                semantics = semantics, subsemantics = subsemantics, domain = domain,
                                                system = system)
        
        # Is a pandas DataFrame expected?
        if dataframe:
            df = self.execute(query, pandas_options = dict(parse_dates = ['time_local', 'time_utc']), dataframe = True, db_catalog = 'hive')
            
            # Fix "value" column may be non-float
            if not pd.api.types.is_float_dtype(df["value"]):
                df["value"] = df["value"].astype('float64')
                self.logger.debug(f'Fixing column "value" dtype to "float64"')
            return df
        else:
            # Return result as engine default
            return self.execute(query, pandas_options = dict(parse_dates = ['time_local', 'time_utc']),
                                dataframe = False, db_catalog = 'hive')
    
    def read_tsdb(self,
                  time_from: datetime,
                  time_to: datetime,
                  supervisor_id: int = None,
                  supervisor_uid: str = None,
                  device_id: int = None,
                  device_uid: str = None,
                  semantics: bool = None,
                  dataframe: bool = True,
                  domain: str = 'default',
                  system: int = 1,
                  live: bool = False):
        """
        Timescale specialized device reader
        Args:
            time_from: search data from this time onward (inclusive)
            time_to: search data up to this time (exclusive)
            supervisor_id: supervisor id to read, ignored if also supervisor_uid is specified
            supervisor_uid: supervisor uid to read, overrides supervisor_id
            device_id: device id to read, ignored if also device_uid is specified
            device_uid: device uid to read, overrides device_id
            semantics: extract this subset of semantics (list of str), if None ignore semantics and extract raw data, if True extract all semantics
            dataframe: if True (default), return pd.DataFrame
            domain: semantic domain, default is 'default'
            system: source system to read from, defaults to 1 and should not be changed
            live: if True, read from live timescale database, otherwise (default) read from extracted data on S3 (Hive)

        Returns:
            a pandas DataFrame with the retrieved data

        """
        if supervisor_id is None and supervisor_uid is None and device_uid is None:
            raise RuntimeError("Supervisor must be specified if 'device_uid' is not specified too")
        if device_id is None and device_uid is None:
            raise RuntimeError("Device must be specified")
        
        """
            Get supervisor details
        """
        if supervisor_uid is not None:
            supervisor_db = self.execute(
                "SELECT supervisor_id, supervisor_uid FROM public.ds_supervisor WHERE supervisor_uid = :sup",
                params = dict(sup = supervisor_uid),
                db_catalog = 'pg_ds').fetchone()
            if supervisor_db is None:
                raise ValueError("Invalid supervisor uid")
        elif supervisor_id is not None:
            supervisor_db = self.execute(
                "SELECT supervisor_id, supervisor_uid FROM public.ds_supervisor WHERE supervisor_id = :sup AND source_system_id = :ss",
                params = dict(sup = supervisor_id, ss = system),
                db_catalog = 'pg_ds').fetchone()
            if supervisor_db is None:
                raise ValueError("Invalid supervisor id")
        else:
            supervisor_db = self.execute(
                "SELECT supervisor_id, supervisor_uid FROM public.ds_supervisor ds, public.ds_device dd "
                "WHERE ds.supervisor_id = dd.line_id and ds.source_system_id = dd.source_system_id and device_uid = :dev",
                params = dict(dev = device_uid),
                db_catalog = 'pg_ds').fetchone()
            if supervisor_db is None:
                raise ValueError("Invalid device uid")
        
        """
            Get device details
        """
        if device_uid is not None:
            device_db = self.execute(
                "SELECT device_id, device_uid FROM public.ds_device WHERE device_uid = :dev",
                params = dict(dev = device_uid),
                db_catalog = 'pg_ds').fetchone()
            if device_db is None:
                raise ValueError("Invalid device uid")
        else:
            device_db = self.execute(
                "SELECT device_id, device_uid FROM public.ds_device WHERE device_id = :dev and source_system_id = :ss and line_id = :sup",
                params = dict(dev = device_id, ss = system, sup = supervisor_db[0]),
                db_catalog = 'pg_ds').fetchone()
            if device_db is None:
                raise ValueError("Invalid device id")

        """
            Get the query to execute depending on parameters
        """
        if semantics is None or not semantics:
            query, params = read_device_tsdb_query(device = device_db[0] if live else device_db[1],
                                                   supervisor = supervisor_db[0] if live else supervisor_db[1],
                                                   time_from = time_from,
                                                   time_to = time_to,
                                                   time_column = 'time_local',
                                                   live = live)
        else:
            query, params = read_device_semantics_tsdb_query(device = device_db[0] if live else device_db[1],
                                                             supervisor = supervisor_db[0] if live else supervisor_db[1],
                                                             time_from = time_from,
                                                             time_to = time_to,
                                                             time_column = 'time_local',
                                                             semantics = semantics,
                                                             domain = domain,
                                                             system = system,
                                                             live = live)
        # Is a pandas DataFrame expected?
        if dataframe:
            df = self.execute(query,
                              params = params,
                              pandas_options = dict(parse_dates = ['time_local', 'time_utc']),
                              dataframe = True,
                              db_catalog = 'hive')
            
            # Fix "value" column may be non-float
            if not pd.api.types.is_float_dtype(df["value"]):
                df["value"] = df["value"].astype('float64')
                self.logger.debug(f'Fixing column "value" dtype to "float64"')
            return df
        else:
            # Return result as engine default
            return self.execute(query, pandas_options = dict(parse_dates = ['time_local', 'time_utc']),
                                dataframe = False, db_catalog = 'hive')
    
    def execute(self,
                sql,
                db_catalog: str,
                params: dict = dict(),
                pandas_options: dict = dict(),
                dataframe=False):
        """
        Execute a query and return the result
        Args:
            sql: SQL to execute
            params: parameters to pass as "param" to the engine object
            pandas_options: parameters to pass to pandas.read_sql function (dataframe=True)
            dataframe: if True, return a dataframe, otherwise a ResultProxy object that depends on the backend
            db_catalog: The catalog to use

        Returns: query result

        """
        engine = self.get_engine(db_catalog = db_catalog)
        query = text(sql).bindparams(**params).compile(engine, compile_kwargs = {"literal_binds": True})
        if dataframe:
            data = pd.read_sql(str(query), engine, **pandas_options)
        else:
            with engine.connect() as conn:
                data = conn.execute(query)
        return data
    
    def query(self, *args, **kwargs):
        """
        Alias of execute
        """
        return self.execute(*args, **kwargs)
    
    def get_device_timezone(self, device_uid: str):
        """
        Get a device (or plant) timezone
        Args:
            device_uid: the device to search for

        Returns: a string representing the device timezone, None if no timezone is available

        """
        res = self.execute(
            f"""SELECT entity_timezone FROM public.dim_entity_v WHERE entity_uid = '{device_uid}' LIMIT 1""",
            dataframe = False,
            db_catalog = 'pg_ds').fetchone()
        if res is None:
            return None
        return res[0]
    
    def get_device_variables_mapping(self, device_uid: str) -> pd.DataFrame:
        """
        Get variable -> semantic mapping for a given device
        Args:
            device_uid: UID of the device to search

        Returns: DataFrame with variable -> semantic mapping

        """
        return self.execute("""
                select
                    dvs.variable_id,
                    dvs.domain_id,
                    dvs.semantic_id,
                    dvs.subdevice_id,
                    ds.semantic_aggregation
                from
                    public.ds_device dv,
                    public.ds_model_variable dmv,
                    public.ds_variable_semantic dvs,
                    public.ds_semantic ds
                where
                    dmv.source_system_id = dv.source_system_id
                    and dmv.model_id = dv.model_id
                    and
                dvs.variable_id = dmv.model_variable_id
                    and ds.semantic_id = dvs.semantic_id
                    and device_uid = :device_uid""",
                            params = {'device_uid': device_uid},
                            dataframe = True,
                            db_catalog = 'pg_ds')
    
    def get_project_details(self, project_id: int = None, project_code: str = None) -> dict:
        """
        Get details for a given project
        Args:
            project_id: project id
            project_code: project code, used when project_id = None

        Returns: (dict) project details

        """
        if project_id is not None:
            pj = self.execute('''SELECT * FROM pg_ds.public.ml_project WHERE project_id = :project_id''',
                              params = dict(project_id = project_id), dataframe = True, db_catalog = 'pg_ds')
        elif project_code is not None:
            pj = self.execute('''SELECT * FROM pg_ds.public.ml_project WHERE project_code = :project_code''',
                              params = dict(project_code = project_code), dataframe = True, db_catalog = 'pg_ds')
        else:
            raise ValueError('At least one between project_id and project_code must be set')
        
        if pj.shape[0] > 0:
            return pj.iloc[0].to_dict()
        return None
    
    def get_entity_details(self, entity_uid: str) -> dict:
        """
        Get details for a given entity (plant or device)
        Args:
            entity_uid: entity uid

        Returns: (dict) entity details

        """
        entity = self.execute(f"""SELECT * FROM public.dim_entity_v WHERE entity_uid = :entity_uid""",
                              params = {'entity_uid': entity_uid}, dataframe = True, db_catalog = 'pg_ds')
        if entity.shape[0] > 0:
            return entity.iloc[0].to_dict()
        return None
    
    def get_entity_project(self, entity_uid: str, project_id: int) -> dict:
        """
        Get details for a given entity and project pair
        Args:
            entity_uid: entity uid (plant or device)
            project_id: the project id

        Returns: (dict) entity details

        """
        entity = self.execute(
            f"""SELECT * FROM projects.entity_project_v WHERE entity_uid = :entity_uid and project_id = :project_id""",
            params = {'entity_uid': entity_uid, 'project_id': project_id}, dataframe = True, db_catalog = 'pg_ds')
        if entity.shape[0] > 0:
            entity_project = entity.iloc[0].to_dict()
            if 'metadata' in entity_project and isinstance(entity_project['metadata'], str):
                if len(entity_project['metadata']) < 2:
                    entity_project['metadata'] = dict()
                else:
                    entity_project['metadata'] = json.loads(entity_project['metadata'])
            return entity_project
        return None
