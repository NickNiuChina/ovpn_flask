"""
    Flask entry script
"""
from pathlib import Path
import os
import sys
import config
from myproject.context import logger
# import logging

# logging.basicConfig(level=logging.WARNING)
# logger = logging.getLogger('wsgi')
# logger.setLevel(logging.DEBUG)

parent_folder = str(Path(__file__).parents[0])
base_folder = os.environ.get('SSO_VENV_BASE', os.path.join(str(Path(__file__).parents[0]), '.venv/'))

logger.info("parent_folder " + parent_folder)
logger.info("base_folder " + base_folder)

### Comment out the following lines if ddtrace is not used
#os.environ['DATADOG_TRACE_ENABLED']='true'
#os.environ['DATADOG_SERVICE']='temb'
#os.environ['DATADOG_ENV']='test'
#os.environ['DD_LOGS_INJECTION']='true'
#os.environ['SECRET_KEY']='000000000000000' # Insert a complex alphanumeric string here

#from ddtrace import patch_all
#patch_all()
### ddtrace <<<

#os.environ['DS_MASTER_DATABASE']='###'
#os.environ['DS_BUCKET_SSO']='cn-red-ana-test-sso-b01'

# Import the application object
sys.path.insert(0, parent_folder)
from myproject import create_app
application = create_app()

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000, debug=True)