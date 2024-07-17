from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytz

from carelds.common.logging.logutil import get_logger
# from memory_profiler import profile

DENSIFY = ('min', 'max', 'nanmin', 'nanmax', 'mean', 'nanmean', 'first', 'last', 'nanfirst', 'nanlast', 'diff', 'nandiff')
NO_DENSIFY = ('count', 'sum', 'nansum', 'change', 'trans01', 'trans10')

# @profile
def pivot_densify(data: pd.DataFrame,
                  time_min: datetime,
                  time_max: datetime,
                  fill: bool = True,
                  fill_limit: int = None,
                  variables: list = None,
                  density: int | None = 5,
                  time_index_column: str ='_time',
                  values_column: str = 'value',
                  variable_column: str = 'variable_id') -> pd.DataFrame:
    """
    Pivot and densify dataframe.
    The variable column (pivot's columns) is expected to be named "variable_id"
    The value column (pivot's values) is expected to be named "value"

    Args:
        data: the dataframe to densify
        variables: the variable_id(s) not listed are not processed and dropped
        time_min: lower time bound for densification
        time_max: higher time bound for densification
        fill: fill the data after densification, default True
        fill_limit: limit of values to fill. The suggested value matches the resampling interval divided by the densify interval. If None (default) no limit is applied
        density: time density in seconds, if None or np.Nan then densification won't be applied and pivoted data is returned as is
        time_index_column: the name of the time column to use as index for pivoting, default is '_time'
        values_column: the name of the column that contains the values, default is 'value'
        variable_column: the name of the column that contains the variable names, default is 'variable_id'

    Returns: a new densified and pivoted dataframe with a column for each variable

    """
    if pd.isna(time_min) or pd.isna(time_max):
        raise ValueError('Time boundaries for densification are invalid')
    nan_placeholder = -97519.192 # a value that (hopefully) never appears in real data
    
    # Perform pivot
    if density is None or pd.isna(density):
        # Do not densify
        if variables is not None:
            return pd.pivot_table(data[data.variable_id.isin(variables)],
                                        index = time_index_column, values = values_column, columns = variable_column)
        else:
            return pd.pivot_table(data, index = time_index_column, values = values_column, columns = variable_column)
    else:
        # Densify and replace NaN with a placeholder to avoid the forward fill of NaN values that should remain NaN
        if variables is not None:
            df_pivoted = pd.pivot_table(data[data[variable_column].isin(variables)].fillna(nan_placeholder),
                                        index = time_index_column, values = values_column, columns = variable_column)
        else:
            df_pivoted = pd.pivot_table(data.fillna(nan_placeholder),
                                        index = time_index_column, values = values_column, columns = variable_column)
    
    # Build densified index
    df_idx = pd.DataFrame({'time': np.arange(time_min,
                                             time_max + timedelta(seconds = int(density)),
                                             timedelta(seconds = int(density)))}).set_index('time')
    
    # # Merge pivoted data with index with 'outer' logic
    # df_merged = pd.merge(df_idx, df_pivoted, how = 'outer', left_index = True, right_index = True)
    # df_merged.sort_index(inplace = True)
    # # Forward fill to populate data on dense index
    # print(f"fill: {fill}, fill_limit: {fill_limit} ({fill_limit*density}s)")
    # if fill:
    #     if fill_limit is not None and fill_limit > 0:
    #         df_merged.ffill(inplace = True, limit = fill_limit)
    #     else:
    #         df_merged.ffill(inplace = True)
    # print(df_merged.loc[df_merged.index > datetime(2024,5,13,9), :].reset_index(drop = False).iloc[:50])
    
    df_merged = None
    for column in df_pivoted.columns:
        # merge with index and ffill one variable (column) at time
        df_merged_col = pd.merge(df_idx, df_pivoted[[column]].dropna(), how = 'outer', left_index = True, right_index = True, sort = True)
        if fill:
            if fill_limit is not None and fill_limit > 0:
                df_merged_col.ffill(inplace = True, limit = fill_limit)
            else:
                df_merged_col.ffill(inplace = True)
        if df_merged is None:
            df_merged = df_merged_col
        else:
            df_merged = pd.merge(df_merged, df_merged_col, how = 'outer', left_index = True, right_index = True)
    
    # Keep index not greater than the maximum data timestamp
    df_idx = df_idx.loc[df_idx.index <= df_pivoted.index.max()]
    # Merge again with 'inner' logic to keep index only
    df_merged = pd.merge(df_idx, df_merged, how = 'inner', left_index = True, right_index = True)
    # Drop all-NaN rows introduced by merging with index (rows before the first valid data timestamp)
    df_merged.dropna(inplace = True, how = 'all', axis = 'index')
    
    # Replace back real data NaNs
    df_merged.replace(nan_placeholder, np.nan, inplace = True)
    
    return df_merged


