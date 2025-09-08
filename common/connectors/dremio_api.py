import json
import requests
from urllib.parse import quote, urlencode
from pathlib import Path
from carelds.common.logging.logutil import get_logger, DEBUG
import uuid



class DremioAPI:

    def __init__(self, username, password, url, logger=None):
        self.username = username
        self.password = password
        self.url = url
        self.logger = logger or get_logger('dremio_api', loglevel=DEBUG)

        login_data = {'userName': self.username, 'password': self.password}
        response = requests.post(f'{self.url}/apiv2/login', headers={'content-type': 'application/json'},
                                 data=json.dumps(login_data))
        response = json.loads(response.text)
        try:
            self._login_header = {'content-type': 'application/json', 'authorization': f'_dremio{response["token"]}'}
        except KeyError:
            self.logger.error(f"Login failed with user {self.username}")


    def get_catalog_root(self):
        return self.get('catalog')['data']


    def get_sources(self):
        return [cat for cat in self.get_catalog_root() if cat.get('containerType') == 'SOURCE']


    def get_spaces(self):
        return [cat for cat in self.get_catalog_root() if cat.get('containerType') == 'SPACE']


    def get_folders(self):
        return [cat for cat in self.get_catalog_root() if cat.get('containerType') == 'FOLDER']


    def get_catalog(self, catalog_id):
        response = requests.get(f'{self.url}/api_v1/v3/catalog/{catalog_id}', headers=self._login_header)
        if 'errorMessage' in response.json():
            self.logger.error(f"Failed to get catalog \"{catalog_id}\": {response.json().get('moreInfo')} ")
            return None
        return json.loads(response.text)


    def post_catalog_id(self, catalog, _id=None):
        """
        Dremio API /api_v1/v3/catalog/ (new catalog entity) and /api_v1/v3/catalog/{id} (PDS promotion)

        Args:
            catalog: the catalog dict object
            _id: folder or file id to promote to PDS, if None (default), assume new catalog entity

        Returns: response if successful, else None

        """
        print(f"POST: {self.url}/api_v1/v3/catalog/{_id}")
        response = requests.post(f'{self.url}/api_v1/v3/catalog/{_id}', headers=self._login_header, data=json.dumps(catalog) if isinstance(catalog, dict) else catalog)
        if 'errorMessage' in response.json():
            self.logger.error(f"Failed to set catalog _id={_id}: {response.json().get('moreInfo')} ")
            print(catalog)
            return None
        return response.json()


    def post_catalog(self, catalog):
        """
        Dremio API /api_v1/v3/catalog/ (new catalog entity) and /api_v1/v3/catalog/{id} (PDS promotion)

        Args:
            catalog: the catalog dict object

        Returns: response if successful, else None

        """
        response = requests.post(f'{self.url}/api_v1/v3/catalog/', headers=self._login_header, data=json.dumps(catalog) if isinstance(catalog, dict) else catalog)
        if 'errorMessage' in response.json():
            self.logger.error(f"Failed to set catalog: {response.json().get('moreInfo')} ")
            self.logger.debug(f"Failed: {catalog}")
            return None
        return response.json()



    def get_catalog_by_path(self, catalog_path):
        """
        Get catalog given its path

        Args:
            catalog_path: catalog path

        Returns: response (catalog definition) if successful, else None

        """
        response = requests.get(f'{self.url}/api_v1/v3/catalog/by-path/{catalog_path}', headers=self._login_header)
        if 'errorMessage' in response.json():
            self.logger.error(f"Failed to get catalog \"{catalog_path}\": {response.json().get('moreInfo')} ")
            return None
        return json.loads(response.text)


    def get(self, endpoint):
        """
        Perform a get operation to the provided endpoint
        Args:
            endpoint: /api_v1/v3/{endpoint}

        Returns: GET response as dict

        """
        resp = requests.get('{server}/api_v1/v3/{endpoint}'.format(server= self.url, endpoint=endpoint), headers=self._login_header, timeout=61)
        return json.loads(resp.text)


    def post(self, endpoint, body=None):
        """
        Perform a post operation to the provided endpoint
        Args:
            endpoint: /api_v1/v3/{endpoint}
            body: POST body as dict (must be json-serializable)

        Returns:    POST response as dict

        """
        text = requests.post('{server}/api_v1/v3/{endpoint}'.format(server=self.url, endpoint=endpoint), headers=self._login_header, data=json.dumps(body), timeout=61).text
        # a post may return no data
        if text:
            return json.loads(text)
        else:
            return None


    def delete_catalog(self, catalog_id, tag='0'):
        requests.request("DELETE", f'{self.url}/api_v1/v3/catalog/{catalog_id}', data="", headers=self._login_header, params={'tag': tag}, timeout=61)


    def create_pds(self, path, new_pds=dict()):
        path_string = '/'.join(path)
        entity_old = self.get_catalog_by_path(path_string)
        if entity_old['entityType'] == 'dataset':  # recreate PDS
            new_pds = {k: entity_old[k] for k in entity_old if k in ('entityType', 'name', 'type', 'path', 'sql', 'fields', 'format', 'accelerationRefreshPolicy')}
            self.delete_catalog(entity_old['id'], entity_old['tag'])
            # Now should be a folder
            folder = self.get_catalog_by_path(path_string)
            if folder['entityType'] not in ('folder', 'file'):
                self.logger.error(f"DremioAPI.create_pds > After deleting old PDS, I expected a folder! Found {folder}")
                return None
        elif entity_old['entityType'] in ('folder', 'file'):  # create PDS
            folder = entity_old
            new_pds.setdefault('path', entity_old['path'])
            new_pds['entityType'] = 'dataset'
            new_pds['type'] = 'PHYSICAL_DATASET'
        else:
            self.logger.error(f"DremioAPI.create_pds > Cannot work with {entity_old['entityType']}")
            return None

        resp = self.post_catalog_id(new_pds, quote(folder['id'],safe=''))
        return resp

    def export_tree(self, node_id, catalogs, folders=True, spaces=False):
        try:  # check if node_id is uuid or path
            uuid.UUID(node_id)
            current_node = self.get_catalog(node_id)
        except (ValueError, TypeError):
            current_node = self.get_catalog_by_path(node_id.replace('dremio:/', ''))

        if current_node is None:
            return catalogs
        self.logger.debug(f"Visiting node: {current_node.get('entityType')} {current_node.get('type')} {current_node.get('path')}")
        new_node = {k: current_node[k] for k in current_node if k in ('entityType', 'name', 'type', 'path', 'sql', 'fields', 'format', 'accelerationRefreshPolicy')}
        if (folders and new_node['entityType'] == 'folder') or (spaces and new_node['entityType'] == 'space') or new_node['entityType'] in ('dataset'):
            catalogs.append(new_node)
            self.logger.debug(f"Export node: {new_node.get('entityType')} {new_node.get('type')} {new_node.get('path')}")
        for child in current_node.get('children', []):
            catalogs += self.export_tree(child['id'], list(), folders, spaces)
        return catalogs