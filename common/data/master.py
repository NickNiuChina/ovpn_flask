import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql import text
from sqlalchemy.sql.elements import TextClause


class MasterDataInterface:

    def __init__(self, connection_uri, test_connection=True, **kwargs):
        """
        Create proxy object to master database
        Args:
            connection_uri: database full connection string
            test_connection: test connection before returning object
            **kwargs: additional arguments to pass to sqlalchemy.create_engine
        """
        self.engine = create_engine(connection_uri, **kwargs)
        self.smaker = sessionmaker(bind=self.engine, autocommit=False)
        self.connection_uri = connection_uri
        if test_connection:
            assert self._test_connection(), "Could not verify connection to Master Database"

    def _test_connection(self):
        try:
            res = self.execute(''' SELECT :test_value v, 'Test Master Database connection' s''', params={'test_value': 1}).fetchone()
            if res.v != 1:
                raise ConnectionError('Could not verify connection to Master Database (invalid test value)')
        except Exception as e:
            return False
        return True


    def execute(self, sql, params=dict(), dataframe=False):
        """
        Executes a query in autocommit

        Args:
            sql: query to execute
            params: query parameters
            dataframe: if True, a dataframe is returned. Expecting a SELECT query, no commit is performed

        Returns: results

        """
        if isinstance(sql, str):
            sql = text(sql)
        elif isinstance(sql, TextClause):
            pass
        else:
            raise f"Invalid sql object type: {type(sql)}. Only 'str' and 'TextClause' allowed"

        if dataframe:
            return pd.read_sql(sql, self.engine, params = params)
        else:
            with self.engine.connect() as connection:
                res = connection.execute(sql, params)
                connection.commit()
                return res
                

    def get_session(self):
        """
        Gets a session object on this connection

        Returns: sqlalchemy session

        """
        return self.smaker()

    def get_engine(self):
        return self.engine

    def dispose(self):
        """
        Disposes the engine
        """
        self.engine.dispose()

    def close(self):
        """
        Alias of self.dispose
        """
        return self.dispose()


    """
        Generic metadata helpers
    """
    def get_project_details(self, project_id: int = None, project_code: str = None):
        """
        Get details for a given project
        Args:
            project_id: project id
            project_code: project code, used when project_id = None

        Returns: (dict) project details

        """
        if project_id is not None:
            pj = self.execute('''SELECT * FROM public.ml_project WHERE project_id = :project_id''',
                              params=dict(project_id=project_id), dataframe=True)
        elif project_code is not None:
            pj = self.execute('''SELECT * FROM public.ml_project WHERE project_code = :project_code''',
                              params=dict(project_code=project_code), dataframe=True)
        else:
            raise ValueError('At least one between project_id and project_code must be set')

        if pj.shape[0] > 0:
            return pj.iloc[0].to_dict()
        return None


    def get_entity_system(self, entity_uid):
        entity = self.execute(f"""SELECT source_system_id FROM public.dim_entity_v WHERE entity_uid = :entity_uid""",
                              {'entity_uid': entity_uid}).fetchone()
        if entity is not None:
            return entity.source_system_id
        else:
            raise ValueError(f"Device not found: {entity_uid}")


    def get_device_timezone(self, device_uid):
        """
        Get a device (or plant) timezone
        Args:
            device_uid: the device to search for

        Returns: a string representing the device timezone, None if no timezone is available

        """
        tz = self.execute(f"""SELECT entity_timezone FROM public.dim_entity_v WHERE entity_uid = :device_uid """,
                          {'device_uid': device_uid}).fetchone()
        if tz is not None:
            return tz.entity_timezone
        else:
            raise ValueError(f"Device {device_uid} does not exist")
        
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
                    ds_device dv,
                    ds_model_variable dmv,
                    ds_variable_semantic dvs,
                    ds_semantic ds
                where
                    dmv.source_system_id = dv.source_system_id
                    and dmv.model_id = dv.model_id
                    and
                dvs.variable_id = dmv.model_variable_id
                    and ds.semantic_id = dvs.semantic_id
                    and device_uid = :device_uid""",
                         {'device_uid': device_uid}, dataframe = True)
 
