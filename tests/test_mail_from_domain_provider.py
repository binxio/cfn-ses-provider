import uuid
import json

from mail_from_domain_provider import MailFromDomainProvider


def test_request_schema_has_correct_additional_properties():
    mail_from_provider = MailFromDomainProvider()
    assert "required" in mail_from_provider.request_schema
    assert "Domain" in mail_from_provider.request_schema["required"]
    assert "Region" in mail_from_provider.request_schema["required"]
    assert "MailFromSubdomain" in mail_from_provider.request_schema["required"]
    assert "properties" in mail_from_provider.request_schema
    assert "MailFromSubdomain" in mail_from_provider.request_schema["properties"]
    assert "BehaviorOnMXFailure" in mail_from_provider.request_schema["properties"]


def test_generate_dns_recordsets_returns_empty_when_no_subdomain():
    mail_from_provider = MailFromDomainProvider()
    request = Request("Create", "example.com", "")
    mail_from_provider.set_request(request, {})
    assert mail_from_provider.is_valid_request()
    assert mail_from_provider.domain == "example.com"
    assert mail_from_provider.mail_from_subdomain == ""
    recordsets = mail_from_provider.generate_dns_recordsets()
    assert len(recordsets) == 0


def test_generate_dns_recordsets_returns_values_when_subdomain():
    mail_from_provider = MailFromDomainProvider()
    request = Request("Create", "example.com", "mail")
    mail_from_provider.set_request(request, {})
    assert mail_from_provider.is_valid_request()
    assert mail_from_provider.domain == "example.com"
    assert mail_from_provider.mail_from_subdomain == "mail"

    recordsets = mail_from_provider.generate_dns_recordsets()
    print(json.dumps(recordsets, indent=2))
    assert len(recordsets) == 2
    expected_mx = {
        "Name": "mail.example.com.",
        "ResourceRecords": ["10 feedback-smtp.eu-west-1.amazonses.com"],
        "TTL": "60",
        "Type": "MX",
    }

    expected_txt = {
        "Name": "mail.example.com.",
        "ResourceRecords": ['"v=spf1 include:amazonses.com ~all"'],
        "TTL": "60",
        "Type": "TXT",
    }

    assert expected_mx in recordsets
    assert expected_txt in recordsets


class Request(dict):
    def __init__(
        self,
        request_type,
        domain=None,
        mail_from_subdomain="",
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
                "ResourceType": "Custom::MailFromDomain",
                "LogicalResourceId": "MyMailFromDomain",
                "ResourceProperties": {
                    "Domain": domain,
                    "MailFromSubdomain": mail_from_subdomain,
                },
            }
        )
        if region:
            self["ResourceProperties"]["Region"] = region

        self["PhysicalResourceId"] = (
            physical_resource_id
            if physical_resource_id
            else "initial-%s" % str(uuid.uuid4())
        )
