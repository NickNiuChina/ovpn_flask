import pytest

from carelds.common.data import get_masterdata_interface
from carelds.common.data.presto import PrestoInterface
from carelds.common.data.trino import TrinoInterface
from carelds.common.logging.logutil import get_logger
import pandas as pd
import numpy as np
from datetime import datetime, date
import os

logger = get_logger('test_data_interface')
os.environ['DS_DREMIO_CONNSTRING'] = 'Driver=/opt/dremio-odbc/lib64/libdrillodbc_sb64.so;ConnectionType=Direct;HOST=ds-be-test-analyze.test-ds.lan;PORT=31010;AuthenticationType=Plain;UID=test;PWD=test123456'

@pytest.fixture(autouse=True)
def print_before_test():
    print()


"""
    DREMIO TESTS
"""
'''def test_dremio_interface_read_device_flight_local():
    """
    Read data with Dremio (flight)
    """
    print()
    dremio = get_dremio_interface(backend='flight', lake='local', logger=logger)
    df = dremio.read_device(date(2020,2,1), date(2020,2,3), '558ee05c2ff1f42b4f941c4eb7d759fe7994aeed')
    assert df.shape[0] == 23040
    assert df.time_local.min() == datetime(2020,2,1)
    assert df.time_local.max() == datetime(2020,2,2,23,59)
    assert -6.8920 < df['value'].mean() < -6.8919'''

'''def test_dremio_interface_read_device_flight_hive():
    """
    Read data with Dremio (flight)
    """
    print()
    dremio = get_dremio_interface(backend='flight', lake='hive', logger=logger)
    df = dremio.read_device(date(2020,2,1), date(2020,2,3), '558ee05c2ff1f42b4f941c4eb7d759fe7994aeed')
    assert df.shape[0] == 23040
    assert df.time_local.min() == datetime(2020,2,1)
    assert df.time_local.max() == datetime(2020,2,2,23,59)
    assert -6.8920 < df['value'].mean() < -6.8919'''


'''def test_dremio_interface_read_device_odbc_local():
    """
    Read data with Dremio (odbc)
    """
    print()
    dremio = get_dremio_interface(backend='odbc', lake='local', logger=logger)
    print(dremio.backend)
    df = dremio.read_device(date(2020,2,1), date(2020,2,3), '558ee05c2ff1f42b4f941c4eb7d759fe7994aeed')
    assert df.shape[0] == 23040
    assert df.time_local.min() == datetime(2020,2,1)
    assert df.time_local.max() == datetime(2020,2,2,23,59)
    assert -6.8920 < df['value'].mean() < -6.8919'''

'''def test_dremio_interface_read_device_odbc_local():
    """
    Read data with Dremio (odbc)
    """
    print()
    dremio = get_dremio_interface(backend='odbc', lake='hive', logger=logger)
    df = dremio.read_device(date(2020,2,1), date(2020,2,3), '558ee05c2ff1f42b4f941c4eb7d759fe7994aeed')
    assert df.shape[0] == 23040
    assert df.time_local.min() == datetime(2020,2,1)
    assert df.time_local.max() == datetime(2020,2,2,23,59)
    assert -6.8920 < df['value'].mean() < -6.8919'''


'''def test_dremio_interface_read_device_semantics_all_local():
    """
    Read data and all semantics with Dremio (flight)
    """
    print()
    dremio = get_dremio_interface(backend='flight', lake='local', logger=logger)
    df = dremio.read_device(date(2020,2,1), date(2020,2,3), '558ee05c2ff1f42b4f941c4eb7d759fe7994aeed', semantics=True)
    assert df.shape[0] == 23040
    assert df.time_local.min() == datetime(2020,2,1)
    assert df.time_local.max() == datetime(2020,2,2,23,59)
    df = pd.pivot_table(df, index='time_local', columns='semantic', values='value').reset_index(drop=False)
    assert 'defrost_temperature' in df.columns
    assert 'active_power' in df.columns
    assert 'efficiency' in df.columns'''


'''def test_dremio_interface_read_device_semantics_all():
    """
    Read data and all semantics with Dremio (flight)
    """
    print()
    dremio = get_dremio_interface(backend='flight', lake='hive', logger=logger)
    df = dremio.read_device(date(2020,2,1), date(2020,2,3), '558ee05c2ff1f42b4f941c4eb7d759fe7994aeed', semantics=True)
    assert df.shape[0] == 23040
    assert df.time_local.min() == datetime(2020,2,1)
    assert df.time_local.max() == datetime(2020,2,2,23,59)
    df = pd.pivot_table(df, index='time_local', columns='semantic', values='value').reset_index(drop=False)
    assert 'defrost_temperature' in df.columns
    assert 'active_power' in df.columns
    assert 'efficiency' in df.columns'''


'''def test_dremio_interface_read_device_semantics_some():
    """
    Read data and some semantics with Dremio (flight)
    """
    print()
    dremio = get_dremio_interface(backend='flight', lake='local', logger=logger)
    df = dremio.read_device(date(2020,2,1), date(2020,2,3), '558ee05c2ff1f42b4f941c4eb7d759fe7994aeed', semantics=['defrost_temperature', 'air_off_temperature'])
    assert df.shape[0] == 2880
    assert df.time_local.min() == datetime(2020,2,1)
    assert df.time_local.max() == datetime(2020,2,2,23,59)
    df = pd.pivot_table(df, index='time_local', columns='semantic', values='value').reset_index(drop=False)
    assert 'defrost_temperature' in df.columns
    assert 'air_off_temperature' not in df.columns'''


