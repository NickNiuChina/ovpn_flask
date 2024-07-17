# 200

# 400
INVALID_PARAMETER_VALUE = lambda parameter_name: ({'error': 'invalid_request', 'error_description': f'Invalid value for parameter \'{parameter_name}\''}, 400)
INVALID_REQUEST = lambda message: ({'error': 'invalid_request', 'error_description': f'Invalid request: {message}'}, 400)
INVALID_JSON_VALUE = lambda parameter_name: ({'error': 'invalid_request', 'error_description': f'Invalid value in json for \'{parameter_name}\''}, 400)
MISSING_JSON_VALUE = lambda parameter_name, details='': ({'error': 'invalid_request', 'error_description': f'Missing value in json for \'{parameter_name}\'.' + details}, 400)
# 401
INVALID_LOGIN = lambda: ({'error': 'unauthorized', 'error_description': 'Invalid login credential'}, 401)
INVALID_TOKEN = lambda: ({'error': 'unauthorized', 'error_description': 'Invalid token provided'}, 401)
# 403
FORBIDDEN = lambda details='You cannot perform this operation': ({'error': 'forbidden', 'error_description': details}, 403)
# 404
PLANT_NOT_FOUND = lambda : ({'error': 'not_found', 'error_description': 'Plant not found'}, 404)
DEVICE_NOT_FOUND = lambda : ({'error': 'not_found', 'error_description': 'Device not found'}, 404)
VIEW_NOT_FOUND = lambda : ({'error': 'not_found', 'error_description': 'View not found'}, 404)
NOT_FOUND = lambda not_found, details='': ({'error': 'not_found', 'error_description': f'{not_found} not found. {details}'}, 404)
# 500
COULD_NOT_ERROR = lambda what = 'Internal server error': ({'error': 'internal_server_error', 'error_description': what}, 500)
INTERNAL_SERVER_ERROR = lambda what = 'Internal server error': ({'error': 'internal_server_error', 'error_description': what}, 500)