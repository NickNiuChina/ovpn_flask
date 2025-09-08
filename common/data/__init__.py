import os
from carelds.common.data.master import MasterDataInterface
from carelds.common.data.presto import PrestoInterface
from carelds.common.data.trino import TrinoInterface
from carelds.common.data.interface import DataInterface
from carelds.common.logging.logutil import get_logger


def get_default_data_interface(logger=get_logger('data_interface'), **kwargs) -> DataInterface:
    """
    Builds a DataInterface object either PrestoInterface or TrinoInterface depending on environment variables
    Args:
        logger: logger instance to pass to interface object

    Returns: data interface object

    """
    if str(os.environ.get('DS_DATA_INTERFACE', '')) == 'dremio':
        raise NotImplementedError('Dremio interface is not working in this "common" release')
    elif str(os.environ.get('DS_DATA_INTERFACE', '')) == 'presto':
        presto_if = PrestoInterface(user=os.environ.get('DS_PRESTO_USER', 'nouser'),
                                    hostname=os.environ.get('DS_PRESTO_HOST', 'localhost'),
                                    port=int(os.environ.get('DS_PRESTO_PORT', '8080')),
                                    logger=logger,
                                    **kwargs
                                    )
        logger.debug(f"Data interface ready to use: PrestoSQL")
        return presto_if
    elif str(os.environ.get('DS_DATA_INTERFACE', '')) == 'trino':
        trino_if = TrinoInterface(user=os.environ.get('DS_TRINO_USER', 'nouser'),
                                  hostname=os.environ.get('DS_TRINO_HOST', 'localhost'),
                                  port=int(os.environ.get('DS_TRINO_PORT', '8080')),
                                  logger=logger,
                                  **kwargs
                                  )
        logger.debug(f"Data interface ready to use: TrinoDB")
        return trino_if
    else:
        raise ValueError(f"Invalid or missing DS_DATA_INTERFACE value: {os.environ.get('DS_DATA_INTERFACE', '')}")


def get_presto_interface(**kwargs) -> PrestoInterface:
    """
    Alias of PrestoInterface constructor
    Args:
        **kwargs: arguments for PrestoInterface constructor

    Returns: PrestoInterface object

    """
    return PrestoInterface(**kwargs)


def get_trino_interface(**kwargs) -> TrinoInterface:
    """
    Alias of TrinoInterface constructor
    Args:
        **kwargs: arguments for TrinoInterface constructor

    Returns: TrinoInterface object

    """
    return TrinoInterface(**kwargs)


def get_masterdata_interface(connection_uri: str = None, test_connection: bool = True, **kwargs) -> MasterDataInterface:
    """
    Return an interface to Master Database

    Args:
        connection_uri: database connection URI, if None is provided, read DS_MASTER_DATABASE envvar
        test_connection: if True (default) check connection and raise error if database is not ready
        **kwargs: additional arguments to pass down to sqlalchemy.create_engine

    Returns: a connection to the master datatabase

    """
    return MasterDataInterface(connection_uri or os.environ['DS_MASTER_DATABASE'], test_connection = test_connection, **kwargs)
