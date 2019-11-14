import time
import uuid

import boto3
import pytest

from ses import handler

ses = boto3.client("ses", region_name="eu-west-1")
route53 = boto3.client("route53")


@pytest.fixture
def hosted_zone():
    hosted_zone_name = "%s.internal." % str(uuid.uuid4())
    hosted_zone_id = None
    try:
        response = route53.create_hosted_zone(
            Name=hosted_zone_name, CallerReference=hosted_zone_name
        )
        hosted_zone_id = response["HostedZone"]["Id"]
        wait_for_change_completion(response["ChangeInfo"]["Id"])
        yield (hosted_zone_name, hosted_zone_id)
    finally:
        if hosted_zone_id:
            try:
                # delete_all_resource_record_sets(hosted_zone_id, hosted_zone_name)
                route53.delete_hosted_zone(Id=hosted_zone_id)
            except Exception as e:
                print(e)


def delete_all_resource_record_sets(hosted_zone_id, hosted_zone_name):
    for response in route53.get_paginator("list_resource_record_sets").paginate():
        changes = list(
            map(
                lambda r: {"Action": "DELETE", "ResourceRecordSet": r},
                filter(
                    lambda r: r["Type"] not in ["SOA", "NS"]
                    and r["Name"] == hosted_zone_name,
                    response["ResourceRecordSets"],
                ),
            )
        )
    if changes:
        change_info = route53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id, ChangeBatch={"Changes": changes}
        )
        wait_for_change_completion(change_info["Id"])


def wait_for_change_completion(change_id):
    while not (route53.get_change(Id=change_id)["ChangeInfo"]["Status"] == "INSYNC"):
        time.sleep(3)


def create_for_domain(hosted_zone_name, hosted_zone_id, domain_name):
    dkim_domain = (
        domain_name.rstrip(".") if domain_name else hosted_zone_name.rstrip(".")
    )
    if domain_name:
        request = Request("Create", hosted_zone_id, domain_name)
    else:
        request = Request("Create", hosted_zone_id)

    response = handler(request, {})
    assert response["Status"] == "SUCCESS", response["Reason"]

    identities = list(
        filter(
            lambda i: i == dkim_domain,
            ses.list_identities(IdentityType="Domain")["Identities"],
        )
    )
    assert len(identities) == 1, (
        "could not find domain %s as SES identity" % dkim_domain
    )

    physical_resource_id = response["PhysicalResourceId"]
    if domain_name and dkim_domain != hosted_zone_name.rstrip("."):
        assert physical_resource_id == f"{dkim_domain}@{hosted_zone_id}"
    else:
        assert physical_resource_id == hosted_zone_id

    records = route53.list_resource_record_sets(HostedZoneId=hosted_zone_id)[
        "ResourceRecordSets"
    ]
    ses_verification_record = list(
        filter(lambda r: r["Name"] == "_amazonses.%s." % dkim_domain, records)
    )
    dkim_verification_records = list(
        filter(lambda r: r["Name"].endswith("._domainkey.%s." % dkim_domain), records)
    )
    assert len(ses_verification_record) == 1, (
        "could not find _amazonses.%s record" % dkim_domain
    )
    assert len(dkim_verification_records) > 0, (
        "could not find any _domainkey.%s records" % dkim_domain
    )

    ## re-insert of existing domain should fail
    response = handler(request, {})
    assert response["Status"] == "FAILED", response["Reason"]
    assert response["Reason"] == f"SES domain identity {dkim_domain} already exists"

    if not domain_name:
        request = Request("Create", hosted_zone_id, dkim_domain)
        response = handler(request, {})
        assert response["Status"] == "FAILED", response["Reason"]
        assert response["Reason"] == f"SES domain identity {dkim_domain} already exists"

    request = Request(
        "Update", hosted_zone_id, physical_resource_id=physical_resource_id
    )
    response = handler(request, {})
    assert response["Status"] == "SUCCESS", response["Reason"]
    if domain_name and dkim_domain != hosted_zone_name.rstrip("."):
        assert physical_resource_id == f"{dkim_domain}@{hosted_zone_id}"
    else:
        assert physical_resource_id == hosted_zone_id

    request = Request(
        "Delete", hosted_zone_id, physical_resource_id=physical_resource_id
    )
    response = handler(request, {})
    assert response["Status"] == "SUCCESS", response["Reason"]

    if domain_name and dkim_domain != hosted_zone_name.rstrip("."):
        assert physical_resource_id == f"{dkim_domain}@{hosted_zone_id}"
    else:
        assert physical_resource_id == hosted_zone_id

    identities = list(
        filter(
            lambda i: i == dkim_domain,
            ses.list_identities(IdentityType="Domain")["Identities"],
        )
    )
    assert len(identities) == 0, (
        "domain %s is still present as a SES identity" % dkim_domain
    )

    records = route53.list_resource_record_sets(HostedZoneId=hosted_zone_id)[
        "ResourceRecordSets"
    ]
    ses_verification_record = list(
        filter(lambda r: r["Name"] == "_amazonses.%s." % dkim_domain, records)
    )
    dkim_verification_records = list(
        filter(lambda r: r["Name"].endswith("._domainkey.%s." % dkim_domain), records)
    )
    assert len(ses_verification_record) == 0, (
        "_amazonses.%s record still present" % dkim_domain
    )
    assert len(dkim_verification_records) == 0, (
        "_domainkey.%s records still present" % dkim_domain
    )


def test_create_for_hosted_zone(hosted_zone):
    name, hosted_zone_id = hosted_zone
    create_for_domain(name, hosted_zone_id, None)


def test_create_with_half_a_hosted_zone_id(hosted_zone):
    name, hosted_zone_id = hosted_zone
    id_to_use = hosted_zone_id.split("/")[-1]
    create_for_domain(name, id_to_use, None)


def test_create_for_domain_in_hosted_zone(hosted_zone):
    name, hosted_zone_id = hosted_zone
    create_for_domain(name, hosted_zone_id, f"mail.{name}")


class Request(dict):
    def __init__(
        self, request_type, hosted_zone_id, domain_name=None, physical_resource_id=None
    ):
        request_id = "request-%s" % uuid.uuid4()
        self.update(
            {
                "RequestType": request_type,
                "ResponseURL": "https://httpbin.org/put",
                "StackId": "arn:aws:cloudformation:us-west-2:EXAMPLE/stack-name/guid",
                "RequestId": request_id,
                "ResourceType": "Custom::DKIM",
                "LogicalResourceId": "MyDKIM",
                "ResourceProperties": {"HostedZoneId": hosted_zone_id},
            }
        )
        if domain_name:
            self["ResourceProperties"]["Domain"] = domain_name

        self["PhysicalResourceId"] = (
            physical_resource_id
            if physical_resource_id is not None
            else "initial-%s" % str(uuid.uuid4())
        )
