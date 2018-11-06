import os
import logging
import cfn_identity_policy_provider
import cfn_domain_provider

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))


def handler(request, context):
    if request['ResourceType'] == 'Custom::IdentityPolicy':
        return cfn_identity_policy_provider.handler(request, context)
    else:
        return cfn_domain_provider.handler(request, context)
