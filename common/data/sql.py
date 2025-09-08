from datetime import datetime, date, timedelta


def query_partitions(time_from: datetime,
                     time_to: datetime,
                     extend_hours: int = 13):
    """
    Build year and month lists covering the provided time interval
    Args:
        time_from: left time bound
        time_to: right time bound
        extend_hours: how many hours extend the time bounds to cover timezones, default 13

    Returns:

    """
    if isinstance(time_from, date):
        time_from = datetime(time_from.year, time_from.month, time_from.day)
    if isinstance(time_to, date):
        time_to = datetime(time_to.year, time_to.month, time_to.day)
    
    d = time_from - timedelta(hours = extend_hours)
    years, months = set(), set()
    while d < time_to + timedelta(hours = extend_hours):
        years.add(d.year)
        months.add(date(d.year, d.month, 1))
        d += timedelta(days = 1)
    return years, months


def read_device_semantics_query(
        device_uid: str,
        time_from: datetime,
        time_to: datetime,
        analysis: bool,
        time_column: str,
        semantics: list,
        subsemantics: bool,
        domain: str,
        system: int):
    """
    Private function that build the device read SQL queries
    Args:
        device_uid: device uid toread
        time_from: left time bound
        time_to: right time bound
        analysis: read also from analysis table
        time_column: time column (usually one between time_utc and time_local)
        semantics: optional list of semantics to read
        subsemantics: read also subsemantics
        domain: semantic domain
        system: explicit source system to improve performance

    Returns: read SQL query

    """
    years, months = query_partitions(time_from, time_to)
    
    if system in (1, 2):
        # Optimized for Systems 1 and 2
        years, months = query_partitions(time_from, time_to, extend_hours = 0)
        sql = f"""
                    SELECT
                        {"trim(concat(vs.semantic_id, ' ', COALESCE(vs.subdevice_id, '')))" if subsemantics else "vs.semantic_id"} semantic, "value", time_utc, time_local
                    FROM
                        data.data_{system}_month_{device_uid[0]} dt,
                        pg_ds.public.ds_variable_semantic vs
                    WHERE
                        concat('{system}_', CAST(model_id AS varchar), '_', model_variable_code) = vs.variable_id
                        and device = '{device_uid}'
                        and domain_id = '{domain}'
                        and {time_column} >= timestamp '{time_from.strftime("%Y-%m-%d %H:%M:%S")}'
                        and {time_column} < timestamp '{time_to.strftime("%Y-%m-%d %H:%M:%S")}'
                        and month in ({', '.join("date '" + str(m) + "'" for m in months)})
                        {f'''and semantic_id in ({','.join([f"'{s}'" for s in set(semantics)])})''' if isinstance(semantics, list) else ""}
                    UNION ALL
                    SELECT
                        {"trim(concat(vs.semantic_id, ' ', COALESCE(vs.subdevice_id, '')))" if subsemantics else "vs.semantic_id"} semantic, "value", time_utc, time_local
                    FROM
                        data.data_{system}_year_{device_uid[0]} dt,
                        pg_ds.public.ds_variable_semantic vs
                    WHERE
                        concat('{system}_', CAST(model_id AS varchar), '_', model_variable_code) = vs.variable_id
                        and device = '{device_uid}'
                        and domain_id = '{domain}'
                        and {time_column} >= timestamp '{time_from.strftime("%Y-%m-%d %H:%M:%S")}'
                        and {time_column} < timestamp '{time_to.strftime("%Y-%m-%d %H:%M:%S")}'
                        and year in ({', '.join((str(y) for y in years))})
                        {f'''and semantic_id in ({','.join([f"'{s}'" for s in set(semantics)])})''' if isinstance(semantics, list) else ""}
                """
        if analysis:
            sql += "UNION " + f"""
                        SELECT
                            {"trim(concat(vs.semantic_id, ' ', COALESCE(vs.subdevice_id, '')))" if subsemantics else "vs.semantic_id"} semantic, "value", time_utc, time_local
                        FROM
                            data.analysis_{system}_month dt,
                            pg_ds.public.ds_variable_semantic vs
                        WHERE
                            concat('1000_', CAST(model_id AS varchar), '_', model_variable_code) = vs.variable_id
                            and device = '{device_uid}'
                            and domain_id = '{domain}'
                            and {time_column} >= timestamp '{time_from.strftime("%Y-%m-%d %H:%M:%S")}'
                            and {time_column} < timestamp '{time_to.strftime("%Y-%m-%d %H:%M:%S")}'
                            and month in ({', '.join("date '" + str(m) + "'" for m in months)})
                            {f'''and semantic_id in ({','.join([f"'{s}'" for s in set(semantics)])})''' if isinstance(semantics, list) else ""}
                    """
        return sql
    
    return f"""
                SELECT
                    {"semantic_sd" if subsemantics else "semantic"} semantic, "value", time_utc, time_local
                FROM
                    data.{"data_sem_v" if system is None else "data_" + str(system) + "_sem_v"} --rmpro
                WHERE
                    device = '{device_uid}'
                    and domain_id = '{domain}'
                    and {time_column} >= timestamp '{time_from.strftime("%Y-%m-%d %H:%M:%S")}'
                    and {time_column} < timestamp '{time_to.strftime("%Y-%m-%d %H:%M:%S")}'
                    and year in ({', '.join((str(y) for y in years))})
                    and month in ({', '.join("date '" + str(m) + "'" for m in months)})
                    {'and not analysis' if not analysis else ''}
                    {f'''and semantic in ({','.join([f"'{s}'" for s in set(semantics)])})''' if isinstance(semantics, list) else ""}
                ORDER BY
                    {time_column}
            """