def aggregation_functions(name: str):
    """
    Return the aggregation function that matches the provided name
    
    Args:
        name: function name

    Returns: callable aggregation function

    """
    
    def min(v):
        return np.min(v.values) if v.values.shape[0] > 0 else np.nan
    
    def max(v):
        return np.max(v.values) if v.values.shape[0] > 0 else np.nan
    
    def mean(v):
        return np.mean(v.values) if v.values.shape[0] > 0 else np.nan
    
    def sum(v):
        return np.sum(v.values) if v.values.shape[0] > 0 else np.nan
    
    if name == 'min':
        return min
    
    if name == 'max':
        return max
    
    if name == 'sum':
        return sum
    
    if name == 'mean':
        return mean
    
    def nanmin(v):
        return np.nanmin(v.values) if v.values.shape[0] > 0 else np.nan
    
    if name == 'nanmin':
        return nanmin
    
    def nanmax(v):
        return np.nanmax(v.values) if v.values.shape[0] > 0 else np.nan
    
    if name == 'nanmax':
        return nanmax
    
    def nansum(v):
        return np.nansum(v.values) if v.values.shape[0] > 0 else np.nan
    
    if name == 'nansum':
        return nansum
    
    def nanmean(v):
        return np.nanmean(v.values) if v.values.shape[0] > 0 else np.nan
    
    if name == 'nanmean':
        return nanmean
        
    def first(v):
        v = v.values
        return v[0] if v.shape[0] > 0 else np.NaN
    
    if name == 'first':
        return first
    
    def last(v):
        v = v.values
        return v[-1] if v.shape[0] > 0 else np.NaN
    
    if name == 'last':
        return last
    
    def nanfirst(v):
        v = v.values
        return v[~np.isnan(v)][0] if np.count_nonzero(~np.isnan(v)) > 0 else np.NaN
    
    if name == 'nanfirst':
        return nanfirst
    
    def nanlast(v):
        v = v.values
        return v[~np.isnan(v)][-1] if np.count_nonzero(~np.isnan(v)) > 0 else np.NaN
    
    if name == 'nanlast':
        return nanlast
    
    def diff(v):
        v = v.values
        return v[0] if v.shape[0] > 0 else np.NaN
    
    if name == 'diff':
        return diff
    
    def nandiff(v):
        v = v.values
        return v[~np.isnan(v)][0] if np.count_nonzero(~np.isnan(v)) > 0 else np.NaN
    
    if name == 'nandiff':
        return nandiff
    
    def trans01(v):
        v = v.values
        return np.nansum(v)
    
    if name == 'trans01':
        # Transition from logic value 0 (<=0) to 1 (>0)
        # Requires pre-processing, then it sums the transition events
        return trans01
    
    def trans10(v):
        v = v.values
        return np.nansum(v)
    
    if name == 'trans10':
        # Transition from logic value 1 (>0) to 0 (<=0)
        # Requires pre-processing, then it sums the transition events
        return trans10
    
    raise ValueError(f"Invalid aggregation function name '{name}'")


