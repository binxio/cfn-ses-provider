import re
import boto3
from botocore.exceptions import ClientError
from cfn_resource_provider import ResourceProvider


request_schema = {
    "type": "object",
    "required": ["HostedZoneId"],
    "properties": {
        "Domain": {"type": "string", "description": "to create DKIM for"},
        "HostedZoneId": {
            "type": "string",
            "description": "to store the DKIM records in",
        },
        "Region": {
            "type": "string",
            "description": "of the SES endpoint to use",
            "default": "eu-west-1",
        },
    },
}


class DKIMProvider(ResourceProvider):
    def __init__(self):
        self.request_schema = request_schema
        self.route53 = boto3.client("route53")

    def create(self):
        if not self.check_identity(self.dkim_domain):
            self.upsert()
        else:
            self.fail(f"SES domain identity {self.dkim_domain} already exists")

    def is_update_required(self):
        old_hosted_zone_id = self.get_old("HostedZoneId", self.get("HostedZoneId"))
        if old_hosted_zone_id != self.hosted_zone_id:
            return True
        old_region = self.get_old("Region", self.get("Region"))
        if old_region != self.get("Region"):
            return True

        old_domain = self.get_old("Domain")
        if not old_domain:
            old_dkim_domain = self.get_hosted_zone_name(old_hosted_zone_id).rstrip(".")
        else:
            old_dkim_domain = old_domain.rstrip(".")

        if old_dkim_domain != self.dkim_domain:
            return True
        return False

    def update(self):
        if not self.is_update_required():
            self.success("no changes")
            return

        if self.check_identity(self.dkim_domain):
            self.fail(f"new SES domain identity {self.dkim_domain} already exists")
            return

        self.upsert()

    def delete(self):
        hosted_zone_id, domain = (
            self.extract_domain_name_and_zone_from_physical_resource_id()
        )
        if hosted_zone_id == "could-not-create":
            return

        if not domain:
            domain = self.get_hosted_zone_name(hosted_zone_id).rstrip(".")
        self.delete_identity(domain)
        self.delete_dns_records(hosted_zone_id, domain)

    def check_identity(self, domain):
        dkim_domain = domain.rstrip(".")
        ses = boto3.client("ses", region_name=self.get("Region"))
        for response in ses.get_paginator("list_identities").paginate(
            IdentityType="Domain"
        ):
            exists = list(filter(lambda d: d == dkim_domain, response["Identities"]))
            if exists:
                return True
        return False

    def delete_identity(self, domain):
        ses = boto3.client("ses", region_name=self.get("Region"))
        ses.delete_identity(Identity=domain)

    def delete_dns_records(self, hosted_zone_id, domain):
        to_delete = []
        paginator = self.route53.get_paginator("list_resource_record_sets")
        for page in paginator.paginate(HostedZoneId=hosted_zone_id):
            for rr in page["ResourceRecordSets"]:
                if rr["Type"] == "CNAME" and rr["Name"].endswith(
                    "._domainkey.%s." % domain
                ):
                    to_delete.append(rr)
                elif rr["Type"] == "TXT" and rr["Name"] == "_amazonses.%s." % domain:
                    to_delete.append(rr)
                else:
                    pass

        if len(to_delete) > 0:
            batch = {
                "Changes": [
                    {"Action": "DELETE", "ResourceRecordSet": rr} for rr in to_delete
                ]
            }
            r = self.route53.change_resource_record_sets(
                HostedZoneId=hosted_zone_id, ChangeBatch=batch
            )
            self.set_attribute("ChangeId", r["ChangeInfo"]["Id"])

    @property
    def hosted_zone_id(self):
        return self.get("HostedZoneId")

    @property
    def hosted_zone_name(self):
        return self.get_hosted_zone_name(self.hosted_zone_id).rstrip(".")

    def get_hosted_zone_name(self, hosted_zone_id):
        response = self.route53.get_hosted_zone(Id=hosted_zone_id)
        return response["HostedZone"]["Name"]

    @property
    def domain(self):
        return self.get("Domain")

    @property
    def dkim_domain(self):
        if self.domain:
            return self.get("Domain").rstrip(".")
        else:
            return self.hosted_zone_name

    def create_physical_resource_id(self):
        if self.domain and self.domain.rstrip(".") != self.hosted_zone_name:
            return f"{self.dkim_domain}@{self.hosted_zone_id}"
        else:
            return self.hosted_zone_id

    def extract_domain_name_and_zone_from_physical_resource_id(self):
        match = re.fullmatch(
            r"((?P<domain>[^@]*)@)?(?P<hosted_zone_id>.*)", self.physical_resource_id
        )
        return (
            (None, None)
            if not match
            else (match.group("hosted_zone_id"), match.group("domain"))
        )

    def upsert(self):
        batch = {"Changes": []}
        try:
            domain = self.dkim_domain
            ses = boto3.client("ses", region_name=self.get("Region"))
            verification_token = ses.verify_domain_identity(Domain=domain)[
                "VerificationToken"
            ]
            dkim_tokens = ses.verify_domain_dkim(Domain=domain)["DkimTokens"]
            batch["Changes"] = [
                {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": "_amazonses.%s" % domain,
                        "Type": "TXT",
                        "TTL": 60,
                        "ResourceRecords": [{"Value": '"%s"' % verification_token}],
                    },
                }
            ]
            for dkim_token in dkim_tokens:
                change = {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": "%s._domainkey.%s." % (dkim_token, domain),
                        "Type": "CNAME",
                        "TTL": 60,
                        "ResourceRecords": [
                            {"Value": "%s.dkim.amazonses.com" % dkim_token}
                        ],
                    },
                }
                batch["Changes"].append(change)

            r = self.route53.change_resource_record_sets(
                HostedZoneId=self.hosted_zone_id, ChangeBatch=batch
            )
            self.set_attribute("ChangeId", r["ChangeInfo"]["Id"])
            self.physical_resource_id = self.create_physical_resource_id()
        except ClientError as e:
            self.physical_resource_id = "could-not-create"
            self.fail(e.message)


provider = DKIMProvider()


def handler(request, context):
    return provider.handle(request, context)
