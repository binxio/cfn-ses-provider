import uuid

from ses import handler


def check_verification_response(name, region, response: dict):
    assert response.get("PhysicalResourceId") == f"{name.rstrip('.')}@{region}"
    data = response.get("Data", {})
    token = data.get("VerificationToken")
    assert token
    assert data.get("Domain") == name.rstrip(".")
    assert data.get("Region") == region

    record_sets = data.get("RecordSets")
    assert isinstance(record_sets, list)
    assert len(record_sets) == 1
    record_set = record_sets[0]
    assert record_set["Name"] == f"_amazonses.{name}."
    assert record_set["Type"] == "TXT"
    assert record_set["TTL"] == "60"
    assert record_set["ResourceRecords"] == [f'{token}']


def test_create():
    name = f"{uuid.uuid4()}.internal"
    try:
        request = Request("Create", name)
        response = handler(request, {})
        assert response["Status"] == "SUCCESS", response["Reason"]
        check_verification_response(name, "eu-west-1", response)

        # try duplicate create
        response = handler(request, {})
        assert response["Status"] == "FAILED", response["Reason"]
        assert (
            response["Reason"]
            == f"SES domain identity {name} already exists in region eu-west-1"
        )
        request["PhysicalResourceId"] = response.get("PhysicalResourceId")

        request["RequestType"] = "Update"
        request["OldResourceProperties"] = {"Region": "eu-west-1"}
        request["ResourceProperties"]["Region"] = "eu-central-1"
        response = handler(request, {})
        assert response["Status"] == "SUCCESS", response["Reason"]
        check_verification_response(name, "eu-central-1", response)

        # try duplicate update of existing record
        request["ResourceProperties"]["Region"] = "eu-central-1"
        request["OldResourceProperties"] = {"Region": "eu-central-1"}
        request["ResourceProperties"]["Region"] = "eu-west-1"
        response = handler(request, {})
        assert response["Status"] == "FAILED", response["Reason"]
        assert (
            response["Reason"]
            == f"cannot change domain identity to {name} as it already exists in region eu-west-1"
        )

    finally:
        for region in ["eu-west-1", "eu-central-1"]:
            request = Request(
                "Delete",
                name,
                region=region,
                physical_resource_id=f"{name.rstrip('.')}@{region}",
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
                "ResourceType": "Custom::DomainIdentity",
                "LogicalResourceId": "MyDomainIdentity",
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
