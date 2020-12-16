import os
import logging
import cfn_dkim_provider
import dkim_tokens_provider
import domain_identity_provider
import mail_from_domain_provider
import active_rule_set_provider
import verified_identity_provider
import verified_mail_from_domain_provider
import identity_notifications_provider
import identity_policy_provider


def handler(request, context):
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    if request["ResourceType"] == "Custom::DkimTokens":
        return dkim_tokens_provider.handler(request, context)
    elif request["ResourceType"] == "Custom::DomainIdentity":
        return domain_identity_provider.handler(request, context)
    elif request["ResourceType"] in [
        "Custom::SESActiveReceiptRuleSet",
        "Custom::ActiveReceiptRuleSet",
    ]:
        return active_rule_set_provider.handler(request, context)
    elif request["ResourceType"] == "Custom::IdentityNotifications":
        return identity_notifications_provider.handler(request, context)
    elif request["ResourceType"] == "Custom::VerifiedIdentity":
        return verified_identity_provider.handler(request, context)
    elif request["ResourceType"] == "Custom::IdentityPolicy":
        return identity_policy_provider.handler(request, context)
    elif request["ResourceType"] == "Custom::MailFromDomain":
        return mail_from_domain_provider.handler(request, context)
    elif request["ResourceType"] == "Custom::VerifiedMailFromDomain":
        return verified_mail_from_domain_provider.handler(request, context)
    else:
        return cfn_dkim_provider.handler(request, context)