'''def test_dremio_interface_read_device_utc_local():
    """
    Read data and some semantics with Dremio (flight), filtering by utc and local
    """
    print()
    dremio = get_dremio_interface(backend='flight', lake='local', logger=logger)
    # by default read by time_local
    df_local = dremio.read_device(date(2020, 7, 2), date(2020, 7, 4), 'd05a4afb206853854aceef4453fdaeb751058e60', semantics=['outdoor_temperature', 'indoor_temperature'])
    assert df_local.shape[0] == 11520
    assert df_local.time_local.min() == datetime(2020, 7, 2)
    assert df_local.time_local.max() == datetime(2020, 7, 3, 23, 59, 30)
    df_utc = dremio.read_device(date(2020, 7, 2), date(2020, 7, 4), 'd05a4afb206853854aceef4453fdaeb751058e60', semantics=['outdoor_temperature', 'indoor_temperature'], time_column='time_utc')
    assert df_utc.shape[0] == 11520
    assert df_utc.time_utc.min() == datetime(2020, 7, 2)
    assert df_utc.time_utc.max() == datetime(2020, 7, 3, 23, 59, 30)
    df = pd.pivot_table(df_local, index='time_local', columns='semantic', values='value').reset_index(drop=False)
    assert 'outdoor_temperature' in df.columns
    assert 'indoor_temperature' in df.columns
    assert 'air_off_temperature' not in df.columns
'''



"""
    PRESTO TESTS
"""

def test_presto_interface_connection():
    presto = PrestoInterface(user='test', hostname='ds-be-test-presto01.test-ds.lan', port='8080', logger=logger)
    assert presto.test_connection()


def test_presto_interface_device_data():
    presto = PrestoInterface(user='test', hostname='ds-be-test-presto01.test-ds.lan', port='8080', logger=logger)
    df = presto.read_device(date(2020,2,1), date(2020,2,3), '558ee05c2ff1f42b4f941c4eb7d759fe7994aeed', analysis=False)
    assert df.shape[0] == 23040
    assert df.time_local.min() == datetime(2020, 2, 1)
    assert df.time_local.max() < datetime(2020, 2, 3)
    assert -6.8920 < df['value'].mean() < -6.8919


def test_presto_interface_query():
    presto = PrestoInterface(user='test', hostname='ds-be-test-presto01.test-ds.lan', port='8080', logger=logger)
    res = presto.execute('SELECT 1 "value" ', dataframe=False)
    assert res.fetchone()['value'] == 1
    res = presto.execute('SELECT 1 "value" ', dataframe=True)
    assert res['value'].values[0] == 1


def test_presto_interface_query_params():
    presto = PrestoInterface(user='test', hostname='ds-be-test-presto01.test-ds.lan', port='8080', logger=logger)
    res = presto.execute('SELECT :v "value"', params=dict(v=1), dataframe=False)
    assert res.fetchone()['value'] == 1


def test_presto_interface_device_timezone():
    presto = PrestoInterface(user='test', hostname='ds-be-test-presto01.test-ds.lan', port='8080', logger=logger)
    try:
        tz = presto.get_device_timezone('16d2298ca1a09eee2d32dbb233b5b21e4437d20a') == 'Europe/Paris'
    except:
        logger.exception('Error')
    assert tz


def test_presto_interface_read_device():
    """
    Read data with Presto
    """
    presto = PrestoInterface(user='test', hostname='ds-be-test-presto01.test-ds.lan', port='8080', logger=logger)
    df = presto.read_device(date(2020,2,1), date(2020,2,3), '558ee05c2ff1f42b4f941c4eb7d759fe7994aeed')
    assert df.shape[0] == 23040
    assert df.time_local.min() == datetime(2020,2,1)
    assert df.time_local.max() == datetime(2020,2,2,23,59)
    assert -6.8920 < df['value'].mean() < -6.8919


def test_presto_interface_read_device_semantics_all():
    """
    Read data and all semantics with Presto
    """
    presto = PrestoInterface(user='test', hostname='ds-be-test-presto01.test-ds.lan', port='8080', logger=logger)
    df = presto.read_device(date(2020,2,1), date(2020,2,3), '558ee05c2ff1f42b4f941c4eb7d759fe7994aeed', semantics=True)
    assert df.shape[0] == 23040
    assert df.time_local.min() == datetime(2020,2,1)
    assert df.time_local.max() == datetime(2020,2,2,23,59)
    df = pd.pivot_table(df, index='time_local', columns='semantic', values='value').reset_index(drop=False)
    assert 'defrost_temperature' in df.columns
    assert 'active_power' in df.columns
    assert 'efficiency' in df.columns


def test_presto_interface_read_device_semantics_some_from_rmpro():
    """
    Read data and some semantics with Presto
    """
    presto = PrestoInterface(user='test', hostname='ds-be-test-presto01.test-ds.lan', port='8080', logger=logger)
    df = presto.read_device(date(2020, 10, 1), date(2020, 10, 3), 'e9952bccb62ed3ca6ab5ea57c0a19ce50c055df6',
                            semantics=['compressor_1_status', 'compressor_2_status', 'condenser_pressure'])
    assert df.shape[0] == 3*1440*2
    assert df.time_local.min() == datetime(2020, 10, 1)
    assert df.time_local.max() == datetime(2020, 10, 2, 23, 59)
    assert len(df.semantic.unique()) == 3
    assert 'compressor_1_status L1' in df.semantic.unique()
    assert 'compressor_2_status L1' in df.semantic.unique()
    assert 'condenser_pressure' in df.semantic.unique()
    assert 'compressor_1_status' not in df.semantic.unique()


