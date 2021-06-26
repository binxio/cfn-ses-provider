from copy import deepcopy

import boto3

from ses_provider import SESProvider


class MailFromDomainProvider(SESProvider):
    def __init__(self):
        super().__init__()
        self.request_schema = deepcopy(self.request_schema)
        self.request_schema["required"].append("MailFromSubdomain")
        self.request_schema["properties"]["MailFromSubdomain"] = {
            "type": "string",
            "description": "subdomain to use as mail from",
        }
        self.request_schema["properties"]["BehaviorOnMXFailure"] = {
            "type": "string",
            "description": "action to take if "
            "Amazon SES cannot "
            "successfully read the "
            "required MX record "
            "when you send an "
            "email ("
            "UseDefaultValue | "
            "RejectMessage), "
            "default is "
            "UseDefaultValue",
        }

    @property
    def mail_from_subdomain(self):
        return self.get("MailFromSubdomain")

    @property
    def behavior_on_mx_failure(self):
        return self.get("BehaviorOnMXFailure")

    def generate_dns_recordsets(self):
        if self.mail_from_subdomain == "":
            return []
        else:
            recordset_mx = deepcopy(self.get("RecordSetDefaults"))
            recordset_mx.update(
                {
                    "Type": "MX",
                    "Name": f"{self.mail_from_subdomain}.{self.domain}.",
                    "ResourceRecords": [
                        f'"10 feedback-smtp.{self.region}.amazonses.com"'
                    ],
                }
            )

            recordset_txt = deepcopy(self.get("RecordSetDefaults"))
            recordset_txt.update(
                {
                    "Type": "TXT",
                    "Name": f"{self.mail_from_subdomain}.{self.domain}.",
                    "ResourceRecords": ["v=spf1 include:amazonses.com ~all"],
                }
            )
            return [recordset_mx, recordset_txt]

    def set_mail_from(self):
        try:
            ses = boto3.client("ses", region_name=self.region)

            mx_failure_behaviour = self.behavior_on_mx_failure

            if mx_failure_behaviour is None:
                mx_failure_behaviour = "UseDefaultValue"

            ses.set_identity_mail_from_domain(
                Identity=self.domain,
                MailFromDomain=self.mail_from_subdomain,
                BehaviorOnMXFailure=mx_failure_behaviour,
            )

            self.physical_resource_id = f"{self.domain}@{self.region}"

            self.set_attribute("Domain", self.domain)
            self.set_attribute("Region", self.region)
            self.set_attribute("RecordSets", self.generate_dns_recordsets())
        except Exception as e:
            if not self.physical_resource_id:
                self.physical_resource_id = "could-not-create"
            self.fail(
                f"could not set mail from domain for {self.mail_from_subdomain}.{self.domain}, {e}"
            )

    def create(self):
        if self.identity_already_exists():
            self.set_mail_from()
        else:
            self.physical_resource_id = "could-not-create"
            self.fail(
                f"SES domain identity {self.domain} must exist in region {self.region} before setting mail from value"
            )

    def update(self):
        self.set_mail_from()

    def delete(self):
        self.properties["mail_from_subdomain"] = ""
        self.set_mail_from()


provider = MailFromDomainProvider()


def handler(request, context):
    return provider.handle(request, context)
