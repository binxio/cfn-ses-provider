import boto3
from copy import deepcopy
from botocore.exceptions import ClientError
from cfn_resource_provider import ResourceProvider


request_schema = {
    "type": "object",
    "required": ["Domain", "Region"],
    "properties": {
        "Domain": {"type": "string", "description": "to get tokens for"},
        "Region": {"type": "string", "description": "of the SES endpoint to use"},
        "RecordSetDefaults": {"type": "object", "default": {"TTL": "60"}},
    },
}


class SESProvider(ResourceProvider):
    def __init__(self):
        super().__init__()
        self.request_schema = request_schema

    @property
    def domain(self):
        return self.get("Domain").rstrip(".")

    @property
    def old_domain(self):
        return self.get_old("Domain", self.domain).rstrip(".")

    @property
    def region(self):
        return self.get("Region")

    @property
    def old_region(self):
        return self.get_old("Region", self.region)

    def identity_already_exists(self) -> bool:
        ses = boto3.client("ses", region_name=self.region)
        for response in ses.get_paginator("list_identities").paginate(
            IdentityType="Domain"
        ):
            exists = list(filter(lambda d: d == self.domain, response["Identities"]))
            if exists:
                return True
        return False