# @profile
def resample_aggregate(df_data: pd.DataFrame,
                       resampling_interval: int,
                       actual_columns: list,
                       logger = get_logger('pivot_procedures')) -> pd.DataFrame:
    """
    Apply resampling and column rename
    
    Args:
        df_data: pivoted dataframe
        resampling_interval: resampling interval in minutes
        actual_columns: columns to resample. List of dict objects specifying "variable_id", "semantic_rename" and "semantic_aggregation"
        logger: logger object

    Returns: the resampled dataframe

    """
    logger.debug(f"Resampling and aggregate data at {resampling_interval}m")
    # retrieve resampling function(s) for each input column
    resampling_function = dict()
    for r in actual_columns:
        # {variable_id1 => [("output_colname1", "aggregation1"), ("output_colname2", "aggregation2"), ...], variable_id2 => [...], ...}
        resampling_function.setdefault(r['variable_id'], list()).append((r['semantic_rename'], r['semantic_aggregation']))
    # resample the densified dataframe and apply the resampling functions
    df_partial_output = df_data[list(set([column['variable_id'] for column in actual_columns]))]. \
        resample(f"{resampling_interval}min", closed = 'left', label = 'left'). \
        apply({c: [aggregation_functions(f[1]) for f in resampling_function[c]] for c in resampling_function}, raw=True)
    # build column rename mapping
    column_rename = dict()
    for col in resampling_function:
        for rf in resampling_function[col]:  # col[1]:
            column_rename[(col, rf[1])] = rf[0]
            logger.debug(f"Rename column ({col}, {rf[1]}) => {rf[0]}")
    # flatten multi-index and apply rename
    df_partial_output.columns = df_partial_output.columns.to_flat_index()
    df_partial_output.rename(columns = column_rename, inplace = True)
    return df_partial_output



def notify_missing_columns(missing_columns, logger):
    """
        Log missing columns
    """
    if len([column for column in missing_columns if column['variable_id'] is not None]) > 0:
        # Some variable id are mapped but no data for them was found
        logger.warning(f'Data for these variable_id is missing and some pivot column will not be available (var_id -> out_column):')
        for column in missing_columns:
            if column['variable_id'] is not None:
                logger.warning(f"\t{column['variable_id']} -> {column['semantic_rename']}")
    
    if len([column for column in missing_columns if column['variable_id'] is None]) > 0:
        # Some semantics are not assigned to any variable id in this device model
        logger.warning(f'The following pivot columns cannot be processed since the model does not map the source semantics (semantic -> out_column):')
        for column in missing_columns:
            if column['variable_id'] is None:
                logger.warning(f"\t{column['semantic_id']} -> {column['semantic_rename']}")


