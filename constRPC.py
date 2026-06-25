import os


def _env_int(name, default):
	value = os.getenv(name)
	if value is None:
		return default
	try:
		return int(value)
	except ValueError:
		return default


OK       = '1'
ADD      = '2'
APPEND   = '3'
GETVALUE = '4'
CREATE   = '5'
STOP     = '6'

# Remote endpoint used by DBClient stub calls.
HOSTS = os.getenv('RPC_SERVER_HOST', '127.0.0.1')
PORTS = _env_int('RPC_SERVER_PORT', 50004)

# Listening ports for the two client processes.
PORTC1 = _env_int('RPC_CLIENT1_PORT', 50053)
PORTC2 = _env_int('RPC_CLIENT2_PORT', 50054)

# Network addresses used when one process connects to another client.
HOSTC1 = os.getenv('RPC_CLIENT1_HOST', '127.0.0.1')
HOSTC2 = os.getenv('RPC_CLIENT2_HOST', '127.0.0.1')

# Bind interfaces for local listeners (server and clients).
SERVER_BIND_HOST = os.getenv('RPC_SERVER_BIND_HOST', '0.0.0.0')
CLIENT_BIND_HOST = os.getenv('RPC_CLIENT_BIND_HOST', '0.0.0.0')
