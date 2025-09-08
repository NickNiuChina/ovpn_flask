from flask import Blueprint
from myproject.context import logger


test_bp = Blueprint("test", __name__)

####################################################################################
# hello page
####################################################################################
@test_bp.route("/hello", methods=("GET",))
def hello():
    return "Hello, 中文!"


####################################################################################
# test page
####################################################################################
@test_bp.route("/test", methods=('GET', 'POST'))
def test():
    """
    @summary: test page for test purpose only.
    @return: flask will take the list or dict and turns to jason automatically.
    """
    logger.debug("Log TEST, debug")
    logger.info("Log TEST, info")
    logger.warning("Log TEST, warning")
    logger.error("LOG TEST, error")
    logger.critical("Log test, fatal")
    return "Hello 世界！", 200