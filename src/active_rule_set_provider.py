import boto3
import logging
from cfn_resource_provider import ResourceProvider


request_schema = {
    "type": "object",
    "required": ["RuleSetName", "Region"],
    "properties": {
        "RuleSetName": {"type": "string", "description": "to activate"},
        "Region": {"type": "string", "description": "of the rule set"},
    },
}


class ActiveReceiptRuleSetProvider(ResourceProvider):
    def __init__(self):
        super().__init__()
        self.request_schema = request_schema
        self._ses = None

    def is_supported_resource_type(self):
        return self.resource_type in [
            "Custom::SESActiveReceiptRuleSet",
            "Custom::ActiveReceiptRuleSet",
        ]

    @property
    def rule_set_name(self):
        return self.get("RuleSetName")

    @property
    def old_rule_set_name(self):
        return self.get_old("RuleSetName", self.rule_set_name)

    @property
    def region(self):
        return self.get("Region")

    @property
    def old_region(self):
        return self.get_old("Region", self.region)

    @property
    def ses(self):
        if not self._ses:
            self._ses = boto3.client("ses", self.region)
        return self._ses

    def get_active_rule_set_name(self):
        response = self.ses.describe_active_receipt_rule_set()
        self.active_rule_set_name = response.get("Metadata", {}).get("Name")

    def activate(self, is_create):
        if is_create:
            self.get_active_rule_set_name()
            if self.active_rule_set_name:
                self.fail(
                    f"active receipt rule set is already set in region {self.region} - {self.active_rule_set_name}"
                )
                return

        self.ses.set_active_receipt_rule_set(RuleSetName=self.rule_set_name)
        self.physical_resource_id = f"active-receipt-rule-set@{self.region}"

    def create(self):
        self.activate(True)

    def update(self):
        self.activate(self.region != self.old_region)

    def delete(self):
        if self.physical_resource_id.startswith("active-receipt-rule-set@"):
            self.ses.set_active_receipt_rule_set()
        else:
            logging.warning(
                f"silently ignoring delete request of active receipt rule set with physical resource id {self.physical_resource_id}"
            )


provider = ActiveReceiptRuleSetProvider()


def handler(request, context):
    return provider.handle(request, context)
