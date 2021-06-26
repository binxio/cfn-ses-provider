import pytest

from identity_policy_provider import provider, request_schema
import uuid, json

def test_wildcard():
        identity = f"{uuid.uuid4()}.internal"
        provider.set_request(Request("Create", identity, "*"), {})
        assert provider.is_valid_request(), provider.reason

def test_simple_root():
    identity = f"{uuid.uuid4()}.internal"
    request = Request("Create", identity, {"AWS": "arn:aws:iam::245111612214:root"})
    provider.set_request(request, {})
    assert provider.is_valid_request(), provider.reason

def test_list_of_aws_root():
    identity = f"{uuid.uuid4()}.internal"
    request = Request("Create", identity, {"AWS": ["arn:aws:iam::245111612214:root", "arn:aws:iam::245111612215:root"]})
    provider.set_request(request, {})
    assert provider.is_valid_request(), provider.reason

def test_services():
    identity = f"{uuid.uuid4()}.internal"
    request = Request("Create", identity, {"Service": "ecs.amazonaws.com"})
    provider.set_request(request, {})
    assert provider.is_valid_request(), provider.reason

def test_list_of_services():
    identity = f"{uuid.uuid4()}.internal"
    request = Request("Create", identity, {"Service": ["ecs.amazonaws.com", "eks.amazonaws.com"]})
    provider.set_request(request, {})
    assert provider.is_valid_request(), provider.reason

def test_list_of_federated():
    identity = f"{uuid.uuid4()}.internal"
    request = Request("Create", identity, {"Federated": ["ecs.amazonaws.com", "eks.amazonaws.com"]})
    provider.set_request(request, {})
    assert provider.is_valid_request(), provider.reason

def test_canonical_user():
    identity = f"{uuid.uuid4()}.internal"
    request = Request("Create", identity, {"CanonicalUser": "dfjsdfskdfsfdhjsdfkjsdfjk"})
    provider.set_request(request, {})
    assert provider.is_valid_request(), provider.reason

def test_invalid_principal():
    identity = f"{uuid.uuid4()}.internal"
    request = Request("Create", identity, {"FederatedUser": ["ecs.amazonaws.com", "eks.amazonaws.com"]})
    provider.set_request(request, {})
    assert not provider.is_valid_request(), provider.reason

class Request(dict):
    def __init__(self, request_type, identity, principals):
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
                                "Principal": "*",
                                "Action": [
                                    "ses:SendEmail",
                                    "ses:SendRawEmail"
                                ],
                                "Resource": "*"
                            }
                        ]
                    }
                }
            }
        )
        self["ResourceProperties"]["PolicyDocument"]["Statement"][0]["Principal"] = principals
