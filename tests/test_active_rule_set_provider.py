import uuid
import datetime
from dateutil.tz import tzutc
import botocore
from botocore.stub import Stubber
from active_rule_set_provider import handler, provider


def test_create_no_existing_rule_set():
    ses = botocore.session.get_session().create_client("ses")
    stubber = Stubber(ses)
    stubber.add_response(
        "describe_active_receipt_rule_set", no_active_receipt_rule_set_response
    )
    stubber.add_response(
        "set_active_receipt_rule_set",
        no_active_receipt_rule_set_response,
        {"RuleSetName": "lists.binx.io"},
    )
    stubber.activate()
    provider._ses = ses
    request = Request("Create", "lists.binx.io")
    response = handler(request, {})
    assert response["Status"] == "SUCCESS", response["Reason"]
    stubber.assert_no_pending_responses()


def test_create_fails_existing_rule_set():
    ses = botocore.session.get_session().create_client("ses")
    stubber = Stubber(ses)
    stubber.add_response(
        "describe_active_receipt_rule_set", active_receipt_rule_set_response
    )
    stubber.activate()
    provider._ses = ses
    request = Request("Create", "lists.binx.io")
    response = handler(request, {})
    assert response["Status"] == "FAILED", response["Reason"]
    assert (
        response["Reason"]
        == "active receipt rule set is already set in region eu-west-1 - lists.binx.io"
    )
    stubber.assert_no_pending_responses()


def test_update_receipt_rule_set():
    ses = botocore.session.get_session().create_client("ses")
    stubber = Stubber(ses)
    stubber.add_response(
        "set_active_receipt_rule_set",
        no_active_receipt_rule_set_response,
        {"RuleSetName": "lists.xebia.com"},
    )
    stubber.activate()
    provider._ses = ses
    request = Request("Update", "lists.xebia.com")
    response = handler(request, {})
    assert response["Status"] == "SUCCESS", response["Reason"]
    stubber.assert_no_pending_responses()


def test_update_receipt_change_region_with_existing_rule_set():
    ses = botocore.session.get_session().create_client("ses")
    stubber = Stubber(ses)
    stubber.add_response(
        "describe_active_receipt_rule_set", active_receipt_rule_set_response
    )
    stubber.activate()
    provider._ses = ses
    request = Request("Update", "lists.xebia.com")
    request["OldResourceProperties"] = {"Region": "us-east-1"}
    response = handler(request, {})
    assert response["Status"] == "FAILED"
    assert (
        response["Reason"]
        == "active receipt rule set is already set in region eu-west-1 - lists.binx.io"
    )
    stubber.assert_no_pending_responses()


def test_activate_receipt_rule_with_rule_set_present():
    ses = botocore.session.get_session().create_client("ses")
    stubber = Stubber(ses)
    stubber.add_response(
        "describe_active_receipt_rule_set", active_receipt_rule_set_response
    )
    stubber.activate()
    provider._ses = ses
    request = Request("Create", "lists.binx.io")
    response = handler(request, {})
    assert response["Status"] == "FAILED", response["Reason"]
    stubber.assert_no_pending_responses()


def test_delete():
    ses = botocore.session.get_session().create_client("ses")
    stubber = Stubber(ses)
    stubber.add_response(
        "set_active_receipt_rule_set", no_active_receipt_rule_set_response, {}
    )
    stubber.activate()
    provider._ses = ses
    request = Request(
        "Delete",
        "lists.binx.io",
        physical_resource_id="active-receipt-rule-set@eu-west-1",
    )
    response = handler(request, {})
    assert response["Status"] == "SUCCESS", response["Reason"]
    stubber.assert_no_pending_responses()


class Request(dict):
    def __init__(
        self,
        request_type,
        ruleset_set_name=None,
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
                "ResourceType": "Custom::SESActiveReceiptRuleSet",
                "LogicalResourceId": "MyReceiptRuleSet",
                "ResourceProperties": {
                    "RuleSetName": ruleset_set_name,
                    "Region": region,
                },
            }
        )

        self["PhysicalResourceId"] = (
            physical_resource_id
            if physical_resource_id
            else "initial-%s" % str(uuid.uuid4())
        )


active_receipt_rule_set_response = {
    "Metadata": {
        "Name": "lists.binx.io",
        "CreatedTimestamp": datetime.datetime(
            2019, 11, 15, 23, 23, 18, 370000, tzinfo=tzutc()
        ),
    },
    "Rules": [
        {
            "Name": "lists.binx.io",
            "Enabled": True,
            "TlsPolicy": "Require",
            "Recipients": ["lists.binx.io"],
            "Actions": [
                {
                    "S3Action": {
                        "BucketName": "dev-mailing-list-archive-binx-io",
                        "ObjectKeyPrefix": "/incoming/",
                    }
                }
            ],
            "ScanEnabled": True,
        }
    ],
    "ResponseMetadata": {
        "RequestId": "84009ed0-52b5-48ce-8a3b-897a3ff72ef1",
        "HTTPStatusCode": 200,
        "HTTPHeaders": {
            "x-amzn-requestid": "84009ed0-52b5-48ce-8a3b-897a3ff72ef1",
            "content-type": "text/xml",
            "content-length": "999",
            "date": "Sat, 16 Nov 2019 17:57:52 GMT",
        },
        "RetryAttempts": 0,
    },
}

no_active_receipt_rule_set_response = {
    "ResponseMetadata": {
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
}
