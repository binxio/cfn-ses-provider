import boto3
from copy import deepcopy
from typing import List
from cfn_resource_provider import ResourceProvider


request_schema = {
    "type": "object",
    "required": ["Domain", "Region"],
    "properties": {
        "Domain": {"type": "string", "description": "to get DKIM tokens for"},
        "Region": {"type": "string", "description": "of the SES endpoint to use"},
        "RecordSetDefaults": {"type": "object", "default": {"TTL": "60"}},
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

    def make_record_sets(self, tokens: List[str]) -> List[dict]:
        result = []
        for token in tokens:
            recordset = deepcopy(self.get("RecordSetDefaults"))
            recordset.update(
                {
                    "Name": f"{token}._domainkey.{self.domain}.",
                    "Type": "CNAME",
                    "ResourceRecords": [f"{token}.dkim.amazonses.com"],
                }
            )
            result.append(recordset)
        return result

    def get_tokens(self):
        try:
            ses = boto3.client("ses", region_name=self.region)
            response = ses.verify_domain_dkim(Domain=self.domain)
            self.physical_resource_id = f"{self.domain}@{self.region}"

            tokens = sorted(response["DkimTokens"])
            record_sets = self.make_record_sets(tokens)

            self.set_attribute("DkimTokens", tokens)
            self.set_attribute("RecordSets", record_sets)
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