# @profile
def perform_pivot(df_data: pd.DataFrame,
                  df_pivot_columns: pd.DataFrame,
                  time_min: datetime = None,
                  time_max: datetime = None,
                  time_column = 'time',
                  values_column: str = 'value',
                  variable_column: str = 'variable_id',
                  dense_interval: int = 5,
                  missing_columns_as_nan: bool = False,
                  convert_time_columns: dict | None = None,
                  densification_fill_sec: int = 900,
                  logger = get_logger('pivot_procedures')) -> pd.DataFrame:
    """
    Perform pivot, resampling and aggregation
    
    Args:
        df_data: the data dataframe as retrieved from the source parquet files
        df_pivot_columns: dataframe containing pivot column definitions as in datascience master data
        time_min: left bound for time index when densifying, default is the lowest 'time' value found
        time_max: right bound for time index when densifying, default is the highest 'time' value found
        time_column: the name of the time column to use as index for pivoting, default is 'time'
        values_column: the name of the column that contains the values (in `df_data`), default is 'value'
        variable_column: the name of the column that contains the variable names (in `df_data`), default is 'variable_id'
        dense_interval: densification interval in seconds, default 5
        missing_columns_as_nan: if True, add missing output columns as null columns
        convert_time_columns: derive other time columns from the index column. Must be in the form `{'other_time_column': ['tz1', 'tz2']}`:
            a new column named 'other_time_column' will be created localizing the index in timezone 'tz1' and converting to 'tz2'
        densification_fill_sec: how many seconds to forward fill missing values in densified data, default 900 (15m)
        logger: logger object

    Returns: the final pivoted and aggregated dataframe

    """
    time_index_col = '_time'
    if df_data.shape[0] < 1:
        logger.warning('Trying to perform pivot on an empty dataframe')
        df_output = pd.DataFrame()
        df_output[time_index_col] = pd.Series().astype('datetime64[us]')
        return df_output.set_index(time_index_col)
    # copy time column
    df_data[time_index_col] = df_data[time_column]
    # columns that require densification prior to aggregation
    df_filled_cols = df_pivot_columns.loc[df_pivot_columns.semantic_aggregation.isin(DENSIFY) & ~pd.isna(df_pivot_columns.semantic_resampling_rate)]
    # columns that must be aggregated without prior densification
    df_unfilled_cols = df_pivot_columns.loc[df_pivot_columns.semantic_aggregation.isin(NO_DENSIFY) & ~pd.isna(df_pivot_columns.semantic_resampling_rate)]
    # columns that must not be aggregated at all
    df_noagg_cols = df_pivot_columns.loc[pd.isna(df_pivot_columns.semantic_resampling_rate)]
    
    # output dataframe
    df_output = None
    
    # Pivot and aggregate columns that require filling
    if df_filled_cols.shape[0] > 0:
        for resampling_interval in df_filled_cols.semantic_resampling_rate.unique():
            # for each aggregation interval
            logger.debug(f"Resampling interval: {resampling_interval}")
            
            # pivot columns that uses this aggregation interval
            pivot_columns = df_filled_cols[df_filled_cols.semantic_resampling_rate == resampling_interval].to_dict(orient = 'records')

            # Densify
            fill_limit = int(densification_fill_sec // dense_interval) if dense_interval is not None and dense_interval > 0 else None
            df_densified = pivot_densify(data = df_data,
                                         time_min = time_min or df_data[time_column].min(),
                                         time_max = time_max or df_data[time_column].max(),
                                         density = dense_interval,
                                         fill_limit = fill_limit,
                                         variables = [column['variable_id'] for column in pivot_columns],
                                         time_index_column = time_index_col,
                                         values_column = values_column,
                                         variable_column = variable_column)
            logger.debug(f"Densified at {dense_interval}s: {df_densified.shape[0]} rows, {df_densified.shape[1]} columns, fill_limit = {fill_limit}")
            
            # intersection between the variables required by the pivot and the available variables
            actual_columns = [column for column in pivot_columns if column['variable_id'] in df_densified.columns]
            missing_columns = [column for column in pivot_columns if column['variable_id'] not in df_densified.columns]
            
            notify_missing_columns(missing_columns, logger)
            if len(actual_columns) < 1:
                logger.warning('No columns')
                continue
                
            # Resample and aggregate
            df_partial_output = resample_aggregate(df_densified, resampling_interval, actual_columns, logger=logger)
            
            # process the "diff" and "nandiff" columns, that has been only aggregated with "first" and "nanfirst" logic
            for column in actual_columns:
                if column['semantic_aggregation'] in ('diff', 'nandiff'):
                    df_partial_output[column['semantic_rename']] = np.ediff1d(df_partial_output[column['semantic_rename']].values, to_end = np.NaN)
            
            # add null columns
            if missing_columns_as_nan:
                for column in missing_columns:
                    df_partial_output[column['semantic_rename']] = np.NaN
            
            # merge with already processed output
            if df_output is None:
                df_output = df_partial_output
            else:
                df_output = pd.merge(df_output, df_partial_output, how = 'outer', left_index = True, right_index = True)
    
    # clean variables to avoid interferences
    try:
        del df_densified
        del pivot_columns
        del df_densified
        del actual_columns
        del missing_columns
        del df_partial_output
    except NameError:
        pass
    
    # Pivot and aggregate columns that must NOT be filled
    if df_unfilled_cols.shape[0] > 0:
        # Pivot data without fill
        df_pivoted = pd.pivot_table(df_data[df_data[variable_column].isin(df_unfilled_cols.variable_id.values)],
                                    index = time_index_col, values = values_column, columns = variable_column)
        
        # Preprocess "trans01" and "trans10" by creating new columns with ones where the transitions happen
        for column in df_unfilled_cols.itertuples():
            if column.semantic_aggregation == 'trans01' and column.variable_id in df_pivoted.columns:
                df_pivoted[column.variable_id + '.trans01'] = (
                        (np.roll(df_pivoted[column.variable_id].ffill().values, 1) == 0) & (
                        df_pivoted[column.variable_id].ffill().values > 0)).astype(int)
                df_unfilled_cols.loc[column.Index, 'variable_id'] = column.variable_id + '.trans01'
            elif column.semantic_aggregation == 'trans10' and column.variable_id in df_pivoted.columns:
                df_pivoted[column.variable_id + '.trans10'] = (
                        (np.roll(df_pivoted[column.variable_id].ffill().values, 1) > 0) & (
                        df_pivoted[column.variable_id].ffill().values == 0)).astype(int)
                df_unfilled_cols.loc[column.Index, 'variable_id'] = column.variable_id + '.trans10'
        
        # for each aggregation interval
        for resampling_interval in df_unfilled_cols.semantic_resampling_rate.unique():
            # pivot columns that uses this aggregation interval
            pivot_columns = df_unfilled_cols[df_unfilled_cols.semantic_resampling_rate == resampling_interval].to_dict(orient = 'records')
            
            # intersection between the variables required by the pivot and the available variables
            actual_columns = [column for column in pivot_columns if column['variable_id'] in df_pivoted.columns]
            missing_columns = [column for column in pivot_columns if column['variable_id'] not in df_pivoted.columns]
            
            notify_missing_columns(missing_columns, logger)
            if len(actual_columns) < 1:
                continue
            
            # perform aggregation
            df_partial_output = resample_aggregate(df_pivoted, resampling_interval, actual_columns, logger=logger)
            # merge with already processed output
            if df_output is None:
                df_output = df_partial_output
            else:
                df_output = pd.merge(df_output, df_partial_output, how = 'outer', left_index = True, right_index = True)
        
    # clean variables to avoid interferences
    try:
        del df_pivoted
        del actual_columns
        del missing_columns
        del df_partial_output
    except NameError:
        pass
    
    # Pivot columns that must NOT be aggregated at all
    if df_noagg_cols.shape[0] > 0:
        # Pivot data without fill
        df_pivoted = pd.pivot_table(df_data[df_data.variable_id.isin(df_noagg_cols.variable_id.values)],
                                    index = time_index_col, values = 'value', columns = 'variable_id')
        
        pivot_columns = df_noagg_cols.to_dict(orient = 'records')
        # intersection between the variables required by the pivot and the available variables
        actual_columns = [column for column in pivot_columns if column['variable_id'] in df_pivoted.columns]
        missing_columns = [column for column in pivot_columns if column['variable_id'] not in df_pivoted.columns]
        notify_missing_columns(missing_columns, logger)
        
        # Rename columns
        df_pivoted.rename(columns={c['variable_id']: c['semantic_rename'] for c in actual_columns}, inplace=True)
        
        # merge with already processed output
        if df_output is None:
            df_output = df_pivoted
        else:
            df_output = pd.merge(df_output, df_pivoted, how = 'outer', left_index = True, right_index = True)
    
    if df_output is None:
        return None
    
    # Drop time index and rename column
    df_output.reset_index(drop = False, names = time_column, inplace=True)
    
    # Build other time columns
    if convert_time_columns is not None:
        for new_time_column in convert_time_columns:
            tz1, tz2 = pytz.timezone(convert_time_columns[new_time_column][0]), pytz.timezone(convert_time_columns[new_time_column][1])
            logger.info(f"Build time column '{new_time_column}' ({tz2}) from '{time_column}' ({tz1})")
            df_output.insert(1, new_time_column, df_output[time_column].df_datatime.tz_localize(tz1).df_datatime.tz_convert(tz2).df_datatime.tz_localize(None))
    
    return df_output
    