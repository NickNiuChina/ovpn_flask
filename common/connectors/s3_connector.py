"""
    Luca Demo - 26/10/18
"""
import warnings
warnings.warn("This module is deprecated, use 'carelds.common.s3.connector' instead", DeprecationWarning, stacklevel=2)

import boto3
from botocore.exceptions import ClientError
import tempfile
import gzip
import pickle
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryFile
import pyarrow.parquet as pq
import pyarrow as pa
import pandas as pd
from typing import Union
import re

class S3Connector:
    """
        Helper class to manage Amazon S3 connection and provide useful shortcuts to write and read strings and bytes
    """
    
    def __init__(self,
                 s3_endpoint=None,
                 s3_port=None,
                 s3_login=None,
                 s3_password=None,
                 s3_region=None,
                 s3_token=None,
                 IAM=None,
                 profile=None,
                 credentials=None,
                 logger=None):
        """
            Args:
                s3_endpoint :obj:`str`, default None
                    S3 endpoint, if None assume Amazon S3 is to be used
                s3_port :obj:`int` or :obj:`str`, default None
                    S3 connection port, if None assume Amazon S3 is to be used
                s3_login :obj:`str`, default None
                    S3 login id, if None assume IAM = True (error if IAM is False)
                s3_password :obj:`str`, default None
                    S3 login secret key, if None assume IAM = True (error if IAM is False)
                s3_region :obj:`str`, default None
                    S3 region, if None assume IAM = True (error if IAM is False)
                IAM :obj:`bool`, default False
                    if True, assumes that the S3 connection should use IAM authentication, all other arguments are ignored
                logger :obj:`logging.Logger`
                    logger object, default None (no logs)
                    
        """
        self.logger = logger

        if IAM:
            # IAM has highest priority
            if self.logger is not None:
                self.logger.debug('S3 connector with IAM authentication')
            self.session = boto3.session.Session(region_name=s3_region) #test if IAM works, if not, this instruction will raise an exception
        elif profile:
            # If a profile is provided
            if self.logger is not None:
                self.logger.debug('S3 connector with profile ("{}") authentication'.format(profile))
            self.session = boto3.session.Session(profile_name=profile)  #test if profile works, if not, this instruction will raise an exception
        elif credentials:
            # Credentials provided (es. sts)
            if self.logger is not None:
                self.logger.debug('S3 connector with provided credentials object')
            self.session = boto3.session.Session(aws_access_key_id=credentials['AccessKeyId'], aws_secret_access_key=credentials['SecretAccessKey'], aws_session_token=credentials['SessionToken'])
        else:
            # try with login/password
            assert s3_login and s3_password
            if s3_endpoint is None or s3_port is None:
                self.s3_login = s3_login
                self.s3_password = s3_password
                self.s3_minio = False
                self.s3_session_token = s3_token
                if self.logger is not None:
                    self.logger.debug('S3 connector with user/key authentication')
            else:                
                self.s3_endpoint = s3_endpoint
                self.s3_port = int(s3_port)     
                self.s3_login = s3_login
                self.s3_password = s3_password
                self.s3_minio = True
                if self.logger is not None:
                    self.logger.debug('S3 connector to Minio {}:{} with user/key authentication'.format(s3_endpoint, s3_port))
        
        self.IAM = IAM
        self.profile = profile
        self.credentials = credentials
        self.s3_region = s3_region
        self.client = self.get_client()
        self.resource = self.get_resource()

        self.urlre = re.compile(r's3://(?P<bucket>[a-zA-Z\-0-9]+)/(?P<path>.+)')


    @staticmethod
    def _bucket_key_from_URI(s3_uri):
        m = S3Connector.urlre.match(s3_uri)
        if m is None:
            raise ValueError(f'Invalid "s3_key" S3 path')
        s3_bucket, s3_key = m.groups()
        return s3_bucket, s3_key

    
    def get_resource(self):
        """
            Get S3 boto3 resource
        """
        if self.IAM or self.profile or self.credentials:
            return self.session.resource(service_name='s3')
        else:
            if self.s3_minio:
                return boto3.resource('s3', 
                                      endpoint_url=':'.join([self.s3_endpoint, str(self.s3_port)]),
                                      region_name=self.s3_region,
                                      aws_access_key_id=self.s3_login,
                                      aws_secret_access_key=self.s3_password)
            else:
                return boto3.resource('s3', 
                                      region_name=self.s3_region,
                                      aws_access_key_id=self.s3_login,
                                      aws_secret_access_key=self.s3_password,
                                      aws_session_token=self.s3_session_token)
                    
    def get_client(self):
        """
            Get S3 boto3 client
        """
        if self.IAM or self.profile or self.credentials:
            return self.session.client('s3')
        else:
            if self.s3_minio:
                return boto3.client('s3', 
                                      endpoint_url=':'.join([self.s3_endpoint, str(self.s3_port)]),
                                      region_name=self.s3_region,
                                      aws_access_key_id=self.s3_login,
                                      aws_secret_access_key=self.s3_password)
            else:
                return boto3.client('s3', 
                                      region_name=self.s3_region,
                                      aws_access_key_id=self.s3_login,
                                      aws_secret_access_key=self.s3_password,
                                      aws_session_token = self.s3_session_token)
    

    def check_for_bucket(self, bucket_name):
        """
            Check if a bucket exists
            
            Args:
                bucket_name :obj:`str`
                    name of the bucket to check for
            
            Returns:
                :obj:`bool`
                    True if specified bucket exists, False otherwise
        """
        return bucket_name in [bucket.name for bucket in self.list_buckets()]

    def check_for_key(self, bucket_name, key):
        """
            Check if a key exists in the specified bucket

            Args:
                bucket_name :obj:`str`
                    name of the bucket to check for
                key :obj:`str`
                    resource key

            Returns:
                :obj:`bool`
                    True if specified bucket-key pair exists, False otherwise
        """
        if self.check_for_bucket(bucket_name):
            try:
                obj = self.get_resource().Object(bucket_name, key)
                obj.load()
                obj.get()['Body'].read()
            except:
                return False
            return True
        return False

    def list_buckets(self):
        """
            Lists buckets in s3

            Returns:
                :obj:`boto3.resources.collection.s3.bucketsCollection`
                    Collection of buckets
        """
        return self.get_resource().buckets.all()

    def write_string_stream(self, string_stream, s3_bucket, s3_key, encoding='utf-8', compress=False):
        """
            Writes a string stream on S3

            Args:
                string_stream :obj:`io.StringIO`
                    String stream to write
                s3_bucket :obj:`str`
                    Bucket name
                s3_key :obj:`str`
                    Key name
                encoding :obj:`str`
                    String encoding, default utf-8
                compress :obj:`bool`
                    If True, compress the string with gzip
        """
        if compress:
            with tempfile.TemporaryFile('w+b') as tbf:
                with gzip.GzipFile(mode='wb', fileobj=tbf) as gzf:
                    gzf.write(string_stream.read().encode(encoding))
                tbf.seek(0)
                self.get_client().upload_fileobj(tbf, s3_bucket, s3_key)
        else:
            filelike_buffer = BytesIO(string_stream.read().encode(encoding))
            self.get_client().upload_fileobj(filelike_buffer, s3_bucket, s3_key)

    def write_string(self, string, s3_bucket, s3_key, encoding='utf-8', compress=False):
        """
            Writes a string on S3

            Args:
                string :obj:`str`
                    String to write
                s3_bucket :obj:`str`
                    Bucket name
                s3_key :obj:`str`
                    Key name
                encoding :obj:`str`
                    String encoding, default utf-8
                compress :obj:`bool`
                    If True, compress the string with gzip
        """
        self.write_string_stream(StringIO(string), s3_bucket, s3_key, encoding, compress)

    def read_string(self, s3_bucket, s3_key, encoding='utf-8', compress=False):
        """
            Reads a string from S3

            Args:
                s3_bucket :obj:`str`
                    Bucket name
                s3_key :obj:`str`
                    Key name
                encoding :obj:`str`
                    String encoding, default utf-8
                compress :obj:`bool`
                    If True, try to decompress with gzip
            Returns:
                :obj:`str`
                    String from S3
        """
        try:
            if compress:
                with TemporaryFile('w+b') as tbf:
                    self.get_client().download_fileobj(s3_bucket, s3_key, tbf)
                    tbf.seek(0)
                    with gzip.GzipFile(mode='rb', fileobj=tbf) as gzf:
                        return gzf.read().decode(encoding)
            else:
                obj = self.get_resource().Object(s3_bucket, s3_key)
                obj.load()
                return obj.get()['Body'].read().decode(encoding)
        except Exception as e:
            if (e.args[0].count('(404)') > 0):
                if self.logger is not None:
                    self.logger.error('Key {} not found in bucket {}'.format(s3_key, s3_bucket))
                return None
            else:
                raise

    def write_file(self, path: Union[str, Path], s3_bucket: str, s3_key: str):
        """

        """
        self.get_client().upload_file(str(path), s3_bucket, s3_key)
        if self.logger is not None:
            self.logger.debug(f"Written to s3://{s3_bucket}/{s3_key}")

    def write_binary(self, buffer, s3_bucket, s3_key, metadata=None):
        """
            Writes a binary buffer to S3

            Args:
                data : :obj:`BytesIO` or binary buffer implementing 'read', or :obj:'bytes'
                    Binary buffer to write
                s3_bucket :obj:`str`
                    Bucket name
                s3_key :obj:`str`
                    Key name
        """
        if isinstance(buffer, bytes):
            buffer = BytesIO(buffer)
        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError('Invalid metadata object, must be a dict')

        self.client.upload_fileobj(buffer, s3_bucket, s3_key,
                                   ExtraArgs={'Metadata': metadata} if metadata is not None else {})
        if self.logger is not None:
            self.logger.debug(f"Written to s3://{s3_bucket}/{s3_key}")

    def read_binary(self, s3_bucket, s3_key):
        """
            Reads raw binary from S3, return as bytes

            Args:
                s3_bucket :obj:`str`
                    Bucket name
                s3_key :obj:`str`
                    Key name
            Returns:
                :obj:`bytes`

        """
        try:
            obj = self.client.get_object(Bucket=s3_bucket, Key=s3_key)
        except ClientError:
            return None
        
        return obj['Body'].read()

    def read_file(self, s3_bucket, s3_key):
        """
            Reads raw binary from S3, return as readable stream

            Args:
                s3_bucket :obj:`str`
                    Bucket name
                s3_key :obj:`str`
                    Key name
            Returns:
                :obj:`bytes`

        """
        return self.client.get_object(Bucket=s3_bucket, Key=s3_key)['Body']

    def read_parquet(self, s3_bucket: str, s3_key: str, output:str = 'pandas', **kwargs):
        """
            Read parquet file from S3

            Args:
                s3_bucket: S3 Bucket name
                s3_key: S3 key
                output: output type, either 'pandas' or 'arrow'
                **kwargs: arguments passed to reader function
            Returns:
                The data as Pandas DataFrame or PyArrow Table

        """
        if output not in ['pandas', 'arrow']:
            raise ValueError(f'Unknown output mode: {output}')
        
        if output == 'arrow':
            return pq.read_table(pa.BufferReader(self.read_binary(s3_bucket, s3_key)), **kwargs)
        else:
            return pd.read_parquet(BytesIO(self.read_binary(s3_bucket, s3_key)), **kwargs)

    def read_csv(self, s3_bucket, s3_key, pd_options={}):
        """
            Read CSV file from S3.

            Args:
                s3_bucket :obj:`str`
                    Bucket name
                s3_key :obj:`str`
                    Key name
            Returns:
                The data as Pandas DataFrame or PyArrow Table

        """
        buf = self.read_string(s3_bucket, s3_key)
        return pd.read_csv(StringIO(buf), **pd_options)

    def write_parquet(self, df, s3_bucket, s3_key, pq_options={}, metadata=None):
        """
        Write a pandas dataframe to S3 as parquet file

        Args:
            df: Dataframe object
            s3_bucket: destination bucket
            s3_key: destination path
            pq_options: kwargs to pass to pandas.DataFrame.to_parquet
        """
        assert isinstance(df, pd.DataFrame)
        # write parquet to Bytes buffer
        df_buf = BytesIO()
        df.to_parquet(df_buf, **pq_options)
        df_buf.seek(0)

        # write the buffer to S3
        self.write_binary(df_buf, s3_bucket, s3_key, metadata=metadata)

    def write_object(self, obj, s3_bucket, s3_key, metadata=None):
        """
            Serialize and writes an object to S3

            Args:
                obj : serializable object
                    Binary buffer to write
                s3_bucket :obj:`str`
                    Bucket name
                s3_key :obj:`str`
                    Key name
        """
        self.write_binary(BytesIO(pickle.dumps(obj)), s3_bucket, s3_key, metadata=metadata)

    def read_object(self, s3_bucket, s3_key):
        """
            Reads and deserialize and object from S3

            Args:
                s3_bucket :obj:`str`
                    Bucket name
                s3_key :obj:`str`
                    Key name
            Returns:
                the deserialized object

        """
        obj = self.get_resource().Object(s3_bucket, s3_key)
        obj.load()
        return pickle.loads(obj.get()['Body'].read())

    def list_objects(self, s3_bucket, prefix):
        """
            List all objects in the given bucket and prefix
        """
        kwargs = {'Bucket': s3_bucket, 'Prefix': prefix, 'MaxKeys': 500}
        client = self.get_client()
        objects = list()

        while True:
            resp = client.list_objects_v2(**kwargs)
            objects.extend(resp.get('Contents', list()))
            try:
                kwargs['ContinuationToken'] = resp['NextContinuationToken']
            except KeyError:
                break

        return objects

    def copy_object(self, s3_key_source: str, s3_key_dest: str, s3_bucket_source: str = None, s3_bucket_dest: str = None) -> None:
        """
        Copy S3 object to another location
        Args:
            s3_key_source: source path. If a fully qualified s3:// URL is provided, then s3_bucket_source is extracted
            s3_key_dest: destination path. If a fully qualified s3:// URL is provided, then s3_bucket_source is extracted
            s3_bucket_source: source bucket, required if s3_key_source is not fully qualified s3:// URL
            s3_bucket_dest: destination bucket, required if s3_key_dest is not fully qualified s3:// URL

        Returns: None

        """
        if s3_bucket_source is None:
            m = self.urlre.match(s3_key_source)
            if m is not None:
                s3_bucket_source = m.groups[0]
                s3_key_source = m.groups[1]
            else:
                raise ValueError('s3_key_source must be a fully qualified s3:// url when s3_bucket_source is None')
        if s3_bucket_dest is None:
            m = self.urlre.match(s3_key_dest)
            if m is not None:
                s3_bucket_dest = m.groups[0]
                s3_key_dest = m.groups[1]
            else:
                raise ValueError('s3_key_dest must be a fully qualified s3:// url when s3_bucket_dest is None')

        bucket = self.resource.Bucket(s3_bucket_dest)
        bucket.copy(CopySource=dict(Bucket=s3_bucket_source, Key=s3_key_source), Key=s3_key_dest)

    def move_object(self, s3_bucket, s3_key_source, s3_key_dest):
        self.copy_object(s3_bucket, s3_key_source, s3_key_dest)
        self.delete_object(s3_bucket, s3_key_source)

    def delete_object(self, s3_bucket, s3_key):
        return self.get_client().delete_object(Bucket=s3_bucket, Key=s3_key)

    def delete_prefix(self, s3_bucket, s3_prefix):
        return self.get_resource().Bucket(s3_bucket).objects.filter(Prefix=s3_prefix).delete()

    def clean_s3_prefix(self, s3_bucket, s3_prefix):
        """
        Helper function that removes all s3 objects given a prefix
        """
        try:
            objects_to_delete = self.list_objects(s3_bucket=s3_bucket, prefix=str(Path(s3_prefix)))
            if len(objects_to_delete) > 0:
                self.delete_prefix(s3_bucket=s3_bucket, s3_prefix=str(Path(s3_prefix)))
        except:
            raise
        return