""" Copyright start
    MIT License
    Copyright (c) 2024 Fortinet Inc
    Copyright end """
# -----------------------------------------
# Unit 42 Intel Objects Feed
# -----------------------------------------

from .operations import operations, check_health_ext
from connectors.core.connector import Connector, get_logger, ConnectorError

logger = get_logger('unit-42-intel-objects-feed')


class Intelfeed(Connector):
    def execute(self, config, operation, params, **kwargs):
        logger.info('In execute() Operation:[{0}]'.format(operation))
        try:
            operation = operations.get(operation)
            return operation(config, params, **kwargs)
        except Exception as err:
            logger.exception(err)
            raise ConnectorError(err)

    def check_health(self, config):
        logger.info('starting health check')
        check_health_ext(config)
        logger.info('completed health check no errors')
