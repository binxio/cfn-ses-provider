import uuid

from ses import handler


def check_dkim_tokens(name, region, response: dict):
    assert response.get("PhysicalResourceId") == f"{name.rstrip('.')}@{region}"
    data = response.get("Data", {})
    dkim_tokens = data.get("DkimTokens")
    assert isinstance(dkim_tokens, list), "DkimTokens should be a list"
    record_sets = data.get("RecordSets")
    assert isinstance(record_sets, list), "RecordSets should be a list"

    for i, record_set in enumerate(record_sets):
        assert record_set["Name"] == f"{dkim_tokens[i]}._domainkey.{name}."
        assert record_set["Type"] == "CNAME"
        assert record_set["TTL"] == "60"
        assert record_set["ResourceRecords"] == [f"{dkim_tokens[i]}.dkim.amazonses.com"]


def test_create():
    name = f"{uuid.uuid4()}.internal"
    try:
        request = Request("Create", name)
        response = handler(request, {})
        assert response["Status"] == "SUCCESS", response["Reason"]
        check_dkim_tokens(name, "eu-west-1", response)

        # try duplicate create
        response = handler(request, {})
        assert response["Status"] == "SUCCESS", response["Reason"]
        check_dkim_tokens(name, "eu-west-1", response)

        request["RequestType"] = "Update"
        request["OldResourceProperties"] = {"Region": "eu-west-1"}
        request["ResourceProperties"]["Region"] = "eu-central-1"
        response = handler(request, {})
        assert response["Status"] == "SUCCESS", response["Reason"]
        check_dkim_tokens(name, "eu-central-1", response)

    finally:
        for region in ["eu-west-1", "eu-central-1"]:
            request = Request(
                "Delete", name, region=region, physical_resource_id="{name}@{region}"
            )
            response = handler(request, {})
            assert response["Status"] == "SUCCESS", response["Reason"]


class Request(dict):
    def __init__(
        self, request_type, domain=None, region="eu-west-1", physical_resource_id=None
    ):
        request_id = "request-%s" % uuid.uuid4()
        self.update(
            {
                "RequestType": request_type,
                "ResponseURL": "https://httpbin.org/put",
                "StackId": "arn:aws:cloudformation:us-west-2:EXAMPLE/stack-name/guid",
                "RequestId": request_id,
                "ResourceType": "Custom::DkimTokens",
                "LogicalResourceId": "MyDkimTokens",
                "ResourceProperties": {"Domain": domain},
            }
        )
        if region:
            self["ResourceProperties"]["Region"] = region

        self["PhysicalResourceId"] = (
            physical_resource_id
            if physical_resource_id
            else "initial-%s" % str(uuid.uuid4())
        )