def test_presto_interface_read_device_semantics_some_from_rmpro_optimized():
    """
    Read data and some semantics with Presto using optimized SQL
    """
    presto = PrestoInterface(user='test', hostname='ds-be-test-presto01.test-ds.lan', port='8080', logger=logger)
    df = presto.read_device(date(2020, 10, 2), date(2020, 10, 4), 'e9952bccb62ed3ca6ab5ea57c0a19ce50c055df6',
                            semantics=['compressor_1_status', 'compressor_2_status', 'condenser_pressure'], system=1)
    assert df.shape[0] == 3*1440*2
    assert df.time_local.min() == datetime(2020, 10, 2)
    assert df.time_local.max() == datetime(2020, 10, 3, 23, 59)
    assert len(df.semantic.unique()) == 3
    assert 'compressor_1_status L1' in df.semantic.unique()
    assert 'compressor_2_status L1' in df.semantic.unique()
    assert 'condenser_pressure' in df.semantic.unique()
    assert 'compressor_1_status' not in df.semantic.unique()


def test_presto_interface_read_device_semantics_some_from_tera():
    """
    Read data and some semantics with Presto
    """
    presto = PrestoInterface(user='test', hostname='ds-be-test-presto01.test-ds.lan', port='8080', logger=logger)
    df = presto.read_device(date(2020, 2, 1), date(2020, 2, 3), '5ad7d0516eae7d383c7d745e40780ac5a75deed9',
                            semantics=['outdoor_temperature', 'indoor_temperature'])
    assert df.shape[0] == 1440*2*2*2
    assert df.time_local.min() == datetime(2020, 2, 1)
    assert df.time_local.max() == datetime(2020, 2, 2, 23, 59, 30)
    df = pd.pivot_table(df, index='time_local', columns='semantic', values='value').reset_index(drop=False)
    assert 'outdoor_temperature' in df.columns
    assert 'indoor_temperature' in df.columns
    assert 'outdoor_humidity' not in df.columns


def test_presto_interface_pivot():
    """

    """
    f_nanfirst = lambda v: v[~np.isnan(v)][0] if np.count_nonzero(~np.isnan(v)) > 0 else np.nan  # First not null value
    f_nanlast = lambda v: v[~np.isnan(v)][-1] if np.count_nonzero(~np.isnan(v)) > 0 else np.nan  # Last not null value
    f_nansum = lambda v: np.nansum(v) if np.count_nonzero(~np.isnan(v)) > 0 else np.nan  # Like np.nansum but return nan (and not 0) if all values are nan, equals Presto's "sum()"
    f_first = lambda v: v[0] if len(v) > 0 else np.nan  # First value
    f_last = lambda v: v[-1] if len(v) > 0 else np.nan  # Last value
    aggregations = [('defrost_temperature', 'nanmean', 'defrost_temperature'),
                    ('exp_valve_opening', 'first', 'valve_first'),
                    ('exp_valve_opening', 'last', 'valve_last'),
                    ('exp_valve_opening', 'nanfirst', 'valve_nanfirst'),
                    ('air_on_temperature', 'nanlast', 'valve_nanlast'),
                    ('defrost_status', 'nanmean', 'defrost_status'),
                    ('defrost_status', 'trans01', 'defrost_switch_on'),
                    ('defrost_status', 'trans10', 'defrost_switch_off'),
                    ('non_existent_semantic', 'nanmean', 'none')
                    ]

    presto = PrestoInterface(user='test', hostname='ds-be-test-presto01.test-ds.lan', port='8080', logger=logger)
    pv1 = presto.pivot_data(device_uid='aa2f6a232172526471cf357af9481e996c9225ac', time_from=datetime(2020, 9, 1),
                            time_to=datetime(2020, 10, 1), interval=15, aggregations=aggregations, table='hive.data.data_1_sem_v')

    df = presto.read_device(device_uid='aa2f6a232172526471cf357af9481e996c9225ac', time_column='time_local',
                            time_from=datetime(2020, 9, 1), time_to=datetime(2020, 10, 1), semantics=True)

    pv2 = pd.pivot_table(df, index='time_local', columns='semantic', values='value')
    pv2['defrost_switch_on'] = (pv2['defrost_status'] - pv2['defrost_status'].shift(1)).values > .5
    pv2['defrost_switch_off'] = (pv2['defrost_status'] - pv2['defrost_status'].shift(1)).values < -.5
    pv2 = pv2.resample('15T').agg(
        {'defrost_temperature': np.nanmean, 'exp_valve_opening': [f_first, f_last, f_nanfirst], 'air_on_temperature': f_nanlast, 'defrost_status': np.nanmean,
         'defrost_switch_on': np.nansum, 'defrost_switch_off': np.nansum}).reset_index(drop=False)
    pv2.columns = ['time_local', 'defrost_temperature', 'valve_first', 'valve_last', 'valve_nanfirst', 'valve_nanlast', 'defrost_status', 'defrost_switch_on', 'defrost_switch_off']
    pv2['none'] = np.nan

    assert pv2.shape[0] == pv1.shape[0]

    pv2.time_local = pv2.time_local.astype('datetime64[s]')
    pv1.time_local = pv1.time_local.astype('datetime64[s]')
    pv2.sort_values(by='time_local', inplace=True)
    pv1.sort_values(by='time_local', inplace=True)
    if 'time_utc' in pv1.columns:
        pv1.drop(columns=['time_utc'], inplace=True)
    if 'time_utc' in pv2.columns:
        pv2.drop(columns=['time_utc'], inplace=True)
    for r in range(20):
        for k in pv1.iloc[r].keys():
            if k.startswith('time_'):
                assert pv1.iloc[r][k] == pv2.iloc[r][k]
            else:
                assert abs(pv1.iloc[r][k]-pv2.iloc[r][k]) < 10**(-9) or (pd.isna(pv1.iloc[r][k]) and pd.isna(pv2.iloc[r][k]))