def read_device_semantics_tsdb_query(device,
                                     supervisor,
                                     time_from: datetime,
                                     time_to: datetime,
                                     time_column: str,
                                     semantics: list,
                                     domain: str = None,
                                     live: bool = False,
                                     **kwargs):
    """
    Private function that build the device read SQL queries
    Args:
        device: device to read (int ID or str UID)
        supervisor: supervisor to read (int ID or str UID)
        time_from: left time bound
        time_to: right time bound
        time_column: time column (usually one between time_utc and time_local)
        semantics: optional list of semantics to read
        domain: semantic domain
        live: if True, query the live timescale database. You must provide integer device_id and supervisor_id parameters

    Returns: read SQL query
    """
    years, months = query_partitions(time_from, time_to, extend_hours = 0)
    params = dict()
    
    where_clauses = list()
    if device is not None:
        if isinstance(device, int):
            where_clauses.append(f"device_id = :device")
        elif isinstance(device, str):
            where_clauses.append(f"device_uid = :device")
        params['device'] = device
    if supervisor is not None:
        if isinstance(supervisor, int):
            where_clauses.append(f"supervisor_id = :supervisor")
        elif isinstance(supervisor, str):
            where_clauses.append(f"supervisor_uid = :supervisor")
        params['supervisor'] = supervisor
    if domain is not None:
        where_clauses.append(f"domain_id = :domain")
        params['domain'] = domain
    if isinstance(semantics, list):
        where_clauses.append(f"""semantic in ({", ".join(["'" + s + "'" for s in semantics])})""")
        # where_clauses.append("semantic in :semantics")
        # params['semantics'] = tuple([str(s) for s in semantics])

    where_clauses.append(f"{time_column} >= timestamp :time_from")
    params['time_from'] = time_from
    where_clauses.append(f"{time_column} < timestamp :time_to")
    params['time_to'] = time_to
    if not live:
        where_clauses.append(f"""month in ({', '.join("date '" + str(m) + "'" for m in months)})""")
    where_clauses = '\nAND '.join(where_clauses)
    
    sql = f"""
            SELECT
                model_variable_code, semantic, subdevice, "value", time_utc, time_local
            FROM
                data_tsdb.data_sem_v --tsdb
            WHERE
                {where_clauses}
            ORDER BY
                6
        """
    
    return sql, params


def read_device_tsdb_query(device,
                           supervisor,
                           time_from: datetime,
                           time_to: datetime,
                           time_column: str,
                           live: bool = False,
                           **kwargs):
    """
    Private function that build the device read SQL queries
    Args:
        device: device to read (int ID or str UID)
        supervisor: supervisor to read (int ID or str UID)
        time_from: left time bound
        time_to: right time bound
        time_column: time column (usually one between time_utc and time_local)

    Returns: read SQL query
    """
    years, months = query_partitions(time_from, time_to, extend_hours = 0)
    params = dict()
    
    where_clauses = list()
    if device is not None:
        if isinstance(device, int):
            where_clauses.append(f"device_id = :device")
        elif isinstance(device, str):
            where_clauses.append(f"device_uid = :device")
        params['device'] = device
    if supervisor is not None:
        if isinstance(supervisor, int):
            where_clauses.append(f"supervisor_id = :supervisor")
        elif isinstance(supervisor, str):
            where_clauses.append(f"supervisor_uid = :supervisor")
        params['supervisor'] = supervisor
    
    where_clauses.append(f"{time_column} >= timestamp :time_from")
    params['time_from'] = time_from
    where_clauses.append(f"{time_column} < timestamp :time_to")
    params['time_to'] = time_to
    if not live:
        where_clauses.append(f"""month in ({', '.join("date '" + str(m) + "'" for m in months)})""")
    where_clauses = '\nAND '.join(where_clauses)
    
    sql = f"""
            SELECT
                model_variable_code, "value", time_utc, time_local
            FROM
                {'data_tsdb.live_data_all_v' if live else 'data_tsdb.data_all_v'} --tsdb
            WHERE
                {where_clauses}
            ORDER BY
                4
        """
    
    return sql, params


def read_device_query(device_uid: str, time_from, time_to, analysis, time_column, system):
    """
    Build query to read device from Presto/Trino
    Args:
        device_uid:
        time_from:
        time_to:
        analysis:
        time_column:
        system:

    Returns:

    """
    years, months = query_partitions(time_from, time_to)
    return f"""
                SELECT
                    model_variable_code, "value", time_utc, time_local
                FROM
                    data.{"data_sem_v" if system is None else "data_" + str(system) + "_sem_v"} --rmpro
                WHERE
                    device = '{device_uid}'
                    and {time_column} >= timestamp '{time_from}'
                    and {time_column} < timestamp '{time_to}'
                    and year in ({', '.join((str(y) for y in years))})
                    and month in ({', '.join("date '" + str(m) + "'" for m in months)})
                    {'and not analysis' if not analysis else ''}
                ORDER BY
                    {time_column}
            """
