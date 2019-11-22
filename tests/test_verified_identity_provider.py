import uuid
import botocore
from botocore.stub import Stubber, ANY
from verified_identity_provider import handler, provider


def test_no_such_identity():
    ses = botocore.session.get_session().create_client("ses", region_name="eu-west-1")
    stubber = Stubber(ses)
    stubber.add_response(
        "get_identity_verification_attributes",
        GetIdentityVerificationAttributesReponse(),
        {"Identities": ["lists.binx.io"]},
    )
    stubber.activate()
    provider._ses = ses
    counter = Counter()
    provider.invoke_lambda = counter.increment

    request = Request("Create", "lists.binx.io", "eu-west-1")
    response = handler(request, ())
    assert response["Status"] == "FAILED", response["Reason"]
    assert not provider.asynchronous
    stubber.assert_no_pending_responses()


def test_verification_failed():
    ses = botocore.session.get_session().create_client("ses", region_name="eu-west-1")
    stubber = Stubber(ses)
    stubber.add_response(
        "get_identity_verification_attributes",
        GetIdentityVerificationAttributesReponse(
            {
                "lists.binx.io": {
                    "VerificationStatus": "Failed",
                    "VerificationToken": "123",
                }
            }
        ),
        {"Identities": ["lists.binx.io"]},
    )
    stubber.activate()
    provider._ses = ses
    counter = Counter()
    provider.invoke_lambda = counter.increment
    assert provider.interval_in_seconds == 15
    provider.interval_in_seconds = 1

    request = Request("Create", "lists.binx.io", "eu-west-1")
    response = handler(request, ())
    assert response["Status"] == "FAILED", response["Reason"]
    assert not provider.asynchronous
    stubber.assert_no_pending_responses()


def test_await_pending_completion():
    ses = botocore.session.get_session().create_client("ses", region_name="eu-west-1")
    stubber = Stubber(ses)
    stubber.add_response(
        "get_identity_verification_attributes",
        GetIdentityVerificationAttributesReponse(
            {
                "lists.binx.io": {
                    "VerificationStatus": "Pending",
                    "VerificationToken": "123",
                }
            }
        ),
        {"Identities": ["lists.binx.io"]},
    )
    stubber.add_response(
        "get_identity_verification_attributes",
        GetIdentityVerificationAttributesReponse(
            {
                "lists.binx.io": {
                    "VerificationStatus": "Success",
                    "VerificationToken": "123",
                }
            }
        ),
        {"Identities": ["lists.binx.io"]},
    )
    stubber.activate()
    provider._ses = ses
    counter = Counter()
    provider.invoke_lambda = counter.increment

    request = Request("Create", "lists.binx.io", "eu-west-1")
    response = handler(request, ())
    assert provider.asynchronous, response["Status"]
    assert counter.count == 1

    request = Request("Create", "lists.binx.io", "eu-west-1")
    response = handler(request, ())
    assert response["Status"] == "SUCCESS", response["Reason"]
    stubber.assert_no_pending_responses()

    assert not provider.asynchronous, response["Reason"]
    assert counter.count == 1


class Counter(object):
    def __init__(self):
        self.count = 0

    def increment(self, *args, **kwargs):
        self.count += 1


class Request(dict):
    def __init__(self, request_type, identity, region, physical_resource_id=None):
        request_id = "request-%s" % uuid.uuid4()
        self.update(
            {
                "RequestType": request_type,
                "ResponseURL": "https://httpbin.org/put",
                "StackId": "arn:aws:cloudformation:us-west-2:EXAMPLE/stack-name/guid",
                "RequestId": request_id,
                "ResourceType": "Custom::VerifiedIdentity",
                "LogicalResourceId": "VerifiedIdentity",
                "ResourceProperties": {"Identity": identity, "Region": region},
            }
        )

        if physical_resource_id:
            self["PhysicalResourceId"] = physical_resource_id


class GetIdentityVerificationAttributesReponse(dict):
    def __init__(self, attributes=None, metadata=None):
        self["VerificationAttributes"] = attributes if attributes else {}
        if not metadata:
            metadata = {
                "RequestId": "2c7bd3fe-730c-4d24-b9a5-1942193a091a",
                "HTTPStatusCode": 200,
                "HTTPHeaders": {
                    "x-amzn-requestid": "2c7bd3fe-730c-4d24-b9a5-1942193a091a",
                    "content-type": "text/xml",
                    "content-length": "275",
                    "date": "Sat, 16 Nov 2019 17:58:29 GMT",
                },
                "RetryAttempts": 0,
            }
        self["ResponseMetadata"] = metadata
