"""
    Copyright start
    MIT License
    Copyright (c) 2024 Fortinet Inc
    Copyright end 
"""

import requests
import datetime

from connectors.core.connector import get_logger, ConnectorError
from connectors.core.utils import update_connnector_config
from taxii2client.v21 import Server
from taxii2client.common import TokenAuth
from taxii2client.v20 import Server, as_pages

logger = get_logger('unit-42-intel-objects-feed')


class Intelfeed(object):
    def __init__(self, config):
        self.base_url = config.get("server_url")
        if self.base_url.startswith('https://') or self.base_url.startswith('http://'):
            self.base_url = self.base_url.strip('/')
        else:
            self.base_url = 'https://{0}'.format(self.base_url.strip('/'))
        self.api_key = config.get("api_key")
        self.verify_ssl = config.get("verify_ssl")

    def api_request(self, endpoint, verb=None, params=None, data=None, json_data=None):
        try:
            server_url = self.base_url + '/taxii'
            server = Server(url=server_url, auth=TokenAuth(key=self.api_key), verify=self.verify_ssl)
            return server
        except requests.exceptions.SSLError:
            logger.error('An SSL error occurred.')
            raise ConnectorError('An SSL error occurred.')
        except requests.exceptions.ConnectionError:
            logger.error('A connection error occurred.')
            raise ConnectorError('A connection error occurred.')
        except Exception as err:
            logger.error(err)
            raise ConnectorError(err)

    def build_payload(self, params):
        result = {k: v for k, v in params.items() if v is not None and v != ''}
        return result


def compare_last_and_current_time(last_pull_time, modified_date): 
    try:
        try:
            last_pull_ts = int(datetime.datetime.strptime(str(last_pull_time), "%Y-%m-%dT%H:%M:%S.%fZ").timestamp())
            modified_time_ts = int(datetime.datetime.strptime(modified_date, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp())
        except Exception as err:
            logger.debug('Err = {0}'.format(err))
            logger.debug('Now checking format {}'.format('%Y-%m-%dT%H:%M:%S.%fZ'))
            raise
        if last_pull_ts < modified_time_ts:
            return True
        return False
    except Exception as Err:
        logger.exception(Err)
        raise ConnectorError(Err)


def fetch_indicators(config, params, **kwargs):
    obj = Intelfeed(config)
    last_pull_time = params.get("last_pull_time")
    result = obj.build_payload(params)
    indicator_object = []
    obj_list = []
    server_response = obj.api_request(config)
    for api_root in server_response.api_roots:
        for collection in api_root.collections:
            indicator_object.append(collection.get_objects())

    for each_object in indicator_object:
        for objects in each_object.get('objects'):
            pattern = objects.get('pattern')
            if pattern and 'value' in pattern:
                objects.update({"indicator_type": pattern.split(':')[0][1:],
                                "indicator_value": pattern.split(':')[1][:-1].split('=')[1][1:].replace("'", '')})
            elif pattern and 'file:hashes' in pattern:
                objects.update({"indicator_type": pattern.split('.')[1].split('=')[0][:-1].replace("'",''),
                                "indicator_value": pattern.split('.')[1].split('=')[1][:-1][1:].replace("'",'')})
            elif pattern and 'process' in pattern:
                objects.update({"indicator_type": pattern.split(':')[0][1:],
                                "indicator_value": pattern.split(':')[1][:-1]})
            if objects.get('modified'):
                if last_pull_time != "" and last_pull_time != None and last_pull_time != 0:
                    flag = compare_last_and_current_time(last_pull_time, objects.get('modified', ''))
                    if flag:
                        obj_list.append(objects)
                else:
                    obj_list.append(objects)
    return obj_list


def check_health_ext(config):
    try:
        obj = Intelfeed(config)
        server_response = obj.api_request(config)
        api_root = server_response.api_roots[0]
        if api_root:
            return True

    except Exception as err:
        logger.error("{0}".format(str(err)))
        raise ConnectorError(str(err))


operations = {
    'fetch_indicators': fetch_indicators
}
