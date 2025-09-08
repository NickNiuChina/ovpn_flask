import os
import pandas as pd
import numpy as np
from typing import List
from datetime import datetime, timedelta, date
from carelds.common.logging.logutil import get_logger
from carelds.common.data.interface import DataInterface
from sqlalchemy.exc import DatabaseError
from time import time


class PrestoInterface(DataInterface):

    def __init__(self,
                 user=os.environ.get('DS_PRESTO_USER'),
                 hostname=os.environ.get('DS_PRESTO_HOST'),
                 port=int(os.environ.get('DS_PRESTO_PORT', 8080)),
                 db_catalog=None,
                 db_schema=None,
                 logger=get_logger('presto_interface', stdout=True)):

        DataInterface.__init__(self,
            connection_url=f"presto://{user}@{hostname}:{port}",
            logger=logger)


    
    def read_device_raw(self, time_from, time_to, device_uid, analysis=False, time_column=None, variables=None, dataframe=True):
        """
        Args:
            time_from: search data from this time onward (inclusive)
            time_to: search data up to this time (exclusive)
            device_uid: device to search
            analysis: if True, include analysis outputs
            time_column: the time column to use: 'time_local', 'time_utc'. Default None to let the function decide (utc for Tera, local for RemotePRO)
            variables: filter rows by variable_id, an iterable of strings is expected, default None (do not filter)
            dataframe: True (default) to return pandas DataFrame

        Returns:
            a pandas DataFrame with the retrieved data

        """
        if time_column not in ('time_local', 'time_utc', None):
            raise ValueError('Explicit time column must be one between "time_local" and "time_utc"')

        d = time_from
        years, months = set(), set()
        while d < time_to:
            years.add(d.year)
            months.add(date(d.year, d.month, 1))
            d += timedelta(days=1)

        query = f"""
            SELECT 
                model_id, variable_id, "value", time_utc, time_local
            FROM 
                data.data_all_v
            WHERE 
                device = '{device_uid}'
                and {time_column} >= timestamp '{time_from}'
                and {time_column} < timestamp '{time_to}'
                and year in ({', '.join((str(y) for y in years))})
                and month in ({', '.join("date '" + str(m) + "'" for m in months)})
                {'and not analysis' if not analysis else ''}
                {f'''and variable_id in ({','.join([f"'{v}'" for v in set(variables)])})''' if variables else ""}
            ORDER BY
                {time_column}    
        """
        return self.execute(query, db_catalog = 'hive', dataframe = dataframe)


    def sync_partition_metadata(self, table, schema, method='FULL', catalog='hive'):
        """
        Call syncing procedure on the query engine, expect catalog "hive"
        Args:
            table: the table to sync
            schema: the schema the table belongs to
            method: how to sync, default 'FULL'
            catalog: the catalog, default 'hive'

        Returns:

        """
        if catalog != 'hive':
            raise NotImplementedError(f"Can only sync catalog 'hive'")
        sync_result = self.execute(f"call system.sync_partition_metadata('{schema}', '{table}', '{method}')", dataframe=False, db_catalog = 'hive').fetchone().result
        if sync_result:
            self.logger.debug(f'Syncing physical dataset {catalog}.{schema}.{table}')
        else:
            self.logger.error(f'Failed to Sync physical dataset {catalog}.{schema}.{table}')
        return sync_result


    def register_partition_metadata(self, table: str, schema: str, partitions: List[List[str]], location: str,
                                    analyze_columns: List[str] = None) -> bool:
        """
        Call register_partition procedure, expect catalog "hive"
        Args:
            table: the table to work on
            schema: the schema the table belongs to
            partitions: partition list as [(p_name1, p_value1), (p_name2, p_value2), ...]
            location: partition physical location
            analyze_columns: list of columns to analyze, default None (do not analyze)

        Returns: True if everything went good, False otherwise

        """
        for p in partitions:
            if len(p) != 2:
                raise ValueError(str(p))

        p_names = ', '.join(f"'{p[0]}'" for p in partitions)
        p_values = ', '.join(f"'{p[1]}'" for p in partitions)

        try:
            sync_result = self.execute(f"call system.register_partition('{schema}', '{table}', ARRAY[{p_names}], ARRAY[{p_values}], '{location}')", dataframe=False, db_catalog = 'hive').fetchone().result
        except DatabaseError as de:
            if 'is already registered' not in de.args[0]:
                self.logger.exception('Failed to register partition', fun = self.logger.warning)
                return False
            sync_result = True

        if analyze_columns is not None and len(analyze_columns) > 0:
            a_columnns = ', '.join(f"'{col}'" for col in analyze_columns)
            try:
                self.execute(f"ANALYZE {self.db_catalog}.{schema}.{table} WITH (partitions = ARRAY[ARRAY[{p_values}]], columns=ARRAY[{a_columnns}])", db_catalog = 'hive')
            except:
                self.logger.exception('Failed to analyze partition', fun=self.logger.warning)
                return False

        return sync_result


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
            engine = self.get_engine()
            sync_result = engine.execute(f"call system.unregister_partition('{schema}', '{table}', ARRAY[{p_names}], ARRAY[{p_values}])", db_catalog = 'hive').fetchone().result
        except DatabaseError as de:
            if 'does not exist' in de.args[0]:
                return True
            raise
        return sync_result


    @classmethod
    def _build_pivot_binary_transition_query(cls, device_uid, time_to, time_from, pivot_column, value_column,
                                             time_column, table, interval, aggregation, domain):
        """
        Returns a SQL code that produces a pivot table that counts the binary transitions over a semantic.
        Args:
            device_uid: device to pivot
            time_to: right time bound
            time_from: left time bound
            pivot_column: column that contains the categories to rewrite as columns
            value_column: column that contains the values
            time_column: time column to use as index
            table: hive table to perform pivot on
            interval: time interval for resampling, accepted values: 5, 10, 15, 20, 30
            aggregation: aggregation definition: (category/semantic:str, aggregation:str, alias:str)

        Returns: (str) subquery.

        """
        # build time interval
        assert time_column in ('time_utc', 'time_local')
        assert aggregation[1] in ('trans01', 'trans10')
        interval = int(interval) if interval is not None else None
        # limit month partitions
        months = ((time_from - timedelta(days=1)).replace(day=1).date(), (time_to + timedelta(days=1)).replace(day=1).date())

        # Time aggregation
        if interval in (5, 10, 15, 20, 30, 60):
            time_agg = f"""date_add('minute', {interval}*(minute({time_column})/{interval}), date_trunc('hour', {time_column}))"""
        elif interval is None:
            time_agg = f"""{time_column}"""
        elif interval in (60 * 2, 60 * 3, 60 * 4, 60 * 6, 60 * 8, 60 * 12, 60 * 24):
            time_agg = f"""date_add('hour', {round(interval / 60)}*(hour({time_column})/{round(interval / 60)}), date_trunc('day', {time_column}))"""
        else:
            raise ValueError(f"Invalid or not yet supported interval: {interval}")

        return f"""SELECT 
                {time_agg} {time_column},
                sum(delta_lag_1) v
            FROM (
                select {time_column}, case when (value-lag({value_column}, 1) over (order by {time_column}) {'>' if aggregation[1] == 'trans01' else '<'} 0 ) then 1 else 0 end delta_lag_1
                FROM {table} t
                where
                    t.device = '{device_uid}'
                    and domain_id = '{domain}'
                    and {pivot_column} = '{aggregation[0]}'
                    and {time_column} between timestamp '{(time_from - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")}' and timestamp '{(time_to + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")}'
                    and month >= timestamp '{(time_from - timedelta(hours=12)).replace(day=1).date()}' and month <= timestamp '{(time_to + timedelta(hours=12)).replace(day=1).date()}')
            GROUP BY {time_agg}
            ORDER BY 1"""


    @classmethod
    def _build_pivot_query(cls, device_uid: str, time_to: datetime, time_from: datetime, pivot_column: str,
                           value_column: str,
                           time_column: str, table: str, interval: int, aggregations: list, domain: str):
        """
        Build pivot table from device semantics
        Args:
            pivot_column: column that contains the categories to rewrite as columns
            value_column: column that contains the values
            time_column: time column to use as index
            table: hive table to perform pivot on
            interval: time interval for resampling, accepted values: 5, 10, 15, 20, 30
            aggregations: list of aggregation definition: [(category/semantic:str, aggregation:str, alias:str), ...]
            domain: semantic domain (default: 'default')

        Returns: (pre_sqls, data_sql, post_sql) three lists of query to execute

        """
        # build time interval
        assert time_column in ('time_utc', 'time_local')
        alternative_time_column = 'time_utc' if time_column == 'time_local' else 'time_local'
        interval = int(interval) if interval is not None else None
        if isinstance(time_to, date):
            time_to = datetime(time_to.year, time_to.month, time_to.day)
        if isinstance(time_from, date):
            time_from = datetime(time_from.year, time_from.month, time_from.day)
        # final query sequence to execute
        queries = list()

        # Time aggregation
        if interval in (5, 10, 15, 20, 30, 60):
            time_agg = f"""date_add('minute', {interval}*(minute({time_column})/{interval}), date_trunc('hour', {time_column}))"""
        elif interval is None:
            time_agg = f"""{time_column}"""
        elif interval in (60 * 2, 60 * 3, 60 * 4, 60 * 6, 60 * 8, 60 * 12, 60 * 24):
            time_agg = f"""date_add('hour', {round(interval / 60)}*(hour({time_column})/{round(interval / 60)}), date_trunc('day', {time_column}))"""
        else:
            raise ValueError(f"Invalid or not supported interval: {interval}")

        # build column definitions
        agg_columns = list()
        agg_columns.append('min_by({at}, {t}) "{at}"'.format(t=time_column, at=alternative_time_column))
        join_tables = list()
        for agg in aggregations:
            if agg[1] in (
                'mean', 'min', 'max', 'sum', 'nanmean', 'nanmin', 'nanmax', 'nansum', 'first', 'last', 'nanfirst',
                    'nanlast', 'nandiff', 'diff'):
                fun = 'avg({v}) FILTER (WHERE {c} = \'{cv}\') "{a}"' if agg[1] == 'mean' \
                    else 'min({v}) FILTER (WHERE {c} = \'{cv}\') "{a}"' if agg[1] == 'min' \
                    else 'max({v}) FILTER (WHERE {c} = \'{cv}\') "{a}"' if agg[1] == 'max' \
                    else 'sum({v}) FILTER (WHERE {c} = \'{cv}\') "{a}"' if agg[1] == 'sum' \
                    else 'avg({v}) FILTER (WHERE {c} = \'{cv}\' AND NOT is_nan({v})) "{a}"' if agg[1] == 'nanmean' \
                    else 'min({v}) FILTER (WHERE {c} = \'{cv}\' AND NOT is_nan({v})) "{a}"' if agg[1] == 'nanmin' \
                    else 'max({v}) FILTER (WHERE {c} = \'{cv}\' AND NOT is_nan({v})) "{a}"' if agg[1] == 'nanmax' \
                    else 'sum({v}) FILTER (WHERE {c} = \'{cv}\' AND NOT is_nan({v})) "{a}"' if agg[1] == 'nansum' \
                    else 'min_by({v}, {t}) FILTER (WHERE {c} = \'{cv}\') "{a}"' if agg[1] in ('first', 'diff') \
                    else 'max_by({v}, {t}) FILTER (WHERE {c} = \'{cv}\') "{a}"' if agg[1] == 'last' \
                    else 'min_by({v}, {t}) FILTER (WHERE {c} = \'{cv}\' AND NOT is_nan({v})) "{a}"' if agg[1] in ('nanfirst', 'nandiff') \
                    else 'max_by({v}, {t}) FILTER (WHERE {c} = \'{cv}\' AND NOT is_nan({v})) "{a}"' if agg[1] == 'nanlast' \
                    else None
                if fun is not None:
                    agg_columns.append(
                        fun.format(c=pivot_column, v=value_column, t=time_column, cv=agg[0], a=agg[2] or agg[0]))
            elif agg[1] in ('trans01', 'trans10'):
                join_tables.append((cls._build_pivot_binary_transition_query(device_uid, time_to, time_from,
                                                                             pivot_column, value_column, time_column,
                                                                             table, interval, agg, domain),
                                    agg[2] or agg[0]))

        # "pv0" is the inner query that aggregates the values
        pv0_sql = f"""SELECT {time_agg} {time_column},\n\t""" + ',\n\t'.join(agg_columns)
        pv0_sql += f"""\nFROM\n\t{table}\n"""
        pv0_sql += f"""WHERE
                device='{device_uid}'
                and domain_id = '{domain}'
                and {time_column} between timestamp '{(time_from - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")}' and timestamp '{(time_to + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")}'
                and month >= timestamp '{(time_from - timedelta(hours=12)).replace(day=1).date()}' and month <= timestamp '{(time_to + timedelta(hours=12)).replace(day=1).date()}'
            group by {time_agg}
            """

        # build outer query
        diff_columns = list()  # diff columns to build from inner query aggregations
        for agg in aggregations:
            if agg[1] in ('nandiff', 'diff'):
                diff_columns.extend([f"""lead(pv0."{agg[2] or agg[0]}") over (order by pv0.{time_column}) - pv0."{agg[2] or agg[0]}" "{agg[2] or agg[0]}" """])
        aggr_columns = [f'"{agg[2] or agg[0]}"' for agg in aggregations if agg[1] not in ('diff', 'nandiff', 'trans01', 'trans10')]  # exclude diff temporary columns from inner query


        if len(join_tables) > 0:
            query = "SELECT " + ', '.join(['pv0.time_utc', 'pv0.time_local'] + aggr_columns + diff_columns + [f"pv{t + 1}.v as {table[1]}" for t, table in enumerate(join_tables)]) + f" FROM (\n{pv0_sql}) pv0"
            for t, table in enumerate(join_tables):
                query += f" FULL OUTER JOIN ({table[0]}) pv{t + 1} ON (pv0.{time_column}=pv{t + 1}.{time_column}) "
        else:
            query = f"""SELECT {', '.join(['time_utc', 'time_local'] + aggr_columns + diff_columns)} FROM (\n{pv0_sql}) pv0 """
        query += f"""WHERE pv0.{time_column} >= timestamp '{time_from.strftime("%Y-%m-%d %H:%M:%S")}' and pv0.{time_column} < timestamp '{time_to.strftime("%Y-%m-%d %H:%M:%S")}'\nORDER BY pv0.{time_column} """

        # Build query list
        return [], query, []


    def pivot_data(self, device_uid, time_to, time_from, interval, aggregations,
                   time_column='time_local', table='hive.data.data_sem_v', domain='default', logger = None):
        pivot_column = 'semantic_sd'
        value_column = 'value'
        dfp = None
        pre_sqls, data_sql, post_sqls = self._build_pivot_query(device_uid, time_to, time_from, pivot_column,
                                                                value_column, time_column, table, interval,
                                                                aggregations, domain)
        for sql in pre_sqls:
            self.execute(sql, db_catalog = 'hive')
            time.sleep(1)  # Wait for pre_sqls to complete
        dfp = self.execute(data_sql, dataframe=True, db_catalog = 'hive')
        for sql in post_sqls:
            self.execute(sql, db_catalog = 'hive')

        for column in dfp.columns:
            if column in ('time_local', 'time_utc'):
                if not pd.api.types.is_datetime64_dtype(dfp[column]):
                    dfp[column] = dfp[column].astype('datetime64[s]')
            else:
                if dfp[column].dtype != np.float64:
                    dfp[column] = dfp[column].fillna(np.nan).astype(np.float64)
        return dfp
    
    