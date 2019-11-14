import boto3
from typing import List
from cfn_resource_provider import ResourceProvider


request_schema = {
    "type": "object",
    "required": ["Domain", "Region"],
    "properties": {
        "Domain": {"type": "string", "description": "to get DKIM tokens for"},
        "Region": {"type": "string", "description": "of the SES endpoint to use"},
        "TTL": {
            "type": "integer",
            "description": "of the resource record set",
            "default": 60,
        },
    },
}


class DkimTokensProvider(ResourceProvider):
    def __init__(self):
        self.request_schema = request_schema

    def convert_property_types(self):
        self.heuristic_convert_property_types(self.properties)

    @property
    def domain(self):
        return self.get("Domain").rstrip(".")

    @property
    def old_domain(self):
        return self.get_old("Region", self.domain).rstrip(".")

    @property
    def ttl(self):
        return self.get("TTL")

    @property
    def region(self):
        return self.get("Region")

    @property
    def old_region(self):
        return self.get_old("Region", self.region)

    def make_record_sets(self, tokens: List[str]) -> List[dict]:
        return [
            {
                "Name": f"{token}._domainkey.{self.domain}.",
                "Type": "CNAME",
                "TTL": self.ttl,
                "DNSResourceRecords": [f"{token}.dkim.amazonses.com"],
            }
            for token in tokens
        ]

    def get_tokens(self):
        try:
            ses = boto3.client("ses", region_name=self.region)
            response = ses.verify_domain_dkim(Domain=self.domain)
            self.physical_resource_id = f"{self.domain}@{self.region}"

            tokens = sorted(response["DkimTokens"])
            record_sets = self.make_record_sets(tokens)

            self.set_attribute("DkimTokens", tokens)
            self.set_attribute("RecordSets", record_sets)
            self.set_attribute(
                "DNSRecordTypes", list(map(lambda rs: rs["Type"], record_sets))
            )
            self.set_attribute(
                "DNSRecordNames", list(map(lambda rs: rs["Name"], record_sets))
            )
            self.set_attribute(
                "DNSResourceRecords",
                list(map(lambda rs: rs["DNSResourceRecords"], record_sets)),
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
