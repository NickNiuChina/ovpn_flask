import os

_ddtrace_module_loaded = False
if os.environ.get('DATADOG_TRACE_ENABLED', '').lower() == 'true':
    try:
        from ddtrace import patch_all;
        
        patch_all(logging = True)
        from ddtrace import tracer
        
        _ddtrace_module_loaded = True
    except:
        pass

import logging
from time import gmtime
from pathlib import Path
import sys
import traceback
import itertools

DEEP = 5
BENCH = 15
METRICS = 25
INFO = logging.INFO  # 20
DEBUG = logging.DEBUG  # 10

DEFAULT_LOGGING_LEVEL = logging.DEBUG if os.environ.get('DS_LOG_LEVEL') == 'DEBUG' \
    else DEEP if os.environ.get('DS_LOG_LEVEL') == 'DEEP' \
    else logging.WARNING if os.environ.get('DS_LOG_LEVEL') in ('WARNING', 'WARN') \
    else logging.ERROR if os.environ.get('DS_LOG_LEVEL') == 'ERROR' \
    else logging.INFO


class UTCFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super(UTCFormatter, self).__init__(*args, **kwargs)
        self.converter = gmtime


def remove_log_handlers(loggername=None):
    root = logging.getLogger(loggername)
    for handler in root.handlers[:]:
        root.removeHandler(handler)


def get_logger(log_name,
               log_path=None,
               log_file_suffix='',
               loglevel=None,
               stdout=os.environ.get('DS_LOG_STDOUT', '1') == '1',
               log_time: bool = True,
               options={}):
    """
    Get the default logger interface object

    Args:
        log_name: logger name, the output file will have this name
        log_path: output path for logfile, default is None (no logfile)
        log_file_suffix: a suffix to output on different logfile with the same log_name, default is empty string
        loglevel: logging level
        stdout: if True (default), send log strings to console output stream
        log_time: if True (default), add log timestamp to output
        options: (dict) additional options

    Returns:
        A CustomLogger instance

    """
    if loglevel is None:
        loglevel = DEFAULT_LOGGING_LEVEL
    if options.get('dd_enabled') and not _ddtrace_module_loaded:
        print(
            "Cannot enable DataDog tracer since the module failed to load or DATADOG_TRACE_ENABLED was not set to 'true'")
    dd_enabled = options.get('dd_enabled', False) and _ddtrace_module_loaded
    
    # Benchmark log level
    logging.addLevelName(BENCH, 'BENCH')
    logging.addLevelName(METRICS, 'METRICS')
    _logger = logging.getLogger(log_name)
    _logger.setLevel(loglevel)
    
    format_string = ""
    if log_time:
        format_string += "%(asctime)s - "
    format_string += log_name
    format_string += "%(prefix)s - %(levelname)s "
    sl_format_dd = UTCFormatter(
        f'{format_string}[dd.service=%(dd.service)s dd.env=%(dd.env)s dd.version=%(dd.version)s dd.trace_id=%(dd.trace_id)s dd.span_id=%(dd.span_id)s] : %(message)s')
    sl_format = UTCFormatter(f'{format_string}: %(message)s')
    
    if not _logger.hasHandlers():  # do not duplicate handlers for already existing loggers
        if log_path:  # write to file too
            # Make destination dir
            Path(log_path).mkdir(parents = True, exist_ok = True)
            # Define formats
            if dd_enabled:
                # DataDog injected log handler
                sl_handler = logging.FileHandler(os.path.join(log_path, log_name + log_file_suffix + '.log'),
                                                 encoding = 'utf8')
                sl_handler.setFormatter(sl_format_dd)
                _logger.addHandler(sl_handler)
                if options.get('dd_clean'):
                    # Also save a log file without DataDog injections
                    sl_handler = logging.FileHandler(os.path.join(log_path, log_name + log_file_suffix + '.clean.log'),
                                                     encoding = 'utf8')
                    sl_handler.setFormatter(sl_format)
                    _logger.addHandler(sl_handler)
            else:
                sl_handler = logging.FileHandler(os.path.join(log_path, log_name + log_file_suffix + '.log'),
                                                 encoding = 'utf8')
                sl_handler.setFormatter(sl_format)
                _logger.addHandler(sl_handler)
        
        if stdout:
            # stdout configuration
            sl_handler_console = logging.StreamHandler(sys.stdout)
            sl_handler_console.setFormatter(sl_format)
            _logger.addHandler(sl_handler_console)
            
            # build and return the logger interface object
    return CustomLogger(_logger, ddtrace_enabled = dd_enabled, extra = options.get('extra', ''))


def ddtrace_decorator(fn):
    """
    Decorator that switches ddtrace tracer decorator accordingly to CustomLogger.ddtrace_enabled

    Args:
        fn: the function to decorate

    Returns:
        A decorator

    """
    
    def wrapper(*args, **kwargs):
        if args[0].ddtrace_enabled:
            # print('DDTRACE:', args[0].ddtrace_enabled)
            return tracer.wrap()(fn)(*args, **kwargs)
        else:
            return fn(*args, **kwargs)
    
    return wrapper


