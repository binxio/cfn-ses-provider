import os
import logging
import cfn_dkim_provider

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))


def handler(request, context):
    return cfn_dkim_provider.handler(request, context)
