from carelds.common.logging.logutil import get_logger
from carelds.common.connectors.s3_connector import S3Connector
import pandas as pd
import os
import secrets
import numpy as np
from datetime import datetime, timedelta

logger = get_logger('test_s3')

"""
    S3 TESTS
"""
def test_bucket_exists():
    s3 = S3Connector(IAM=True)
    assert s3.check_for_bucket('carel-ds-tera-test')


def test_s3_write_binary():
    data = os.urandom(1024)
    s3 = S3Connector(IAM=True)
    s3.write_binary(data, 'carel-ds-tera-test', 'test/s3/test_s3_write_binary')
    data_get = s3.read_binary('carel-ds-tera-test', 'test/s3/test_s3_write_binary')
    assert data == data_get


def test_s3_write_string():
    s = secrets.token_urlsafe(1024)
    s3 = S3Connector(IAM=True)
    s3.write_string(s, 'carel-ds-tera-test', 'test/s3/test_s3_write_string')
    s_get = s3.read_string('carel-ds-tera-test', 'test/s3/test_s3_write_string')
    assert s == s_get


def test_s3_write_parquet():
    df = pd.DataFrame({'t': np.arange(datetime(2020, 1, 1), datetime(2020, 1, 2), timedelta(minutes=1)),
                       'x': np.random.randint(100, size=(1440,)),
                       'y': np.random.random(size=(1440,)).flatten()})
    s3 = S3Connector(IAM=True)
    s3.write_parquet(df, 'carel-ds-tera-test', 'test/s3/test_s3_write_parquet', pq_options=dict(index=False))
    df_get = s3.read_parquet('carel-ds-tera-test', 'test/s3/test_s3_write_parquet')
    assert df_get.iloc[100].x == df.iloc[100].x and df_get.iloc[200].y == df.iloc[200].y


def test_s3_move_object():
    data = os.urandom(1024)
    s3 = S3Connector(IAM=True)
    s3.write_binary(data, 'carel-ds-tera-test', 'test/s3/test_s3_move_object')
    s3.move_object('carel-ds-tera-test', 'test/s3/test_s3_move_object', 'test/s3/test_s3_move_object_copy')
    data_get = s3.read_binary('carel-ds-tera-test', 'test/s3/test_s3_move_object_copy')
    assert data == data_get
