import requests
from carelds.common.utils.constants import *
from datetime import datetime, date
import pytz

class ElasticLogger:

    def __init__(self, server_host='localhost', server_port=9200, logger=None, **kwargs):
        """

        Args:
            server_host: elasticsearch server hostname
            server_port: elasticsearch server port
            logger: logger object
        """
        self.session = requests.Session()
        self.server_host = server_host
        self.server_port = server_port
        self.logger = logger

        try:
            r = self.session.get(f"http://{self.server_host}:{self.server_port}/thisindexdoesnotexist/_search", timeout=3)
            assert r.status_code == 404
            self.connected = True
        except:
            self.connected = False
            if self.logger is not None:
                logger.warning('Failed to connect to ElasticSearch')
            else:
                print('Could not connect to ElasticSearch')

    def log_new(self, index_, doc, id_):
        if not self.connected:
            return None
        r = self.session.put(f'http://{self.server_host}:{self.server_port}/{index_}/_doc/{id_}', json=doc)
        if r.status_code >= 400:
            raise RuntimeError(f"Failed to put new document: {r.text}")
        return r.json()

    def log_update(self, index_, doc, id_):
        if not self.connected:
            return None
        r = self.session.post(f'http://{self.server_host}:{self.server_port}/{index_}/_update/{id_}', json=dict(doc=doc))
        if r.status_code >= 400:
            raise RuntimeError(f"Failed to update document: {r.text}")
        return r.json()

    def log_get(self, index_, query):
        if not self.connected:
            return None
        r = self.session.get(f'http://{self.server_host}:{self.server_port}/{index_}/_doc/_search', json=dict(query=query))
        if r.status_code >= 400:
            raise RuntimeError(f"Failed to read from ElasticSearch: {r.text}")
        return r.json()



class ElasticMDMLogger(ElasticLogger):

    def __init__(self, *args, **kwargs):
        """

        Args:
            server_host: elasticsearch server hostname
            server_port: elasticsearch server port
            logger: logger object
            except_on_fail: if True, an exception is raised (propagated) if any elasticsearch response has status code >= 400
        """
        super().__init__(*args, **kwargs)
        self.except_on_fail = kwargs.get('except_on_fail', False) is True

    def consolidation_plan(self, job_uuid, device:str, job_task:str, job_date:date, job_trigger:dict, plan_time:datetime):
        """
        Create a new consolidation job.
        Args:
            job_trigger:
            job_date:
            job_uuid:
            device:
            job_task:
            plan_time: Job plan time. Time is expected to be UTC localized or naive datetime.

        Returns: True if everything went good, False otherwise

        """
        assert len(device) == 40, 'Invalid device'
        assert job_task in ('DataMonth', 'AnalysisMonth', 'DataYear', 'ProjectMonth', 'PivotMonth'), 'Invalid job_type'
        try:
            self.log_new(index_='consolidate_jobs', id_=job_uuid,
                        doc={"task": job_task, "device":device, "job_date":str(job_date), "job_trigger": job_trigger,
                             "steps": {"plan": {"plan_time": int(pytz.utc.localize(plan_time).timestamp())}}, "status": STATUS_PLANNED})
        except RuntimeError:
            if self.except_on_fail:
                raise
            return False
        return True

    def consolidation_run(self, job_uuid, run_time:datetime):
        """
        Update an existing consolidation h
        Args:
            run_time: job start time. Time is expected to be UTC localized or naive datetime.
            job_uuid: job uuid

        Returns: True if everything went good, False otherwise

        """
        try:
            self.log_update(index_='consolidate_jobs', id_=job_uuid,
                            doc={"steps": {"run": {"run_time": int(pytz.utc.localize(run_time).timestamp())}}, "status": STATUS_RUNNING})
        except RuntimeError:
            if self.except_on_fail:
                raise
            return False
        return True

    def consolidation_notify(self, job_uuid, lambda_id:str, end_time:datetime, data_time:datetime, status:int):
        """

        Args:
            lambda_id: id of the lambda that performed this job (lambda's requestId)
            end_time: job end time, when the lambda ended. Time is expected to be UTC localized or naive datetime.
            data_time: data time, the timestamp of the S3 output. Time is expected to be UTC localized or naive datetime.
            job_uuid: job uuid, assigned by the service
            status: job status

        Returns: True if everything went good, False otherwise

        """
        try:
            self.log_update(index_='consolidate_jobs', id_=job_uuid,
                            doc={"steps": {"notify": {"end_time": int(pytz.utc.localize(end_time).timestamp()),
                                                      "data_time": int(pytz.utc.localize(data_time).timestamp()) if data_time is not None else None}},
                                 "status": status, "lambda_id": lambda_id})
        except RuntimeError:
            if self.except_on_fail:
                raise
            return False
        return True


    def extract_run(self, job_uuid, device:str, job_task:str, job_date:date, run_time:datetime):
        """

        Args:
            device:
            job_task:
            job_date:
            job_uuid:
            run_time: Job Run (and Plan) time. Time is expected to be UTC localized or naive datetime.

        Returns:

        """
        assert len(device) == 40, 'Invalid device'
        r = self.log_new(index_='extract_jobs', id_=job_uuid,
                         doc={"task": job_task, "device": device, "job_date": str(job_date),
                              "steps": {"run": {"run_time": int(pytz.utc.localize(run_time).timestamp())}, "plan": {"plan_time": int(pytz.utc.localize(run_time).timestamp())}},
                              "status": STATUS_RUNNING})

    def extract_notify(self, job_uuid, lambda_id:str, end_time:datetime, data_time:datetime, status:int):
        """

        Args:
            lambda_id:
            job_uuid:
            end_time: Job end time. Time is expected to be UTC localized or naive datetime.
            data_time: S3 data time. Time is expected to be UTC localized or naive datetime.
            status:

        Returns:

        """
        try:
            self.log_update(index_='extract_jobs', id_=job_uuid,
                            doc={"steps": {"notify": {"end_time": int(pytz.utc.localize(end_time).timestamp()),
                                                      "data_time": int(pytz.utc.localize(data_time).timestamp()) if data_time is not None else None}},
                                 "status": status, "lambda_id": lambda_id})
        except RuntimeError:
            if self.except_on_fail:
                raise
            return False
        return True

    def get_device_extractions(self, device:str, after:datetime=None, before:datetime=None):
        query = {"bool": {"must": [{"term": {"device": device}}]}}
        if after is not None:
            query['bool']['must'].append({"range": {"steps.run.run_time": {"gte": int(pytz.utc.localize(after).timestamp())}}})
        if before is not None:
            query['bool']['must'].append({"range": {"steps.run.end_time": {"lte": int(pytz.utc.localize(before).timestamp())}}})
        r = self.log_get(index_='extract_jobs', query=query)
        return r

    def get_device_consolidations(self, device:str, after:datetime=None, before:datetime=None):
        query = {"bool": {"must": [{"term": {"device": device}}]}}
        if after is not None:
            query['bool']['must'].append(
                {"range": {"steps.plan.plan_time": {"gte": int(pytz.utc.localize(after).timestamp())}}})
        if before is not None:
            query['bool']['must'].append(
                {"range": {"steps.notify.end_time": {"lte": int(pytz.utc.localize(before).timestamp())}}})
        r = self.log_get(index_='consolidate_jobs', query=query)
        return r
