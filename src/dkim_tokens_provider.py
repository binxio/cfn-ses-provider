import boto3
from botocore.exceptions import ClientError
from cfn_resource_provider import ResourceProvider


request_schema = {
    "type": "object",
    "required": ["Domain"],
    "properties": {
        "Domain": {"type": "string", "description": "to get DKIM tokens for"},
        "Region": {
            "type": "string",
            "description": "of the SES endpoint to use",
            "default": "eu-west-1",
        },
    },
}


class DkimTokensProvider(ResourceProvider):
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

    def get_tokens(self):
        try:
            ses = boto3.client("ses", region_name=self.region)
            response = ses.verify_domain_dkim(Domain=self.domain)
            self.physical_resource_id = f"{self.domain}@{self.region}"

            tokens = response["DkimTokens"]
            self.set_attribute("DkimTokens", tokens)
            self.set_attribute("DNSRecordTypes", list(map(lambda t: "CNAME", tokens)))
            self.set_attribute(
                "DNSRecordNames",
                list(map(lambda t: f"{t}._domainkey.{self.domain}.", tokens)),
            )
            self.set_attribute(
                "DNSResourceRecords",
                list(map(lambda t: [{"Value": f"{t}.dkim.amazonses.com"}], tokens)),
            )
        except Exception as e:
            self.fail(f"could not get domain dkim tokens for {self.domain}, {e}")
            if not self.physical_resource_id:
                self.physical_resource_id = "could-not-create"

    def create(self):
        self.get_tokens()

    def update(self):
        self.get_tokens()

    def delete(self):
        pass


provider = DkimTokensProvider()


def handler(request, context):
    return provider.handle(request, context)
