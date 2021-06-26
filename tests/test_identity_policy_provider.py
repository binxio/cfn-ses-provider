import uuid
import boto3
import pytest
import logging

from identity_policy_provider import handler
from test_domain_identity_provider import Request as DomainIdentityRequest
from domain_identity_provider import handler as domain_identity_provider


@pytest.fixture
def domain_identity():
    identity = f"{uuid.uuid4()}.internal"
    region = "eu-central-1"
    try:
        response = domain_identity_provider(
            DomainIdentityRequest("Create", identity, region), {}
        )
        yield response
    finally:
        request = DomainIdentityRequest(
            "Delete",
            identity,
            region=region,
            physical_resource_id=f"{identity.rstrip('.')}@{region}",
        )
        response = domain_identity_provider(request, {})
        if response["Status"] != "SUCCESS":
            logging.error("failed to delete domain identity, %s", response["Reason"])


def test_create(domain_identity):
    account_id = (boto3.client("sts")).get_caller_identity()["Account"]
    region = domain_identity["Data"]["Region"]
    identity = domain_identity["Data"]["Domain"]

    try:
        request = Request("Create", identity, account_id, region)
        response = handler(request, {})
        assert response["Status"] == "SUCCESS", response["Reason"]
        assert response.get("PhysicalResourceId") == f"{identity}/@MyPolicy"

    finally:
        request = Request(
            "Delete",
            identity,
            account_id,
            region,
            physical_resource_id=f"{identity}/@{region}",
        )
        response = handler(request, {})
        assert response["Status"] == "SUCCESS", response["Reason"]


class Request(dict):
    def __init__(
        self,
        request_type,
        identity,
        account_id,
        region="eu-west-1",
        physical_resource_id=None,
    ):
        request_id = "request-%s" % uuid.uuid4()
        self.update(
            {
                "RequestType": request_type,
                "ResponseURL": "https://httpbin.org/put",
                "StackId": "arn:aws:cloudformation:us-west-2:EXAMPLE/stack-name/guid",
                "RequestId": request_id,
                "ResourceType": "Custom::IdentityPolicy",
                "LogicalResourceId": "Record",
                "ResourceProperties": {
                    "Identity": identity,
                    "PolicyName": "MyPolicy",
                    "PolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {
                                    "AWS": ["arn:aws:iam::245111612214:root"]
                                },
                                "Action": ["ses:SendEmail", "ses:SendRawEmail"],
                                "Resource": f"arn:aws:ses:{region}:{account_id}:identity/{identity}",
                            }
                        ],
                    },
                },
            }
        )

        if physical_resource_id:
            self["PhysicalResourceId"] = physical_resource_id