def test_presto_interface_pivot_hours():
    """

    """
    f_nanfirst = lambda v: v[~np.isnan(v)][0] if np.count_nonzero(~np.isnan(v)) > 0 else np.nan  # First not null value
    f_nanlast = lambda v: v[~np.isnan(v)][-1] if np.count_nonzero(~np.isnan(v)) > 0 else np.nan  # Last not null value
    f_nansum = lambda v: np.nansum(v) if np.count_nonzero(~np.isnan(v)) > 0 else np.nan  # Like np.nansum but return nan (and not 0) if all values are nan, equals Presto's "sum()"
    f_first = lambda v: v[0] if len(v) > 0 else np.nan  # First value
    f_last = lambda v: v[-1] if len(v) > 0 else np.nan  # Last value
    aggregations = [('defrost_temperature', 'nanmean', 'defrost_temperature'),
                    ('exp_valve_opening', 'first', 'valve_first'),
                    ('exp_valve_opening', 'last', 'valve_last'),
                    ('exp_valve_opening', 'nanfirst', 'valve_nanfirst'),
                    ('air_on_temperature', 'nanlast', 'valve_nanlast'),
                    ('defrost_status', 'nanmean', 'defrost_status'),
                    ('non_existent_semantic', 'nanmean', 'none')
                    ]

    presto = PrestoInterface(user='test', hostname='ds-be-test-presto01.test-ds.lan', port='8080', logger=logger)
    pv1 = presto.pivot_data(device_uid='aa2f6a232172526471cf357af9481e996c9225ac', time_from=datetime(2020, 9, 1),
                            time_to=datetime(2020, 9, 2), interval=60*3, aggregations=aggregations)

    df = presto.read_device(device_uid='aa2f6a232172526471cf357af9481e996c9225ac', time_column='time_local',
                            time_from=datetime(2020, 9, 1), time_to=datetime(2020, 9, 2), semantics=True)
    pv2 = pd.pivot_table(df, index='time_local', columns='semantic', values='value').resample('3H').agg(
        {'defrost_temperature': np.nanmean, 'exp_valve_opening': [f_first, f_last, f_nanfirst], 'air_on_temperature': f_nanlast, 'defrost_status': np.nanmean}).reset_index(drop=False)
    pv2.columns = ['time_local', 'defrost_temperature', 'valve_first', 'valve_last', 'valve_nanfirst', 'valve_nanlast', 'defrost_status']
    pv2['none'] = np.nan

    assert pv2.shape[0] == pv1.shape[0]

    pv2.time_local = pv2.time_local.astype('datetime64[s]')
    pv1.time_local = pv1.time_local.astype('datetime64[s]')
    pv2.sort_values(by='time_local', inplace=True)
    pv1.sort_values(by='time_local', inplace=True)
    if 'time_utc' in pv1.columns:
        pv1.drop(columns=['time_utc'], inplace=True)
    if 'time_utc' in pv2.columns:
        pv2.drop(columns=['time_utc'], inplace=True)
    for r in range(min(20, pv1.shape[0])):
        for k in pv1.iloc[r].keys():
            if k.startswith('time_'):
                assert pv1.iloc[r][k] == pv2.iloc[r][k]
            else:
                assert abs(pv1.iloc[r][k]-pv2.iloc[r][k]) < 10**(-9) or (pd.isna(pv1.iloc[r][k]) and pd.isna(pv2.iloc[r][k])), f"{k} at {pv1.iloc[r]['time_local']}"


def test_presto_interface_pivot_none():
    """

    """
    f_nanfirst = lambda v: v[~np.isnan(v)][0] if np.count_nonzero(~np.isnan(v)) > 0 else np.nan  # First not null value
    f_nanlast = lambda v: v[~np.isnan(v)][-1] if np.count_nonzero(~np.isnan(v)) > 0 else np.nan  # Last not null value
    f_nansum = lambda v: np.nansum(v) if np.count_nonzero(~np.isnan(v)) > 0 else np.nan  # Like np.nansum but return nan (and not 0) if all values are nan, equals Presto's "sum()"
    f_first = lambda v: v[0] if len(v) > 0 else np.nan  # First value
    f_last = lambda v: v[-1] if len(v) > 0 else np.nan  # Last value
    aggregations = [('defrost_temperature', 'nanfirst', 'defrost_temperature'),
                    ('exp_valve_opening', 'nanfirst', None),
                    ('air_on_temperature', 'nanfirst', None),
                    ('defrost_status', 'nanfirst', 'defrost_status'),
                    ('non_existent_semantic', 'nanfirst', 'none')
                    ]

    presto = PrestoInterface(user='test', hostname='ds-be-test-presto01.test-ds.lan', port='8080', logger=logger)
    pv1 = presto.pivot_data(device_uid='aa2f6a232172526471cf357af9481e996c9225ac', time_from=datetime(2020, 9, 1),
                            time_to=datetime(2020, 10, 1), interval=None, aggregations=aggregations)

    df = presto.read_device(device_uid='aa2f6a232172526471cf357af9481e996c9225ac', time_column='time_local',
                            time_from=datetime(2020, 9, 1), time_to=datetime(2020, 10, 1),
                            semantics=['defrost_temperature', 'exp_valve_opening', 'air_on_temperature', 'defrost_status'])
    pv2 = pd.pivot_table(df, index='time_local', columns='semantic', values='value').reset_index(drop=False)
    #pv2.columns = ['time_local', 'defrost_temperature', 'valve_first', 'valve_last', 'valve_nanfirst', 'valve_nanlast', 'defrost_status']
    pv2['none'] = np.nan

    assert pv2.shape[0] == pv1.shape[0]

    pv2.time_local = pv2.time_local.astype('datetime64[s]')
    pv1.time_local = pv1.time_local.astype('datetime64[s]')
    pv2.sort_values(by='time_local', inplace=True)
    pv1.sort_values(by='time_local', inplace=True)
    if 'time_utc' in pv1.columns:
        pv1.drop(columns=['time_utc'], inplace=True)
    if 'time_utc' in pv2.columns:
        pv2.drop(columns=['time_utc'], inplace=True)
    for r in range(20):
        for k in pv1.iloc[r].keys():
            if k.startswith('time_'):
                assert pv1.iloc[r][k] == pv2.iloc[r][k]
            else:
                assert abs(pv1.iloc[r][k]-pv2.iloc[r][k]) < 10**(-9) or (pd.isna(pv1.iloc[r][k]) and pd.isna(pv2.iloc[r][k]))


