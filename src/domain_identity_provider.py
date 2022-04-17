import boto3
from copy import deepcopy
from botocore.exceptions import ClientError
from ses_provider import SESProvider


class DomainIdentityProvider(SESProvider):
    def __init__(self):
        super().__init__()

    def get_token(self):
        try:
            ses = boto3.client("ses", region_name=self.region)
            response = ses.verify_domain_identity(Domain=self.domain)
            self.physical_resource_id = f"{self.domain}@{self.region}"

            token = response["VerificationToken"]
            self.set_attribute("VerificationToken", token)

            recordset = deepcopy(self.get("RecordSetDefaults"))
            recordset.update(
                {
                    "Type": "TXT",
                    "Name": f"_amazonses.{self.domain}.",
                    "ResourceRecords": [f'{token}'],
                }
            )
            self.set_attribute("Domain", self.domain)
            self.set_attribute("Region", self.region)
            self.set_attribute("RecordSets", [recordset])
        except Exception as e:
            self.fail(
                f"could not request domain identity verification for {self.domain}, {e}"
            )
            if not self.physical_resource_id:
                self.physical_resource_id = "could-not-create"

    def create(self):
        if not self.identity_already_exists():
            self.get_token()
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
        self.get_token()

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
