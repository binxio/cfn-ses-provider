import uuid
from copy import copy
import botocore
from botocore.stub import Stubber, ANY
from identity_notifications_provider import handler, provider

attributes = {
    "lists.binx.io": {
        "BounceTopic": "arn:aws:sns:eu-west-1:111111111111:SES_email_bounces",
        "ComplaintTopic": "arn:aws:sns:eu-west-1:222222222222:SES_email_bounces",
        "DeliveryTopic": "arn:aws:sns:eu-west-1:333333333333:SES_email_bounces",
        "ForwardingEnabled": True,
        "HeadersInBounceNotificationsEnabled": True,
        "HeadersInComplaintNotificationsEnabled": True,
        "HeadersInDeliveryNotificationsEnabled": True,
    }
}


def test_set_notifications():
    ses = botocore.session.get_session().create_client("ses", region_name="eu-west-1")
    stubber = Stubber(ses)
    addStubberCreateResponse(stubber, attributes)
    stubber.activate()
    provider._ses = ses

    request = Request("Create", attributes)
    response = handler(request, ())
    assert response["Status"] == "SUCCESS", response["Reason"]
    stubber.assert_no_pending_responses()
    stubber.deactivate()


def test_refusal_to_overwrite_settings():
    ses = botocore.session.get_session().create_client("ses", region_name="eu-west-1")
    stubber = Stubber(ses)
    provider._ses = ses

    stubber.add_response(
        "get_identity_notification_attributes",
        GetIdentityNotificationAttributesResponse(attributes),
        {"Identities": ["lists.binx.io"]},
    )
    stubber.activate()
    provider._ses = ses

    request = Request("Create", attributes)
    response = handler(request, ())
    assert response["Status"] == "FAILED"
    stubber.assert_no_pending_responses()


def test_create_with_override():
    ses = botocore.session.get_session().create_client("ses", region_name="eu-west-1")
    stubber = Stubber(ses)
    provider._ses = ses

    addStubberCreateResponse(stubber, attributes, override=True)
    stubber.activate()
    request = Request("Create", attributes)
    request["ResourceProperties"]["ForceOverride"] = True
    response = handler(request, ())
    assert response["Status"] == "SUCCESS", response["Reason"]
    stubber.assert_no_pending_responses()


def test_delete():
    ses = botocore.session.get_session().create_client("ses", region_name="eu-west-1")
    stubber = Stubber(ses)
    provider._ses = ses

    addStubberDeleteResponse(stubber, attributes)
    stubber.activate()
    request = Request("Delete", attributes)
    response = handler(request, ())
    assert response["Status"] == "SUCCESS", response["Reason"]
    stubber.assert_no_pending_responses()


class Request(dict):
    def __init__(self, request_type, attributes, physical_resource_id=None):
        request_id = "request-%s" % uuid.uuid4()
        self.update(
            {
                "RequestType": request_type,
                "ResponseURL": "https://httpbin.org/put",
                "StackId": "arn:aws:cloudformation:us-west-2:EXAMPLE/stack-name/guid",
                "RequestId": request_id,
                "ResourceType": "Custom::IdentityNotifications",
                "LogicalResourceId": "IdentityNotifications",
            }
        )

        if physical_resource_id:
            self["PhysicalResourceId"] = physical_resource_id

        for identity, notifications in attributes.items():
            self["ResourceProperties"] = {}
            self["ResourceProperties"].update(notifications)
            self["ResourceProperties"]["Identity"] = identity
            self["ResourceProperties"]["Region"] = "eu-west-1"


class GetIdentityNotificationAttributesResponse(dict):
    def __init__(self, attributes=None, metadata=None):
        self["NotificationAttributes"] = attributes if attributes else {}
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


class SetIdentityHeadersInNotificationsEnabledResponse(dict):
    def __init__(self):
        self["ResponseMetadata"] = {
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


class SetIdentityNotificationTopicResponse(dict):
    def __init__(self):
        self["ResponseMetadata"] = {
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


class SetIdentityHeadersInNotificationsEnabledResponse(dict):
    def __init__(self):
        self["ResponseMetadata"] = {
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


def addStubberCreateResponse(
    stubber, attributes, current_attributes={}, override=False
):
    for identity, notifications in attributes.items():
        if not override:
            stubber.add_response(
                "get_identity_notification_attributes",
                GetIdentityNotificationAttributesResponse(current_attributes),
                {"Identities": [identity]},
            )

        for notification_type in ["Bounce", "Complaint", "Delivery"]:
            topic = notifications.get(f"{notification_type}Topic")
            args = {"Identity": identity, "NotificationType": notification_type}
            if topic:
                args["SnsTopic"] = topic
            stubber.add_response(
                "set_identity_notification_topic",
                SetIdentityNotificationTopicResponse(),
                copy(args),
            )
            if topic:
                args.pop("SnsTopic")
                args["Enabled"] = notifications.get(
                    f"HeadersIn{notification_type}NotificationsEnabled"
                )
                stubber.add_response(
                    "set_identity_headers_in_notifications_enabled",
                    SetIdentityNotificationTopicResponse(),
                    copy(args),
                )
        stubber.add_response(
            "set_identity_feedback_forwarding_enabled",
            SetIdentityNotificationTopicResponse(),
            {
                "Identity": identity,
                "ForwardingEnabled": notifications.get("ForwardingEnabled"),
            },
        )


def addStubberDeleteResponse(stubber, attributes):
    for identity, notifications in attributes.items():
        stubber.add_response(
            "set_identity_feedback_forwarding_enabled",
            SetIdentityNotificationTopicResponse(),
            {"Identity": identity, "ForwardingEnabled": True},
        )
        for notification_type in ["Bounce", "Complaint", "Delivery"]:
            topic = notifications.get(f"{notification_type}Topic")
            args = {"Identity": identity, "NotificationType": notification_type}
            stubber.add_response(
                "set_identity_notification_topic",
                SetIdentityNotificationTopicResponse(),
                copy(args),
            )