def test_presto_interface_pivot_advanced():
    """
    Pivot with nandiff aggregation and subsemantics.
    Compare Presto pivot and pandas resample/pivot

    """
    f_nanfirst = lambda v: v[~np.isnan(v)][0] if np.count_nonzero(~np.isnan(v)) > 0 else np.nan  # First not null value
    aggregations = [('active_energy_counter COOLING', 'nandiff', 'cooling_active_energy')]
    
    presto = PrestoInterface(user='test', hostname='ds-be-test-presto01.test-ds.lan', port='8080', logger=logger)
    pv1 = presto.pivot_data(device_uid='27ec871796e0fee22e782ccb5612a05812a095d7', time_from=datetime(2022, 3, 1),
                             time_to=datetime(2022, 3, 2), interval=60, aggregations=aggregations)[['time_utc', 'cooling_active_energy']]

    df = presto.read_device(device_uid = '27ec871796e0fee22e782ccb5612a05812a095d7', time_column = 'time_utc',
                            time_from = datetime(2022, 3, 1), time_to = datetime(2022, 3, 2),
                            semantics = True, subsemantics = True)

    pv2 = pd.pivot_table(df, index = 'time_utc', columns = 'semantic', values = 'value').resample('60T').agg({
        'active_energy_counter COOLING': f_nanfirst
    }).reset_index(drop=False)
    pv2.columns = ['time_utc', 'cooling_active_energy']
    pv2['cooling_active_energy'] = pv2['cooling_active_energy'].shift(-1) - pv2['cooling_active_energy']
    
    pv = pd.merge(pv1, pv2, left_on = 'time_utc', right_on = 'time_utc', how = 'inner').dropna(subset = ['cooling_active_energy_x', 'cooling_active_energy_y'])
    for row in pv.itertuples():
        assert row[2] == row[3]


def test_presto_entity_details():
    presto = PrestoInterface(user='test', hostname='ds-be-test-presto01.test-ds.lan', port='8080', logger=logger)

    device_info = presto.get_entity_details('2d3d24c48c4035428a112de43271967ff943eb7b')
    assert device_info['entity_uid'] == '2d3d24c48c4035428a112de43271967ff943eb7b'
    assert device_info['entity_type'] == 'device'
    assert device_info['entity_id'] == '9732'
    assert device_info['source_system_id'] == 0
    assert device_info['entity_timezone'] == 'Europe/Paris'

    device_info = presto.get_entity_details('56479e26bb139e08665b4bd5da1a0de4a141205a')
    assert device_info['entity_uid'] == '56479e26bb139e08665b4bd5da1a0de4a141205a'
    assert device_info['source_system_id'] == 1

    device_info = presto.get_entity_details('0308ccac682cdeabcfbc26ece3480ea9f0bfe91d')
    assert device_info['entity_type'] == 'plant'
    assert device_info['tenant_id'] == 'MAN_HEOS'

    device_info = presto.get_entity_details('2d3d24c48c4035428a112de43271967ff943eb7a')
    assert device_info is None


def test_presto_project_details():
    presto = PrestoInterface(user='test', hostname='ds-be-test-presto01.test-ds.lan', port='8080', logger=logger)

    pj = presto.get_project_details(12)
    assert pj['project_id'] == 12
    assert pj['project_code'] == 'heos_baseline'
    assert pj['project_output_type'] == 'analysis'

    pj = presto.get_project_details(9999)
    assert pj is None


"""
    MASTERDATA TESTS
"""

def test_masterdata_interface_device_timezone():
    print()
    try:
        tz = get_masterdata_interface().get_device_timezone('16d2298ca1a09eee2d32dbb233b5b21e4437d20a') == 'Europe/Paris'
    except:
        logger.exception('Error')
    assert tz


def test_masterdata_interface_project_details():
    print()
    try:
        pj = get_masterdata_interface().get_project_details(2)
    except:
        logger.exception('Error')
    assert isinstance(pj, dict)
    assert pj['project_id'] == 2



"""
    TRINO TESTS
"""

def test_trino_interface_connection():
    trino = TrinoInterface(user='test', hostname='ds-be-test-trino01.test-ds.lan', port='8080', logger=logger)
    assert trino.test_connection()


