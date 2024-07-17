from pyarrow import flight
from pyarrow._flight import FlightUnavailableError, BasicAuth
import time
from carelds.common.logging import logutil
import base64


class HttpDremioClientAuthHandler(flight.ClientAuthHandler):

    def __init__(self, username, password):
        super().__init__()
        self.basic_auth = flight.BasicAuth(username, password)
        self.username = username
        self.password = password
        self.token = None

    def authenticate(self, outgoing, incoming):
        #outgoing.write(base64.b64encode(self.username + b':' + self.password))
        auth = self.basic_auth.serialize()
        outgoing.write(auth)
        self.token = incoming.read()

    def get_token(self):
        return self.token


class FlightQuery:

    def __init__(self, reader, logger):
        self.reader = reader    #<class 'pyarrow._flight.FlightStreamReader'>
        self.logger = logger

    def to_table(self):
        return self.reader.read_all()

    def to_pandas(self):
        return self.to_table().to_pandas()

    def to_dict(self):
        return self.to_table().to_pydict()


class FlightClient:

    def __init__(self, username, password, host, port=47470, logger=logutil.get_logger(log_name='flight', loglevel=logutil.DEBUG)):
        self.logger = logger
        for _ in range(1):
            try:
                self.client = flight.FlightClient(f'grpc+tcp://{host}:{port}')
                self.client.authenticate(HttpDremioClientAuthHandler(username.encode(), password.encode()))
                #self.client.wait_for_available(timeout=10)
                break
            except (FlightUnavailableError, Exception):
                self.logger.exception("Failed to connect to Dremio through Flight")
                raise

    def list_flights(self):
        return self.client.list_flights()

    def list_actions(self):
        return self.client.list_actions()

    def query(self, sql):
        info = self.client.get_flight_info(flight.FlightDescriptor.for_command(sql))
        return FlightQuery(self.client.do_get(info.endpoints[0].ticket), self.logger)

    def execute(self, sql):
        return self.query(sql)
