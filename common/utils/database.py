import pandas as pd
from sqlalchemy.sql import text, expression
from pyarrow.csv import read_csv, ConvertOptions
import sqlalchemy
import pyarrow as pa

import json
import io
import psycopg2
import re

def export_postgres_table(dbsession, how, table, columns=None, filter=None, lf='\n', html_color=False):
    """
    Export database table

    Args:
        dbsession: Database sqlalchemy session
        how: Export as 'update' or 'upsert' or 'insert'
        table: The table full name (schema.table)
        columns: list of columns to export
        filter: WHERE clauses (omit 'WHERE' keyword)
        lf: line feed to add after each command, default is '\n'

    Returns:
        SQL update/upsert commands

    """
    if '.' in table:
        schema, table = table.split('.')[0], table.split('.')[1]
    else:
        schema, table = 'public', table

    pkey = dbsession.execute(f'''
        SELECT a.attname, i.indisprimary
        FROM   pg_index i
        JOIN   pg_attribute a ON a.attrelid = i.indrelid
                             AND a.attnum = ANY(i.indkey)
        WHERE  i.indrelid = '{schema}.{table}'::regclass
        AND    i.indisprimary;

    ''')

    cols = dbsession.execute(f'''
        select column_name, data_type
        from information_schema.columns 
        where table_name = '{table}' and table_schema='{schema}';
    ''')

    pkcols = [k[0] for k in pkey]
    cols = [{'col_name': col['column_name'], 'col_type': col['data_type'], 'pkey': col['column_name'] in pkcols} for col in cols]
    vcols = [c['col_name'] for c in cols]


    if columns is not None:
        keep_columns = [c for c in columns if c in vcols]
    else:
        keep_columns = vcols

    if len(keep_columns) < 1:
        return 'No columns to extract'

    rows = dbsession.execute(f'''
        SELECT * FROM {schema}.{table} {'WHERE ' + filter if filter is not None else ''}
    ''')

    if html_color:
        _update = '<span style="color: darkorange;">UPDATE</span>'
        _set = '<span style="color: darkorange;">SET</span>'
        _insert = '<span style="color: darkorange;">INSERT INTO</span>'
        _values = '<span style="color: darkorange;">VALUES</span>'
        _conflict = '<span style="color: darkorange;">ON CONFLICT</span>'
        _do = '<span style="color: darkorange;">DO</span>'
        _where = '<span style="color: darkorange;">WHERE</span>'
    else:
        _update = 'UPDATE'
        _set = 'SET'
        _insert = 'INSERT INTO'
        _values = 'VALUES'
        _conflict = 'ON CONFLICT'
        _do = 'DO'
        _where = 'WHERE'

    null_literal = expression.null() if sqlalchemy.__version__[:3] == '1.3' else None
    update_strings = list()
    for r in rows:
        if how == 'update':
            stmt = f'''{_update} {schema}.{table} {_set} {', '.join([f"""{vc} = :{vc}""" for vc in vcols if  vc in keep_columns])} {_where} {' AND '.join([f"""{pk} = :{pk}""" for pk in pkcols])}'''
        elif how == 'upsert':
            stmt = f'''{_insert} {schema}.{table} ({', '.join([vc['col_name'] for vc in cols])}) {_values}
                ({', '.join([':' + vc['col_name'] for vc in cols])}) 
                {_conflict} ({', '.join([pk['col_name'] for pk in cols if pk['pkey']])}) {_do}                 
                {_update} {_set} {', '.join([f"""{vc} = :{vc}""" for vc in vcols if  vc in keep_columns])}'''
        elif how == 'insert':
            stmt = f'''{_insert} {schema}.{table} ({', '.join([vc['col_name'] for vc in cols])}) {_values} ({', '.join([':' + vc['col_name'] for vc in cols])}) '''
        else:
            raise ValueError(f'Unknown export mode: {how}')

        stmt = text(stmt).bindparams(
            **{vc['col_name']: null_literal if r[vc['col_name']] is None
                else json.dumps(r[vc['col_name']]) if vc['col_type'] == 'jsonb'
                else r[vc['col_name']].strftime('%Y-%m-%d %H:%M:%S') if vc['col_type'].startswith('timestamp')
                else str(r[vc['col_name']]) if vc['col_type'] == 'date'
                else str(r[vc['col_name']]) if vc['col_type'] == 'uuid'
                else f"{{{','.join(r[vc['col_name']])}}}" if vc['col_type'] == 'ARRAY'
                else r[vc['col_name']]
            for vc in cols if not vc['pkey'] and (vc['col_name'] in keep_columns or how == 'upsert')},
            **{vc['col_name']: json.dumps(r[vc['col_name']]) if vc['col_type'] == 'jsonb'
                else r[vc['col_name']].strftime('%Y-%m-%d %H:%M:%S') if vc['col_type'].startswith('timestamp')
                else str(r[vc['col_name']]) if vc['col_type'] == 'date'
                else str(r[vc['col_name']]) if vc['col_type'] == 'uuid'
                else r[vc['col_name']]
            for vc in cols if vc['pkey']}
        )

        update_strings.append(str(stmt.compile(dbsession.get_bind(), compile_kwargs={"literal_binds": True})) + ';')

    return lf.join(update_strings)


