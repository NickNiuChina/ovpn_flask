import os
from carelds.common.logging.logutil import get_logger
from carelds.common.data.interface import DataInterface
from carelds.common.data.presto import PrestoInterface
from typing import List
from trino.exceptions import TrinoUserError
from sqlalchemy.exc import ProgrammingError



class TrinoInterface(PrestoInterface):

    def __init__(self,
                 user=os.environ.get('DS_TRINO_USER'),
                 hostname=os.environ.get('DS_TRINO_HOST'),
                 port=int(os.environ.get('DS_TRINO_PORT', 8080)),
                 db_catalog=None,
                 db_schema=None,
                 logger=get_logger('data_interface', stdout=True)):
        
        if user is None or hostname is None:
            raise RuntimeError("Cannot instantiate TrinoInterface since no user/hostname provided or not both of "
                               "DS_TRINO_USER and DS_TRINO_HOST are set")
        
        # Build the connection string
        if db_schema is not None and db_catalog is not None:
            DataInterface.__init__(self,
                                   connection_url=f"trino://{user}@{hostname}:{port}/{db_catalog}/{db_schema}",
                                   logger=logger)
        else:
            DataInterface.__init__(self,
                                   connection_url = f"trino://{user}@{hostname}:{port}/",
                                   logger = logger)
    
    
    def register_partition_metadata(self,
                                    table: str,
                                    schema: str,
                                    partitions: List[List[str]],
                                    location: str,
                                    analyze_columns: List[str] = None,
                                    db_catalog: str = 'hive') -> bool:
        """
        Call register_partition procedure
        Args:
            table: the table to work on
            schema: the schema the table belongs to
            partitions: partition list as [(p_name1, p_value1), (p_name2, p_value2), ...]
            location: partition physical location
            analyze_columns: list of columns to analyze, default None (do not analyze)
            db_catalog: the catalog to work with, by default is 'hive'

        Returns: True if everything went good, False otherwise

        """
        for p in partitions:
            if len(p) != 2:
                raise ValueError(str(p))

        p_names = ', '.join(f"'{p[0]}'" for p in partitions)
        p_values = ', '.join(f"'{p[1]}'" for p in partitions)

        try:
            try:
                self.execute(f"call system.register_partition('{schema}', '{table}', ARRAY[{p_names}], ARRAY[{p_values}], '{location}')", dataframe=False, db_catalog = 'hive')
            except ProgrammingError as e:
                if type(e.orig) == TrinoUserError:
                    raise e.orig
        except TrinoUserError as e:
            if e.error_name == 'ALREADY_EXISTS':
                self.logger.debug(f'The partition is already registered: {partitions}')
            else:
                self.logger.exception(f'Failed to register partition: {partitions}', fun=self.logger.warning)
                return False

        if analyze_columns is not None and len(analyze_columns) > 0:
            a_columnns = ', '.join(f"'{col}'" for col in analyze_columns)
            try:
                self.execute(f"ANALYZE hive.{schema}.{table} WITH (partitions = ARRAY[ARRAY[{p_values}]], columns=ARRAY[{a_columnns}])", db_catalog = 'hive')
            except:
                self.logger.exception(f'Failed to analyze partition: {partitions}', fun=self.logger.warning)
                return False

        return True


    def unregister_partition_metadata(self, table: str, schema: str, partitions: list):
        """
        Call unregister_partition procedure on the SQL engine, expect catalog "hive"
        Args:
            table: the table to work on
            schema: the schema the table belongs to
            partitions: partition list as [(p_name1, p_value1), (p_name2, p_value2), ...]

        Returns: statement result as returned by the SQL engine

        """
        for p in partitions:
            if len(p) != 2:
                raise ValueError(str(p))

        p_names = ', '.join(f"'{p[0]}'" for p in partitions)
        p_values = ', '.join(f"'{p[1]}'" for p in partitions)

        try:
            self.execute(f"call system.unregister_partition('{schema}', '{table}', ARRAY[{p_names}], ARRAY[{p_values}])", db_catalog = 'hive')
        except TrinoUserError as tue:
            if tue.args[0]['errorName'] == 'NOT_FOUND':
                self.logger.warning(f'Failed to unregister partition: {tue.args[0]["message"]}')
                return False
            else:
                self.logger.exception(f'Failed to unregister partition', fun = self.logger.warning)
                return False
            
        return True
    
    