def test_trino_interface_device_data():
    trino = TrinoInterface(user='test', hostname='ds-be-test-trino01.test-ds.lan', port='8080', logger=logger)
    df = trino.read_device(date(2020, 2, 1), date(2020, 2, 3), '558ee05c2ff1f42b4f941c4eb7d759fe7994aeed',
                            analysis=False)
    assert df.shape[0] == 23040
    assert df.time_local.min() == datetime(2020, 2, 1)
    assert df.time_local.max() < datetime(2020, 2, 3)
    assert -6.8920 < df['value'].mean() < -6.8919


def test_trino_interface_query():
    trino = TrinoInterface(user='test', hostname='ds-be-test-trino01.test-ds.lan', port='8080', logger=logger)
    res = trino.execute('SELECT 1 "value" ', dataframe=False)
    assert res.fetchone()['value'] == 1
    res = trino.execute('SELECT 1 "value" ', dataframe=True)
    assert res['value'].values[0] == 1


def test_trino_interface_query_params():
    trino = TrinoInterface(user='test', hostname='ds-be-test-trino01.test-ds.lan', port='8080', logger=logger)
    res = trino.execute('SELECT :v "value"', params=dict(v=1), dataframe=False)
    assert res.fetchone()['value'] == 1


def test_trino_interface_device_timezone():
    trino = TrinoInterface(user='test', hostname='ds-be-test-trino01.test-ds.lan', port='8080', logger=logger)
    try:
        tz = trino.get_device_timezone('16d2298ca1a09eee2d32dbb233b5b21e4437d20a') == 'Europe/Paris'
    except:
        logger.exception('Error')
    assert tz


def test_trino_interface_read_device():
    """
    Read data with Presto
    """
    trino = TrinoInterface(user='test', hostname='ds-be-test-trino01.test-ds.lan', port='8080', logger=logger)
    df = trino.read_device(date(2020, 2, 1), date(2020, 2, 3), '558ee05c2ff1f42b4f941c4eb7d759fe7994aeed')
    assert df.shape[0] == 23040
    assert df.time_local.min() == datetime(2020, 2, 1)
    assert df.time_local.max() == datetime(2020, 2, 2, 23, 59)
    assert -6.8920 < df['value'].mean() < -6.8919


def test_trino_interface_read_device_semantics_all():
    """
    Read data and all semantics with Presto
    """
    trino = TrinoInterface(user='test', hostname='ds-be-test-trino01.test-ds.lan', port='8080', logger=logger)
    df = trino.read_device(date(2020, 2, 1), date(2020, 2, 3), '558ee05c2ff1f42b4f941c4eb7d759fe7994aeed',
                            semantics=True)
    assert df.shape[0] == 23040
    assert df.time_local.min() == datetime(2020, 2, 1)
    assert df.time_local.max() == datetime(2020, 2, 2, 23, 59)
    df = pd.pivot_table(df, index='time_local', columns='semantic', values='value').reset_index(drop=False)
    assert 'defrost_temperature' in df.columns
    assert 'active_power' in df.columns
    assert 'efficiency' in df.columns


def test_trino_interface_read_device_semantics_some_from_rmpro():
    """
    Read data and some semantics with Presto
    """
    trino = TrinoInterface(user='test', hostname='ds-be-test-trino01.test-ds.lan', port='8080', logger=logger)
    df = trino.read_device(date(2020, 10, 1), date(2020, 10, 3), 'e9952bccb62ed3ca6ab5ea57c0a19ce50c055df6',
                            semantics=['compressor_1_status', 'compressor_2_status', 'condenser_pressure'])
    assert df.shape[0] == 3 * 1440 * 2
    assert df.time_local.min() == datetime(2020, 10, 1)
    assert df.time_local.max() == datetime(2020, 10, 2, 23, 59)
    assert len(df.semantic.unique()) == 3
    assert 'compressor_1_status L1' in df.semantic.unique()
    assert 'compressor_2_status L1' in df.semantic.unique()
    assert 'condenser_pressure' in df.semantic.unique()
    assert 'compressor_1_status' not in df.semantic.unique()


def test_trino_interface_read_device_semantics_some_from_rmpro_optimized():
    """
    Read data and some semantics with Presto using optimized SQL
    """
    trino = TrinoInterface(user='test', hostname='ds-be-test-trino01.test-ds.lan', port='8080', logger=logger)
    df = trino.read_device(date(2020, 10, 2), date(2020, 10, 4), 'e9952bccb62ed3ca6ab5ea57c0a19ce50c055df6',
                            semantics=['compressor_1_status', 'compressor_2_status', 'condenser_pressure'], system=1)
    assert df.shape[0] == 3*1440*2
    assert df.time_local.min() == datetime(2020, 10, 2)
    assert df.time_local.max() == datetime(2020, 10, 3, 23, 59)
    assert len(df.semantic.unique()) == 3
    assert 'compressor_1_status L1' in df.semantic.unique()
    assert 'compressor_2_status L1' in df.semantic.unique()
    assert 'condenser_pressure' in df.semantic.unique()
    assert 'compressor_1_status' not in df.semantic.unique()


