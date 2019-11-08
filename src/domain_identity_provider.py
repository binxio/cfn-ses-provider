import boto3
from botocore.exceptions import ClientError
from cfn_resource_provider import ResourceProvider


request_schema = {
    "type": "object",
    "required": ["Domain"],
    "properties": {
        "Domain": {"type": "string", "description": "to get tokens for"},
        "Region": {
            "type": "string",
            "description": "of the SES endpoint to use",
            "default": "eu-west-1",
        },
    },
}


class DomainIdentityProvider(ResourceProvider):
    def __init__(self):
        self.request_schema = request_schema

    @property
    def domain(self):
        return self.get("Domain").rstrip(".")

    @property
    def old_domain(self):
        return self.get_old("Region", self.domain).rstrip(".")

    @property
    def region(self):
        return self.get("Region")

    @property
    def old_region(self):
        return self.get_old("Region", self.region)

    def verify(self):
        try:
            ses = boto3.client("ses", region_name=self.region)
            response = ses.verify_domain_identity(Domain=self.domain)
            self.physical_resource_id = f"{self.domain}@{self.region}"

            token = response["VerificationToken"]
            self.set_attribute("VerificationToken", token)
            self.set_attribute("DNSRecordType", "TXT")
            self.set_attribute("DNSRecordName", f"_amazonses.{self.domain}.")
            self.set_attribute("DNSResourceRecords", [{"Value": f'"{token}"'}])
        except Exception as e:
            self.fail(
                f"could not request domain identity verification for {self.domain}, {e}"
            )
            if not self.physical_resource_id:
                self.physical_resource_id = "could-not-create"

    def identity_already_exists(self) -> bool:
        ses = boto3.client("ses", region_name=self.region)
        for response in ses.get_paginator("list_identities").paginate(
            IdentityType="Domain"
        ):
            exists = list(filter(lambda d: d == self.domain, response["Identities"]))
            if exists:
                return True
        return False

    def create(self):
        if not self.identity_already_exists():
            self.verify()
        else:
            self.fail(
                f"SES domain identity {self.domain} already exists in region {self.region}"
            )
            self.physical_resource_id = "could-not-create"

    def update(self):
        if (
            self.region != self.old_region or self.domain != self.old_domain
        ) and self.identity_already_exists():
            self.fail(
                f"cannot change domain identity to {self.domain} as it already exists in region {self.region}"
            )
            return
        self.verify()

    def delete(self):
        if self.physical_resource_id != "could-not-create":
            ses = boto3.client("ses", region_name=self.region)
            try:
                ses.delete_identity(Identity=self.domain)
            except ClientError as e:
                self.success(f"ignoring failed delete of identity, {e}")


provider = DomainIdentityProvider()


def handler(request, context):
    return provider.handle(request, context)