def read_sql_csv(query: str,
                 db_engine: sqlalchemy.engine.Engine = None,
                 db_connection: psycopg2.extensions.connection = None) -> io.BytesIO:
    """
    Read from database using copy_expert on a raw connection, returns CSV data
    Args:
        query: query to execute
        db_engine: database engine to use, if db_connection is None
        db_connection: database connection to use

    Returns:

    """
    copy_sql = "COPY ({query}) TO STDOUT WITH CSV {head}".format(
       query=query, head="HEADER"
    )
    if db_connection is None:
        db_connection = db_engine.raw_connection()
    cur = db_connection.cursor()
    store = io.BytesIO()
    cur.copy_expert(copy_sql, store)
    store.seek(0)
    return store


def read_sql_pandas(query: str,
                    db_engine: sqlalchemy.engine.Engine = None,
                    db_connection: psycopg2.extensions.connection = None,
                    schema: dict = None) -> pd.DataFrame:
    """
    Read from database using copy_expert on a raw connection, returns pandas.DataFrame
    Args:
        query: query to execute
        db_engine: database engine to use, if db_connection is None
        db_connection: database connection to use
        schema: Pandas schema for column dtypes, is passed as "dtype" argument in pandas.read_csv function

    Returns:

    """
    store = read_sql_csv(query, db_engine, db_connection)
    return pd.read_csv(store, dtype=schema)


def read_sql_arrow(query: str,
                   db_engine: sqlalchemy.engine.Engine = None,
                   db_connection: psycopg2.extensions.connection = None,
                   schema: pa.Schema = None) -> pa.Table:
    """
    Read from database using copy_expert on a raw connection, returns pyarrow.Table
    Args:
        query: query to execute
        db_engine: database engine to use, if db_connection is None
        db_connection: database connection to use
        schema: Arrow schema for column types, is passed as "ConvertOptions.column_types" in pyarrow.csv.read_csv function

    Returns:

    """
    csv = read_sql_csv(query, db_engine, db_connection)
    if schema is None:
        return pa.csv.read_csv(csv)
    else:
        return pa.csv.read_csv(csv, convert_options=pa.csv.ConvertOptions(column_types=schema))


def parse_database_connection_string(connstring: str):
    matcher = re.compile("(?P<url_schema>[a-z0-9]+)://(?P<user_name>[a-zA-Z0-9\-\_]+)(:(?P<user_pass>[^@]+)@|@)(?P<url_host>[a-zA-Z0-9\-\_\.]+)(:(?P<port>[0-9]+)|)/(?P<db_catalog>[a-zA-Z0-9]+)/(?P<db_schema>[a-zA-Z0-9]+)")
    m = matcher.match(connstring)
    if m is not None:
        return {
            'url_schema': m.group('url_schema'),
            'user_name': m.group('user_name'),
            'user_pass': m.group('user_pass'),
            'url_host': m.group('url_host'),
            'port': m.group('port'),
            'db_catalog': m.group('db_catalog'),
            'db_schema': m.group('db_schema'),
            'port': m.group('port')
        }
    matcher = re.compile("(?P<url_schema>[a-z0-9]+)://(?P<user_name>[a-zA-Z0-9\-\_]+)(:(?P<user_pass>[^@]+)@|@)(?P<url_host>[a-zA-Z0-9\-\_\.]+)(:(?P<port>[0-9]+)|)/*")
    m = matcher.match(connstring)
    if m is not None:
        return {
            'url_schema': m.group('url_schema'),
            'user_name': m.group('user_name'),
            'user_pass': m.group('user_pass'),
            'url_host': m.group('url_host'),
            'port': m.group('port'),
            'db_catalog': None,
            'db_schema': None,
            'port': m.group('port')
        }
    return None


def build_database_connection_string(url_schema:str, user_name:str, user_pass:str, url_host:str, port:int, db_catalog:str = None, **kwargs):
    user_pass = f':{user_pass}' if user_pass is not None else ''
    connstring = f'{url_schema}://{user_name}{user_pass}@{url_host}:{port}'
    if db_catalog is not None:
        connstring += f'/{db_catalog}'
    return connstring