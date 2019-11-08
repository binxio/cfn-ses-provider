import os
import logging
import cfn_dkim_provider
import dkim_tokens_provider
import domain_identity_provider

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


def handler(request, context):
    if request["ResourceType"] == "Custom::DkimTokens":
        return dkim_tokens_provider.handler(request, context)
    elif request["ResourceType"] == "Custom::DomainIdentity":
        return domain_identity_provider.handler(request, context)
    else:
        return cfn_dkim_provider.handler(request, context)
