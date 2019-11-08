import uuid

from ses import handler


def check_dkim_tokens(name, region, response: dict):
    assert response.get("PhysicalResourceId") == f"{name.rstrip('.')}@{region}"
    data = response.get("Data", {})
    dkim_tokens = data.get("DkimTokens")
    dns_record_names = data.get("DNSRecordNames")
    dns_record_types = data.get("DNSRecordTypes")
    dns_resource_records = data.get("DNSResourceRecords")
    assert isinstance(dkim_tokens, list), "DkimTokens should be a list"
    assert isinstance(dns_record_names, list), "DNSRecordNames should be a list"
    assert isinstance(dns_record_types, list), "DNSRecordTypes should be list"
    assert isinstance(dns_resource_records, list), "DNSRecordRecords should be list"
    assert not list(
        filter(lambda t: t != "CNAME", dns_record_types)
    ), "DNSResourceTypes should all be CNAME"
    for i, rr in enumerate(dns_resource_records):
        assert isinstance(rr, list), "DNSResourceRecords {i} should a list"
        assert len(rr) == 1, "expected the list to be of length 1"
        assert isinstance(rr[0], str), "expected ResourceRecord to be str"
        value = rr[0]
        assert value == f"{dkim_tokens[i]}.dkim.amazonses.com"

    for i, dns_name in enumerate(dns_record_names):
        assert dns_name == f"{dkim_tokens[i]}._domainkey.{name}."


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
