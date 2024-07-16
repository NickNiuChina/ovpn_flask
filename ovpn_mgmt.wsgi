"""
    Carel "SSO" Tableau embedder portal

    Accordingly to the default deployment procedure, this file should be placed in /var/www/remote_analysis_webserver/
"""
from pathlib import Path
import os
import sys
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('wsgi')
logger.setLevel(logging.DEBUG)

parent_folder = str(Path(__file__).parents[0])
base_folder = os.environ.get('SSO_VENV_BASE', os.path.join(str(Path(__file__).parents[0]), 'venv/'))
activate_this = os.path.join(base_folder, 'bin/activate_this.py')
logger.info("parent_folder " + parent_folder)
logger.info("base_folder " + base_folder)
logger.info("activate_this " + activate_this)

with open(activate_this) as file_:
    exec(file_.read(), dict(__file__ = activate_this))

### Comment out the following lines if ddtrace is not used
### >>> ddtrace
#os.environ['DATADOG_TRACE_ENABLED']='true'
#os.environ['DATADOG_SERVICE']='temb'
#os.environ['DATADOG_ENV']='test'
#os.environ['DD_LOGS_INJECTION']='true'
#os.environ['SECRET_KEY']='000000000000000' # Insert a complex alphanumeric string here

#from ddtrace import patch_all
#patch_all()
### ddtrace <<<

os.environ['DS_MASTER_DATABASE']='postgresql://tableau_sso:tableau_sso@ds-be-test-ana-rds01.test.red.carel-cn:5432/ds?application_name=ra_sso' # Set DS password for user tableau_sso
os.environ['DS_BUCKET_SSO']='cn-red-ana-test-sso-b01'

os.environ['TABLEAU_AUTH']='http://ds-fe-test-ana-tbl01.test.red.carel-cn/'
os.environ['TABLEAU_SERVER']='https://digital-service-test.carel-red.com/'
#os.environ['TABLEAU_SERVER_0']='https://test-datascience.teraservice.com/'
#os.environ['TABLEAU_SERVER_1']='https://test-datascience.remotepro.io/'
#os.environ['TABLEAU_SERVER_100']='https://test-datascience.digital-service.com/'
os.environ['TABLEAU_SERVER_1000']='https://digital-service-test.carel-red.com/'
#os.environ['AUTH_SYSTEM_1_URL']='https://test-carel.remotepro.io;remotepro.io'
#os.environ['AUTH_SYSTEM_0_URL']='https://test-accounts.teraportal.com'
os.environ['AUTH_SYSTEM_2_URL']='https://remote.carel-remote.com;carel-remote.com'
#os.environ['AUTH_SYSTEM_100_URL']='https://test-auth.digital-service.com'


os.environ['MARIADBAX_HOST']="ds-be-test-ana-mdb01.test.red.carel-cn"
os.environ['MARIADBAX_PORT']="3306"
os.environ['MARIADBAX_USER']="tableau_ro"
os.environ['MARIADBAX_PASS']="Tableau_ro123!" # Insert MariaDB password here
os.environ['MARIADBAX_DB']="tableau_data"

os.environ['HTML_REPORT_HACCP_NEW_QUERY']='1'
# Import the application object
sys.path.insert(0, parent_folder)
from carelds.temb.app import app as application