class CustomLogger:
    """
        Logger interface
    """
    
    def __init__(self, logger: logging.Logger, ddtrace_enabled: bool = False, extra=''):
        self.logger = logger
        self.BENCH = BENCH
        self.METRICS = METRICS
        self.ddtrace_enabled = ddtrace_enabled
        self.extra = dict(prefix = extra)
        self.exception_fun = self.error
        self.exception_trace_limit = 50
        self.summary = {'debug': 0, 'info': 0, 'warning': 0, 'error': 0, 'critical': 0}
    
    def prepare_message(self, messages):
        return itertools.chain(*tuple([str(m).splitlines() for m in messages]))
    
    def exception(self, *message, trace_limit=None, fun=None):
        if trace_limit is not None:
            self.warning('"trace_limit" option in CustomLogger.exception is deprecated!')
        if fun is not None:
            fun(*message, *tuple(traceback.format_exc(limit = trace_limit or self.exception_trace_limit).split('\n')))
        else:
            self.exception_fun(*message, *tuple(traceback.format_exc(limit = self.exception_trace_limit).split('\n')))
    
    def set_level(self, level):
        self.logger.setLevel(level)
        
    def reset_summary(self):
        self.summary = {'debug': 0, 'info': 0, 'warning': 0, 'error': 0, 'critical': 0}
    
    def deep(self, *message):
        # 5
        for m in self.prepare_message(message):
            self.logger.log(DEEP, m)
    
    @ddtrace_decorator
    def debug(self, *message, extra=dict()):
        # 10
        for m in self.prepare_message(message):
            self.logger.debug(m, extra = {**self.extra, **extra})
        self.summary['debug'] += 1
    
    @ddtrace_decorator
    def info(self, *message, extra=dict()):
        # 20
        for m in self.prepare_message(message):
            self.logger.info(m, extra = {**self.extra, **extra})
        self.summary['info'] += 1
    
    @ddtrace_decorator
    def warn(self, *message, extra=dict()):
        # 30
        self.warning(*message, extra = extra)
    
    @ddtrace_decorator
    def warning(self, *message, extra=dict()):
        # 30
        for m in self.prepare_message(message):
            self.logger.warning(m, extra = {**self.extra, **extra})
        self.summary['warning'] += 1
    
    @ddtrace_decorator
    def error(self, *message, extra=dict()):
        # 40
        for m in self.prepare_message(message):
            self.logger.error(m, extra = {**self.extra, **extra})
        self.summary['error'] += 1
    
    @ddtrace_decorator
    def fatal(self, *message, extra=dict()):
        # 50
        for m in self.prepare_message(message):
            self.logger.fatal(m, extra = {**self.extra, **extra})
        self.summary['critical'] += 1
    
    @ddtrace_decorator
    def critical(self, *message, extra=dict()):
        # 50
        for m in self.prepare_message(message):
            self.logger.critical(m, extra = {**self.extra, **extra})
        self.summary['critical'] += 1
    
    @ddtrace_decorator
    def bench(self, *message, extra=dict()):
        # 15
        for m in self.prepare_message(message):
            self.logger.log(BENCH, m, extra = {**self.extra, **extra})
    
    @ddtrace_decorator
    def metrics(self, metrics):
        # 25
        if not isinstance(metrics, dict):
            self.error("CustomLogger.metrics argument must be a dict {metric->value}")
            return
        for metric in metrics:
            for m in self.prepare_message((f"{metric} = {metrics[metric]}",)):
                self.logger.log(self.METRICS, m)
    
    def log(self, level, *message):
        for m in self.prepare_message(message):
            self.logger.log(level, m)


class CustomRequestLogger(CustomLogger):
    """
        This logger is specialized for the applications where you want to assign a prefix to all your messages.
        Example is a Flask application where we want to assign a unique UUID to every single request, or to distinguish subprocess.
    """
    
    def __init__(self, logger, prefix=None, ddtrace_enabled=None):
        CustomLogger.__init__(self, logger = logger, ddtrace_enabled = ddtrace_enabled)
        if isinstance(logger, CustomLogger):
            self.logger = logger.logger
            self.ddtrace_enabled = ddtrace_enabled or logger.ddtrace_enabled
            self.extra = logger.extra
            self.exception_fun = logger.exception_fun
            self.exception_trace_limit = logger.exception_trace_limit
        else:
            self.logger = logger
            self.ddtrace_enabled = ddtrace_enabled or False
            self.exception_fun = self.error
            self.exception_trace_limit = 10
        
        self.DEEP = DEEP
        self.BENCH = BENCH
        self.METRICS = METRICS
        self.prefix = prefix
        
        self.extra = dict(prefix = f" - {prefix}" or '')
    
    """def prepare_message(self, message):
        lines = [str(' '.join([str(m) for m in message]))]#.splitlines()
        return ['{} - {}'.format(self.prefix, l) for l in lines] if self.prefix is not None else lines"""