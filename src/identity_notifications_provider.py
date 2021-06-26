import logging

import boto3
from cfn_resource_provider import ResourceProvider

sts = boto3.client("sts")

request_schema = {
    "type": "object",
    "required": ["Identity", "Region"],
    "properties": {
        "Identity": {"type": "string", "description": "to set the notifications for"},
        "Region": {"type": "string", "description": "of the identity"},
        "BounceTopic": {
            "type": "string",
            "description": "SNS topic ARN to send Bounce notifications to",
            "pattern": "arn:[^:]*:sns:[^:][^:]*:[0-9][0-9]*:[^:][^:]*",
        },
        "ComplaintTopic": {
            "type": "string",
            "description": "SNS topic ARN to send Complaint notifications to",
            "pattern": "arn:[^:]*:sns:[^:][^:]*:[0-9][0-9]*:[^:][^:]*",
        },
        "DeliveryTopic": {
            "type": "string",
            "description": "SNS topic ARN to send Delivery notifications to",
            "pattern": "arn:[^:]*:sns:[^:][^:]*:[0-9][0-9]*:[^:][^:]*",
        },
        "ForwardingEnabled": {
            "type": "boolean",
            "description": "set notification forwarding enabled",
            "default": True,
        },
        "HeadersInBounceNotificationsEnabled": {
            "type": "boolean",
            "description": "include headers in bounce notifications",
            "default": False,
        },
        "HeadersInComplaintNotificationsEnabled": {
            "type": "boolean",
            "description": "include headers in complaint notifications",
            "default": False,
        },
        "HeadersInDeliveryNotificationsEnabled": {
            "type": "boolean",
            "description": "include headers in delivery notifications",
            "default": False,
        },
        "ForceOverride": {
            "type": "boolean",
            "description": "existing notifications settings",
            "default": False,
        },
    },
}


class IdentityNotificationsProvider(ResourceProvider):
    def __init__(self):
        super().__init__()
        self.request_schema = request_schema
        self._ses = None

    def convert_property_types(self):
        self.heuristic_convert_property_types(self.properties)

    @property
    def identity(self):
        return self.get("Identity").rstrip(".")

    @property
    def old_identity(self):
        return self.get_old("Identity", self.identity).rstrip(".")

    @property
    def region(self):
        return self.get("Region")

    @property
    def old_region(self):
        return self.get_old("Region", self.region)

    @property
    def account_id(self):
        response = sts.get_caller_identity()
        return response["Account"]

    @property
    def arn(self):
        return f"arn::ses:{self.region}:{self.account_id}:identity/{self.identity}"

    @property
    def ses(self):
        if not self._ses or self._ses.meta.region_name != self.region:
            self._ses = boto3.client("ses", region_name=self.region)
        return self._ses

    def check_precondition(self):
        if self.get("ForceOverride"):
            logging.info(
                f"ForceOverride of notification settings for {self.identity} in {self.region} requested"
            )
            return True

        if self.request_type == "Create" or (
            self.request_type == "Update"
            and self.region != self.old_region
            or self.identity != self.old_identity
        ):
            response = self.ses.get_identity_notification_attributes(
                Identities=[self.identity]
            )
            attrs = response["NotificationAttributes"].get(self.identity)
            if not attrs:
                return True

            for topic in ["BounceTopic", "ComplaintTopic", "DeliveryTopic"]:
                if topic in attrs:
                    self.fail(
                        f"{topic} already set for identity {self.identity} in {self.region}"
                    )
                    return False

            if not self.get("ForwardingEnabled") and not (
                self.get("BounceTopic") and self.get("ComplaintTopic")
            ):
                self.fail(
                    "ForwardingEnabled cannot be disabled without an SNS BounceTopic and SNS ComplaintTopic"
                )
                return False

        return True

    def set_notifications(self):
        for notification_type in ["Bounce", "Complaint", "Delivery"]:
            topic = self.get(f"{notification_type}Topic")
            kwargs = {"Identity": self.identity, "NotificationType": notification_type}
            if topic:
                kwargs["SnsTopic"] = topic
            self.ses.set_identity_notification_topic(**kwargs)
            self.physical_resource_id = self.arn

            if topic:
                kwargs.pop("SnsTopic")
                kwargs["Enabled"] = self.get(
                    f"HeadersIn{notification_type}NotificationsEnabled"
                )
                self.ses.set_identity_headers_in_notifications_enabled(**kwargs)

        self.ses.set_identity_feedback_forwarding_enabled(
            Identity=self.identity, ForwardingEnabled=self.get("ForwardingEnabled")
        )

    def clear_notifications(self):
        self.ses.set_identity_feedback_forwarding_enabled(
            Identity=self.identity, ForwardingEnabled=True
        )
        for notification_type in ["Bounce", "Complaint", "Delivery"]:
            self.ses.set_identity_notification_topic(
                Identity=self.identity, NotificationType=notification_type
            )

    def create(self):
        if self.check_precondition():
            self.set_notifications()

    def update(self):
        if self.check_precondition():
            self.set_notifications()

    def delete(self):
        if self.physical_resource_id != "could-not-create":
            self.clear_notifications()


provider = IdentityNotificationsProvider()


def handler(request, context):
    return provider.handle(request, context)
