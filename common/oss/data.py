import pyarrow as pa
import pyarrow.compute as pc
import pandas as pd
import os
import re
import pytz

from datetime import datetime, date, timedelta
from carelds.common.s3.connector import S3Connector


class S3Data:
    """
        Extract data directly from parquet files on S3 with optimized arrow procedures.
        Trino and other SQL engines are not used here, only a connection to S3 is required while the user must provide
        all the metadata needed for data extraction.
    """
    
    def __init__(self, s3_connection: S3Connector):
        self.s3_connection = s3_connection
    
    def _read_s3_to_tables(self,
                           objects: list,
                           source_system_id: int,
                           s3_bucket: str,
                           s3_bucket_analysis: str = None,
                           filters = None,
                           columns: list = ['model_id', 'model_variable_code', 'time_local', 'time_utc', 'value'],
                           coerce_timestamp_ms: bool = True):
        dfs = list()
        for obj in objects:
            tbl = self.s3_connection.read_parquet(s3_bucket if obj[0] == 'data' else (s3_bucket_analysis or s3_bucket),
                                                  obj[1]['Key'],
                                                  output = 'arrow',
                                                  filters = filters,
                                                  columns = columns)
            
            tbl = tbl.append_column('variable_id',
                                    pc.binary_join_element_wise(
                                        str(int(source_system_id)) if obj[0] == 'data' else '1000',
                                        pc.cast(tbl['model_id'], pa.string()),
                                        tbl['model_variable_code'],
                                        '_'))
            
            if coerce_timestamp_ms:
                for time_col in ['time_utc', 'time_local', 'time']:
                    if time_col in tbl.column_names:
                        if tbl.column(time_col).type == pa.timestamp('us'):
                            # cast 'us' timestamp to 'ms'
                            new_col = pa.array(tbl.column(time_col).to_pandas().dt.round('ms'), pa.timestamp('ms'))
                            tbl = tbl.drop_columns([time_col]) \
                                .append_column(time_col, new_col.cast(pa.timestamp('ms')))
                        elif tbl.column(time_col).type in (pa.int64(), pa.int32()):
                            # the time column is integer (when you read from tera and rmpro daily parquet)
                            time_field = pa.field(time_col, pa.timestamp('ms'))
                            time_data = pa.array([datetime.utcfromtimestamp(t) for t in tbl.column(time_col).to_numpy()], pa.timestamp('ms'))
                            tbl = tbl.drop_columns([time_col]) \
                                .append_column(time_field, time_data)
            dfs.append(tbl.select(columns + ['variable_id']))
        if len(dfs) > 0:
            return pa.concat_tables(dfs)
        return None
    
    def read_tsdb(self,
                  supervisor_uid: str,
                  time_from: datetime | date,
                  time_to: datetime | date,
                  device_uid: str = None,
                  device_id: int = None,
                  mod_var_codes: list = None,
                  read_analysis: bool = False,
                  s3_bucket: str = None,
                  s3_bucket_analysis: str = None,
                  device_columns: bool = None,
                  output: str = 'pandas') -> pd.DataFrame | pa.Table:
        """
        Read data from S3 parquets produced by Timescale DB extract procedures
        Args:
            supervisor_uid: supervisor unique id
            time_from: left time bound (inclusive)
            time_to: right time bound (exclusive)
            device_uid: device unique id
            device_id: device id (ignored if device_uid is not None)
            mod_var_codes: variables code to get, if None no filtering is applied
            read_analysis: read from analysis (analysis output). Assumes source system is 1.
            s3_bucket: the bucket to extract from, default is the DS_BUCKET_TSDB environment variable
            s3_bucket_analysis: the bucket to extract analysis from, default is the environment variable DS_BUCKET_1 (assumes source system is 1)
            device_columns: if True, also return device_id and device_uid columns. By default, device info are returned only when not filtering by device_id or device_uid.
            output: 'pandas' (default) to return a pandas DataFrame, 'arrow' to return a pyarrow Table

        Returns: a dataframe or pyarrow table containing the requested data

        """
        if output not in ('pandas', 'arrow'):
            raise ValueError(f"Invalid output parameter: {output}")
        if device_columns is None and device_id is None and device_uid is None:
            device_columns = True
        s3_bucket = s3_bucket or os.environ.get('DS_BUCKET_TSDB')
        s3_bucket_analysis = s3_bucket_analysis or os.environ.get('DS_BUCKET_1')
        if s3_bucket is None:
            raise RuntimeError(f"Could not determine TSDB s3 bucket name")
        if s3_bucket_analysis is None and read_analysis:
            raise RuntimeError(f"Could not determine analysis s3 bucket name")
        
        # days in the time interval
        days = set([date(d.year, d.month, d.day) for d in pd.date_range(time_from, time_to)])
        # month partitions to search
        months = set([date(d.year, d.month, 1) for d in pd.date_range(time_from, time_to)])
        # regex matcher for relevant parquet files
        obj_matcher = re.compile(".+/[0-9a-f]{40}_(" + "|".join([str(d).replace('-', r'\-') for d in days]) + ")\.parquet")
        
        # list parquet files
        objs = list()
        for month in months:
            prefix = f'data/supervisor={supervisor_uid}/month={month}/'
            objs.extend([('data', obj) for obj in self.s3_connection.list_objects(s3_bucket = s3_bucket, prefix = prefix) if obj_matcher.match(obj['Key']) is not None])
            if read_analysis:
                prefix = f'analysis_month_new/month={month}/device={device_uid}/'
                objs.extend([('analysis', obj) for obj in self.s3_connection.list_objects(s3_bucket = s3_bucket, prefix = prefix)])
        
        # build filters
        flt = (pc.field('time') >= time_from) & (pc.field('time') < time_to)
        if device_uid is not None:
            flt &= pc.field("device_uid") == device_uid
        if device_id is not None:
            flt &= pc.field("device_id") == device_id
        if mod_var_codes is not None:
            flt &= pc.field("model_variable_code").isin(mod_var_codes)
        
        table = self._read_s3_to_tables(objects = objs,
                                        source_system_id = 1,
                                        s3_bucket = s3_bucket,
                                        s3_bucket_analysis = s3_bucket_analysis,
                                        filters = flt,
                                        columns = ['model_id', 'model_variable_code', 'time', 'value']
                                        )
        
        if table is not None:
            if output == 'pandas':
                return table.to_pandas()
            return table
        
    def read_rmpro(self,
                   device_uid: str,
                   source_system_id: int,
                   time_from: datetime | date,
                   time_to: datetime | date,
                   time_column: str = 'time_local',
                   mod_var_codes: list = None,
                   read_data: bool = True,
                   read_analysis: bool = False,
                   s3_bucket: str = None,
                   read_daily_data: bool = False,
                   output: str = 'pandas') -> pd.DataFrame | pa.Table:
        """
            Read data from S3 parquets, legacy red/remotepro hive partitioning
            Args:
                device_uid: device unique id
                source_system_id: source system used to determine source bucket and variable ids
                time_from: left time bound (inclusive)
                time_to: right time bound (exclusive)
                time_column: the name of the column to use as time column, default 'time_local'
                mod_var_codes: variables code to get, if None no filtering is applied
                read_data: read from data path (extracted data)
                read_analysis: read from analysis path (analysis output)
                s3_bucket: override the auto-discovered s3 bucket
                read_daily_data: read from daily parquet instead of consolidated, defaults to False
                output: 'pandas' (default) to return a pandas DataFrame, 'arrow' to return a pyarrow Table
    
            Returns: a dataframe or pyarrow table containing the requested data
        """

        if output not in ('pandas', 'arrow'):
            raise ValueError(f"Invalid output parameter: {output}")
        days = pd.date_range(time_from, time_to)
        months = set([date(d.year, d.month, 1) for d in days])
        years = set([date(d.year, 1, 1) for d in months])
        s3_bucket = s3_bucket or os.environ[f'DS_BUCKET_{source_system_id}']

        if type(time_from) == date:
            time_from = datetime(time_from.year, time_from.month, time_from.day)
        if type(time_to) == date:
            time_to = datetime(time_to.year, time_to.month, time_to.day)
        
        # list parquet files
        objs = list()
        if read_daily_data:
            for day in days:
                if read_data:
                    prefix = f'data/dt={day.strftime("%Y-%m-%d")}/device={device_uid}'
                    objs.extend([('data', obj) for obj in self.s3_connection.list_objects(s3_bucket = s3_bucket, prefix = prefix)])
            flt = (pc.field(time_column) >= pytz.UTC.localize(time_from).timestamp()) \
                    & (pc.field(time_column) < pytz.UTC.localize(time_to).timestamp())
        else:
            for year in years:
                if read_data:
                    prefix = f'data_merged/{device_uid[0]}/by_year/year={year.year}/device={device_uid}/'
                    objs.extend([('data', obj) for obj in self.s3_connection.list_objects(s3_bucket = s3_bucket, prefix = prefix)])
            for month in months:
                if read_data:
                    prefix = f'data_merged/{device_uid[0]}/by_month/month={month}/device={device_uid}/'
                    objs.extend([('data', obj) for obj in self.s3_connection.list_objects(s3_bucket = s3_bucket, prefix = prefix)])
                if read_analysis:
                    prefix = f'analysis_month_new/month={month}/device={device_uid}/'
                    objs.extend([('analysis', obj) for obj in self.s3_connection.list_objects(s3_bucket = s3_bucket, prefix = prefix)])
        
            flt = (pc.field(time_column) >= time_from) & (pc.field(time_column) < time_to)
        
        if mod_var_codes is not None:
            flt &= pc.field("model_variable_code").isin(mod_var_codes)
            
        table = self._read_s3_to_tables(objects = objs,
                                        source_system_id = source_system_id,
                                        s3_bucket = s3_bucket,
                                        filters = flt,
                                        columns = ['model_id', 'model_variable_code', 'time_local', 'value']
                                        )
        
        if table is not None:
            if output == 'pandas':
                return table.to_pandas()
            return table
    
    
    def read_tera(self,
                  device_uid: str,
                  source_system_id: int,
                  time_from: datetime | date,
                  time_to: datetime | date,
                  time_column: str = 'time_local',
                  mod_var_codes: list = None,
                  read_data: bool = True,
                  read_analysis: bool = False,
                  s3_bucket: str = None,
                  output: str = 'pandas'
                  ):
        """
            Read data from S3 parquets, Tera hive partitioning
            Args:
                device_uid: device unique id
                source_system_id: source system used to determine source bucket and variable ids
                time_from: left time bound (inclusive)
                time_to: right time bound (exclusive)
                time_column: the name of the column to use as time column, default 'time_local'
                mod_var_codes: variables code to get, if None no filtering is applied
                read_data: read from data path (extracted data)
                read_analysis: read from analysis path (analysis output)
                s3_bucket: override the auto-discovered s3 bucket
                output: 'pandas' (default) to return a pandas DataFrame, 'arrow' to return a pyarrow Table
    
            Returns: a dataframe or pyarrow table containing the requested data
        """
        if output not in ('pandas', 'arrow'):
            raise ValueError(f"Invalid output parameter: {output}")
            
        if time_column == 'time_local':
            if isinstance(time_from, datetime):
                _time_from = (datetime(time_from.year, time_from.month, time_from.day, time_from.hour) - timedelta(hours = 12))\
                    .replace(hour = 0, minute = 0, second = 0, microsecond = 0, tzinfo = None)
            else:
                _time_from = (datetime(time_from.year, time_from.month, time_from.day) - timedelta(hours = 12))\
                    .replace(hour = 0, minute = 0, second = 0, microsecond = 0, tzinfo = None)
            if isinstance(time_to, datetime):
                _time_to = (datetime(time_to.year, time_to.month, time_to.day, time_to.hour) + timedelta(hours = 13))\
                    .replace(hour = 0, minute = 0, second = 0, microsecond = 0, tzinfo = None)
            else:
                _time_to = (datetime(time_to.year, time_to.month, time_to.day) + timedelta(hours = 13))\
                    .replace(hour = 0, minute = 0, second = 0, microsecond = 0, tzinfo = None)
        else:
            _time_from = datetime(time_from.year, time_from.month, time_from.day).replace(hour = 0, minute = 0, second = 0, microsecond = 0, tzinfo = None)
            _time_to = datetime(time_to.year, time_to.month, time_to.day).replace(hour = 0, minute = 0, second = 0, microsecond = 0, tzinfo = None)
        
        months = set([date(d.year, d.month, 1) for d in pd.date_range(_time_from, _time_to)])
        s3_bucket = s3_bucket or os.environ[f'DS_BUCKET_{source_system_id}']
        
        # list parquet files
        objs = list()
        for month in months:
            if read_data:
                objs.extend([('data', obj) for obj in self.s3_connection.list_objects(s3_bucket = s3_bucket,
                                                    prefix = f'data_month_new/month={month}/device={device_uid}/')])
            if read_analysis:
                objs.extend([('analysis', obj) for obj in self.s3_connection.list_objects(s3_bucket = s3_bucket,
                                                    prefix = f'analysis_month_new/month={month}/device={device_uid}/')])
        
        # build filters
        flt = (pc.field(time_column) >= time_from) & (pc.field(time_column) < time_to)
        if mod_var_codes is not None:
            flt &= pc.field("model_variable_code").isin(mod_var_codes)
        
        table = self._read_s3_to_tables(objects = objs,
                                        source_system_id = source_system_id,
                                        s3_bucket = s3_bucket,
                                        filters = flt,
                                        columns = ['model_id', 'model_variable_code', 'time_local', 'time_utc', 'value']
                                        )
        
        if table is not None:
            if output == 'pandas':
                return table.to_pandas()
            return table
        
        
        
    def read_tera_chunked(self,
                          device_uid: str,
                          source_system_id: int,
                          time_from: datetime | date,
                          time_to: datetime | date,
                          time_column: str = 'time_local',
                          mod_var_codes: list = None,
                          read_data: bool = True,
                          read_analysis: bool = False,
                          s3_bucket: str = None,
                          output: str = 'pandas',
                          column_chunk_size: int = None
                          ):
        """
            Read data from S3 parquets,Tera hive partitioning. Works as generator.
            Args:
                device_uid: device unique id
                source_system_id: source system used to determine source bucket and variable ids
                time_from: left time bound (inclusive)
                time_to: right time bound (exclusive)
                time_column: the name of the column to use as time column, default 'time_local'
                mod_var_codes: variables code to get, if None no filtering is applied
                read_data: read from data path (extracted data)
                read_analysis: read from analysis path (analysis output)
                s3_bucket: override the auto-discovered s3 bucket
                output: 'pandas' (default) to return a pandas DataFrame, 'arrow' to return a pyarrow Table
                column_chunk_size: let the function yield this maximum amount of columns per time, requires `mod_var_codes`
    
            Yields: dataframes or pyarrow table containing the requested data
        """
        
        if mod_var_codes is None:
            raise ValueError("mod_var_codes must be specified")
        
        if column_chunk_size is None:
            raise ValueError("chunk_size must be specified")
 
        chunk = 0
        while (chunk * column_chunk_size) < len(mod_var_codes):
            mod_var_subset = mod_var_codes[chunk * column_chunk_size:(chunk + 1) * column_chunk_size]
            yield (mod_var_subset, self.read_tera(
                device_uid = device_uid,
                source_system_id = source_system_id,
                time_from = time_from,
                time_to = time_to,
                time_column = time_column,
                mod_var_codes = mod_var_subset,
                read_data = read_data,
                read_analysis = read_analysis,
                s3_bucket = s3_bucket,
                output = output
            ))
            chunk += 1
