import uuid
import boto3

from identity_policy_provider import handler


def test_create():
    identity = f"{uuid.uuid4()}.internal"
    account_id = (boto3.client("sts")).get_caller_identity()["Account"]
    region = "eu-west-1"

    try:
        request = Request("Create", identity, account_id, region)
        response = handler(request, {})
        assert response["Status"] == "SUCCESS", response["Reason"]
        assert response.get("PhysicalResourceId") == "MyPolicy"

    finally:
        request = Request(
            "Delete", identity, account_id, region, physical_resource_id="{identity}@{region}"
        )
        response = handler(request, {})
        assert response["Status"] == "SUCCESS", response["Reason"]


class Request(dict):
    def __init__(self, request_type, identity, account_id, region="eu-west-1", physical_resource_id=None):
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
                                    "AWS": [
                                        "arn:aws:iam::245111612214:root"
                                    ]
                                },
                                "Action": [
                                    "ses:SendEmail",
                                    "ses:SendRawEmail"
                                ],
                                "Resource": f"arn:aws:ses:{region}:{account_id}:identity/{identity}"
                            }
                        ]
                    }
                }
            }
        )

        if physical_resource_id:
            self["PhysicalResourceId"] = physical_resource_id
