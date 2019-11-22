import os
import sys
import time

import boto3
import json
from cfn_resource_provider import ResourceProvider
import logging


lmbda = boto3.client("lambda")


class VerifiedIdentityProvider(ResourceProvider):
    def __init__(self):
        super(VerifiedIdentityProvider, self).__init__()
        self.request_schema = {
            "type": "object",
            "required": ["Identity", "Region"],
            "properties": {
                "Identity": {"type": "string", "description": "to await verification"},
                "Region": {"type": "string", "description": "of to the identity"},
            },
        }
        self._ses = None
        self.interval_in_seconds = int(os.getenv("INTERVAL_IN_SECONDS", "15"))

    @property
    def identity(self):
        return self.get("Identity").rstrip(".")

    @property
    def region(self):
        return self.get("Region")

    @property
    def ses(self):
        if not self._ses or self._ses.meta.region_name != self.region:
            self._ses = boto3.client("ses", region_name=self.region)
        return self._ses

    def check(self):
        self.physical_resource_id = self.identity
        response = self.ses.get_identity_verification_attributes(
            Identities=[self.identity]
        )
        attrs = response["VerificationAttributes"].get(self.identity, {})
        status = attrs.get("VerificationStatus")
        logging.info(
            f'Verification of identity "{self.identity}" in region {self.region} is in state {status}.'
        )
        if status == "Success":
            self.success(
                f'identity "{self.identity}" in region {self.region} is verified.'
            )
            self.set_attribute("Region", self.region)
            self.set_attribute("Identity", self.identity)
            self.set_attribute("VerificationToken", attrs.get("VerificationToken"))
            self.set_attribute("VerificationStatus", attrs.get("VerificationStatus`"))
        elif status == "Pending":
            self.async_reinvoke()
        else:
            if status:
                self.fail(
                    f'Verification of identity "{self.identity}" in region {self.region} failed, state {status}.'
                )
            else:
                self.fail(
                    f'The identity "{self.identity}" does not exist in region {self.region}.'
                )

    def create(self):
        self.check()

    def update(self):
        self.check()

    def delete(self):
        self.success("nothing to delete")

    def invoke_lambda(self, payload):
        lmbda.invoke(
            FunctionName=self.get("ServiceToken"),
            InvocationType="Event",
            Payload=payload,
        )

    def async_reinvoke(self):
        self.asynchronous = True  ## do not report result to CFN yet
        time.sleep(self.interval_in_seconds)
        self.increment_attempt()
        payload = json.dumps(self.request).encode("utf-8")
        self.invoke_lambda(payload)

    @property
    def attempt(self):
        """ returns the number of attempts waiting for completion """
        return int(self.get("Attempt", 1))

    def increment_attempt(self):
        """ returns the number of attempts waiting for completion """
        self.properties["Attempt"] = self.attempt + 1


provider = VerifiedIdentityProvider()


def handler(request, context):
    return provider.handle(request, context)