def test_trino_interface_read_device_semantics_some_from_tera():
    """
    Read data and some semantics with Presto
    """
    trino = TrinoInterface(user='test', hostname='ds-be-test-trino01.test-ds.lan', port='8080', logger=logger)
    df = trino.read_device(date(2020, 2, 1), date(2020, 2, 3), '5ad7d0516eae7d383c7d745e40780ac5a75deed9', semantics=['outdoor_temperature', 'indoor_temperature'])
    assert df.shape[0] == 1440*2*2*2
    assert df.time_local.min() == datetime(2020, 2, 1)
    assert df.time_local.max() == datetime(2020, 2, 2, 23, 59, 30)
    df = pd.pivot_table(df, index='time_local', columns='semantic', values='value').reset_index(drop=False)
    assert 'outdoor_temperature' in df.columns
    assert 'indoor_temperature' in df.columns
    assert 'outdoor_humidity' not in df.columns


f_nanfirst = lambda v: v[~np.isnan(v)][0] if np.count_nonzero(~np.isnan(v)) > 0 else np.nan  # First not null value
f_nanlast = lambda v: v[~np.isnan(v)][-1] if np.count_nonzero(~np.isnan(v)) > 0 else np.nan  # Last not null value
f_nansum = lambda v: np.nansum(v) if np.count_nonzero(~np.isnan(v)) > 0 else np.nan  # Like np.nansum but return nan (and not 0) if all values are nan, equals Presto's "sum()"
f_first = lambda v: v[0] if len(v) > 0 else np.nan  # First value
f_last = lambda v: v[-1] if len(v) > 0 else np.nan  # Last value


def test_trino_interface_pivot():
    """

    """
    aggregations = [('defrost_temperature', 'nanmean', 'defrost_temperature'),
                    ('exp_valve_opening', 'first', 'valve_first'),
                    ('exp_valve_opening', 'last', 'valve_last'),
                    ('exp_valve_opening', 'nanfirst', 'valve_nanfirst'),
                    ('air_on_temperature', 'nanlast', 'valve_nanlast'),
                    ('defrost_status', 'nanmean', 'defrost_status'),
                    ('defrost_status', 'trans01', 'defrost_switch_on'),
                    ('defrost_status', 'trans10', 'defrost_switch_off'),
                    ('non_existent_semantic', 'nanmean', 'none')
                    ]

    trino = TrinoInterface(user='test', hostname='ds-be-test-trino01.test-ds.lan', port='8080', logger=logger)
    pv1 = trino.pivot_data(device_uid='aa2f6a232172526471cf357af9481e996c9225ac', time_from=datetime(2020, 9, 1),
                            time_to=datetime(2020, 10, 1), interval=15, aggregations=aggregations, table='hive.data.data_1_sem_v')

    df = trino.read_device(device_uid='aa2f6a232172526471cf357af9481e996c9225ac', time_column='time_local',
                            time_from=datetime(2020, 9, 1), time_to=datetime(2020, 10, 1), semantics=True)

    pv2 = pd.pivot_table(df, index='time_local', columns='semantic', values='value')
    pv2['defrost_switch_on'] = (pv2['defrost_status'] - pv2['defrost_status'].shift(1)).values > .5
    pv2['defrost_switch_off'] = (pv2['defrost_status'] - pv2['defrost_status'].shift(1)).values < -.5
    pv2 = pv2.resample('15T').agg(
        {'defrost_temperature': np.nanmean, 'exp_valve_opening': [f_first, f_last, f_nanfirst], 'air_on_temperature': f_nanlast, 'defrost_status': np.nanmean,
         'defrost_switch_on': np.nansum, 'defrost_switch_off': np.nansum}).reset_index(drop=False)
    pv2.columns = ['time_local', 'defrost_temperature', 'valve_first', 'valve_last', 'valve_nanfirst', 'valve_nanlast', 'defrost_status', 'defrost_switch_on', 'defrost_switch_off']
    pv2['none'] = np.nan

    assert pv2.shape[0] == pv1.shape[0]

    pv2.time_local = pv2.time_local.astype('datetime64[s]')
    pv1.time_local = pv1.time_local.astype('datetime64[s]')
    pv2.sort_values(by='time_local', inplace=True)
    pv1.sort_values(by='time_local', inplace=True)
    if 'time_utc' in pv1.columns:
        pv1.drop(columns=['time_utc'], inplace=True)
    if 'time_utc' in pv2.columns:
        pv2.drop(columns=['time_utc'], inplace=True)
    for r in range(20):
        for k in pv1.iloc[r].keys():
            if k.startswith('time_'):
                assert pv1.iloc[r][k] == pv2.iloc[r][k]
            else:
                assert abs(pv1.iloc[r][k]-pv2.iloc[r][k]) < 10**(-9) or (pd.isna(pv1.iloc[r][k]) and pd.isna(pv2.iloc[r][k]))


