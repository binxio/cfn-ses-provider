import boto3
from copy import deepcopy
from typing import List
from ses_provider import SESProvider


class DkimTokensProvider(SESProvider):
    def __init__(self):
        super().__init__()

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
        if not self.identity_already_exists():
            self.fail(f"the domain identity {self.domain} does not exist")
            return

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
        if self.identity_already_exists():
            self.get_tokens()

    def delete(self):
        pass


provider = DkimTokensProvider()


def handler(request, context):
    return provider.handle(request, context)
