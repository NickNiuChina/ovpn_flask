# EXTRACT SERVICE
STATUS_PLANNED = 0     #job has been planned, but never run
STATUS_RUNNING = 1     #job is running
STATUS_OK = 2          #job returned data (STATUS_OK), and other jobs returned data after this day, assume all data extracted
STATUS_OK_PARTIALDATA = 3 #job returned data (STATUS_OK), but since there is no data after this day yet, assume partial data (STATUS_OK -> STATUS_OK_PARTIALDATA)
STATUS_OK_NODATA = 4      #job returned no data (STATUS_OK_NODATA), and there is nothing after this day, extraction will be retried
STATUS_OK_NODATA_FINAL = 5  #job returned no data (STATUS_OK_NODATA), but other jobs returned data after this day, assume there is no data (STATUS_OK_NODATA -> STATUS_OK_NODATA_FINAL)
STATUS_FAILED_EXT = 6
STATUS_FAILED_TRANS = 7
STATUS_FAILED_LOAD = 8
STATUS_FAILED_HANDLER = 9
STATUS_STRINGS = {
    STATUS_OK: 'OK',
    STATUS_OK_PARTIALDATA: 'OK_PARTIAL_DATA',
    STATUS_OK_NODATA: 'OK_NODATA',
    STATUS_OK_NODATA_FINAL : 'OK_NODATA_FINAL',
    STATUS_FAILED_EXT: 'FAILED_EXT',
    STATUS_FAILED_TRANS: 'FAILED_TRANS',
    STATUS_FAILED_LOAD: 'FAILED_LOAD',
    STATUS_FAILED_HANDLER: 'FAILED_HANDLER'
}

# CONSOLIDATE SERVICE
STATUS_PIVOT_NODATA = 4
STATUS_PIVOT_NULL = 5
STATUS_FAILED_CONS = 6  # generic failure
STATUS_FAILED_PIVOT = 6 # generic failure
STATUS_FAILED_CONS_INPUT_SIZE = 7   # consolidation failed cause of input too large
STATUS_FAILED_PRESTO = 8    # there was an error with presto

# SCHEDULER AND REPORTING SERVICES
STATUS_PLANNED = 0
STATUS_SENT = 2
STATUS_CHECK_FAILED = 3
STATUS_FORCED = 4
STATUS_UNRECOVERABLE_ERROR = 5
STATUS_TABLEAU_ERROR = 6
STATUS_SCRIPT_ERROR = 7
STATUS_SMTP_ERROR = 8


# ONE TIME REPORT STATUSES
STATUS_REPORT_PENDING = STATUS_PLANNED
STATUS_REPORT_PROCESSING = 1 # Not used
STATUS_REPORT_READY = STATUS_SENT
STATUS_REPORT_CHECK_FAILED = STATUS_CHECK_FAILED
STATUS_REPORT_DELETED = 4
STATUS_REPORT_ERROR = STATUS_UNRECOVERABLE_ERROR

# TSDB EXTRACT
EXTRACT_FORCED = 'forced'   # Extraction has been forced by the user, will be executed whenever possible
EXTRACT_PLANNED = 'planned'     # job has been planned since new data notified from TSDB, will be executed when conditions are met
EXTRACT_PENDING = 'pending'     # Extraction has been requested as in queue for execution
EXTRACT_RUNNING = 'running'     # job is executing
EXTRACT_COMPLETE = 'complete'         # job returned data and no other extractions are planned
EXTRACT_OK_NODATA = 'nodata'      # job returned no data, might run again in the future
EXTRACT_FAIL = 'failed' # job failed, might be run again

# ANALYSIS JOBS
ANALYSIS_PENDING = 'pending'
ANALYSIS_PLANNED = 'planned'
ANALYSIS_RUNNING = 'running'
ANALYSIS_COMPLETE = 'complete'
ANALYSIS_OK_NODATA = 'nodata'
ANALYSIS_FAIL = 'failed'

# NEW ENUM STATUSES

STATUS_ENUM_PLANNED = 'planned'
STATUS_ENUM_PENDING = 'pending'
STATUS_ENUM_RUNNING = 'running'
STATUS_ENUM_COMPLETE = 'complete'
STATUS_ENUM_NODATA = 'nodata'
STATUS_ENUM_FAILED = 'failed'
STATUS_ENUM_FORCED = 'forced'