def test_trino_interface_pivot_hours():
    """

    """
    aggregations = [('defrost_temperature', 'nanmean', 'defrost_temperature'),
                    ('exp_valve_opening', 'first', 'valve_first'),
                    ('exp_valve_opening', 'last', 'valve_last'),
                    ('exp_valve_opening', 'nanfirst', 'valve_nanfirst'),
                    ('air_on_temperature', 'nanlast', 'valve_nanlast'),
                    ('defrost_status', 'nanmean', 'defrost_status'),
                    ('non_existent_semantic', 'nanmean', 'none')
                    ]

    trino = TrinoInterface(user='test', hostname='ds-be-test-trino01.test-ds.lan', port='8080', logger=logger)
    pv1 = trino.pivot_data(device_uid='aa2f6a232172526471cf357af9481e996c9225ac', time_from=datetime(2020, 9, 1),
                            time_to=datetime(2020, 9, 2), interval=60*3, aggregations=aggregations)

    df = trino.read_device(device_uid='aa2f6a232172526471cf357af9481e996c9225ac', time_column='time_local',
                            time_from=datetime(2020, 9, 1), time_to=datetime(2020, 9, 2), semantics=True)
    pv2 = pd.pivot_table(df, index='time_local', columns='semantic', values='value').resample('3H').agg(
        {'defrost_temperature': np.nanmean, 'exp_valve_opening': [f_first, f_last, f_nanfirst], 'air_on_temperature': f_nanlast, 'defrost_status': np.nanmean}).reset_index(drop=False)
    pv2.columns = ['time_local', 'defrost_temperature', 'valve_first', 'valve_last', 'valve_nanfirst', 'valve_nanlast', 'defrost_status']
    pv2['none'] = np.nan

    assert pv2.shape[0] == pv1.shape[0]

    pv2.time_local = pv2.time_local.astype('datetime64[s]')
    pv1.time_local = pv1.time_local.astype('datetime64[s]')
    pv2.sort_values(by='time_local', inplace=True)
    pv1.sort_values(by='time_local', inplace=True)
    if 'time_utc' in pv1.columns:
        pv1.drop(columns=['time_utc'], inplace=True)
    if 'time_utc' in pv2.columns:
        pv2.drop(columns=['time_utc'], inplace=True)
    for r in range(min(20, pv1.shape[0])):
        for k in pv1.iloc[r].keys():
            if k.startswith('time_'):
                assert pv1.iloc[r][k] == pv2.iloc[r][k]
            else:
                assert abs(pv1.iloc[r][k]-pv2.iloc[r][k]) < 10**(-9) or (pd.isna(pv1.iloc[r][k]) and pd.isna(pv2.iloc[r][k])), f"{k} at {pv1.iloc[r]['time_local']}"


def test_trino_interface_pivot_none():
    """

    """
    aggregations = [('defrost_temperature', 'nanfirst', 'defrost_temperature'),
                    ('exp_valve_opening', 'nanfirst', None),
                    ('air_on_temperature', 'nanfirst', None),
                    ('defrost_status', 'nanfirst', 'defrost_status'),
                    ('non_existent_semantic', 'nanfirst', 'none')
                    ]

    trino = TrinoInterface(user='test', hostname='ds-be-test-trino01.test-ds.lan', port='8080', logger=logger)
    pv1 = trino.pivot_data(device_uid='aa2f6a232172526471cf357af9481e996c9225ac', time_from=datetime(2020, 9, 1),
                            time_to=datetime(2020, 10, 1), interval=None, aggregations=aggregations)

    df = trino.read_device(device_uid='aa2f6a232172526471cf357af9481e996c9225ac', time_column='time_local',
                            time_from=datetime(2020, 9, 1), time_to=datetime(2020, 10, 1),
                            semantics=['defrost_temperature', 'exp_valve_opening', 'air_on_temperature', 'defrost_status'])
    pv2 = pd.pivot_table(df, index='time_local', columns='semantic', values='value').reset_index(drop=False)
    #pv2.columns = ['time_local', 'defrost_temperature', 'valve_first', 'valve_last', 'valve_nanfirst', 'valve_nanlast', 'defrost_status']
    pv2['none'] = np.nan

    assert pv2.shape[0] == pv1.shape[0]

    pv2.time_local = pv2.time_local.astype('datetime64[s]')
    pv1.time_local = pv1.time_local.astype('datetime64[s]')
    pv2.sort_values(by='time_local', inplace=True)
    pv1.sort_values(by='time_local', inplace=True)
    if 'time_utc' in pv1.columns:
        pv1.drop(columns=['time_utc'], inplace=True)
    if 'time_utc' in pv2.columns:
        pv2.drop(columns=['time_utc'], inplace=True)
    for r in range(20):
        for k in pv1.iloc[r].keys():
            if k.startswith('time_'):
                assert pv1.iloc[r][k] == pv2.iloc[r][k]
            else:
                assert abs(pv1.iloc[r][k]-pv2.iloc[r][k]) < 10**(-9) or (pd.isna(pv1.iloc[r][k]) and pd.isna(pv2.iloc[r][k]))






def test_trino_entity_details():
    trino = TrinoInterface(user='test', hostname='ds-be-test-trino01.test-ds.lan', port='8080', logger=logger)

    device_info = trino.get_entity_details('2d3d24c48c4035428a112de43271967ff943eb7b')
    assert device_info['entity_uid'] == '2d3d24c48c4035428a112de43271967ff943eb7b'
    assert device_info['entity_type'] == 'device'
    assert device_info['entity_id'] == '9732'
    assert device_info['source_system_id'] == 0
    assert device_info['entity_timezone'] == 'Europe/Paris'

    device_info = trino.get_entity_details('56479e26bb139e08665b4bd5da1a0de4a141205a')
    assert device_info['entity_uid'] == '56479e26bb139e08665b4bd5da1a0de4a141205a'
    assert device_info['source_system_id'] == 1

    device_info = trino.get_entity_details('0308ccac682cdeabcfbc26ece3480ea9f0bfe91d')
    assert device_info['entity_type'] == 'plant'
    assert device_info['tenant_id'] == 'MAN_HEOS'

    device_info = trino.get_entity_details('2d3d24c48c4035428a112de43271967ff943eb7a')
    assert device_info is None


def test_trino_project_details():
    trino = TrinoInterface(user='test', hostname='ds-be-test-trino01.test-ds.lan', port='8080', logger=logger)

    pj = trino.get_project_details(12)
    assert pj['project_id'] == 12
    assert pj['project_code'] == 'heos_baseline'
    assert pj['project_output_type'] == 'analysis'

    pj = trino.get_project_details(9999)
    assert pj is None