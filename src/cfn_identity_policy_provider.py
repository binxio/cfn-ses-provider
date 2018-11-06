import boto3
import json
from botocore.exceptions import ClientError, BotoCoreError

from cfn_resource_provider import ResourceProvider


request_schema = {
    "type": "object",
    "required": ["Identity", "PolicyName", "PolicyDocument"],
    "properties": {
        "Identity": {
            "type": "string",
            "description": "that the policy will apply to"
        },
        "PolicyName": {
            "type": "string",
            "description": "of the policy"
        },
        "PolicyDocument": {
            "type": "object",
            "description": "the permissions for the principal",
            "required": ["Statement"],
            "properties": {
                "Statement": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["Effect", "Principal", "Action"],
                        "properties": {
                            "Effect": {
                                "type": "string",
                                "enum": ["Allow", "Deny"]
                            },
                            "Principal": {
                                "type": "object",
                                "oneOf": [{
                                    "required": ["AWS"],
                                    "properties": {
                                        "AWS": {
                                            "type": "string"
                                        }
                                    }
                                }, {
                                    "required": ["AWS"],
                                    "properties": {
                                        "AWS": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }]
                            },
                            "Action": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["ses:SendEmail", "ses:SendRawEmail"]
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}


class IdentityPolicyProvider(ResourceProvider):

    def __init__(self):
        super(IdentityPolicyProvider, self).__init__()
        self.request_schema = request_schema
        self.ses = boto3.client('ses')

    def convert_property_types(self):
        self.heuristic_convert_property_types(self.properties)

    def create(self):
        self.upsert()

    def update(self):
        self.upsert()

    def upsert(self):
        current_policy_document = PolicyDocument.from_json(
            self.get_identity_policy(Identity=self.get('Identity'), PolicyName=self.get('PolicyName')))
        desired_policy_document = PolicyDocument.from_dict(self.get('PolicyDocument'))

        if current_policy_document != desired_policy_document:
            try:
                self.ses.put_identity_policy(
                    Identity=self.get('Identity'),
                    PolicyName=self.get('PolicyName'),
                    Policy=desired_policy_document.to_json())
                self.physical_resource_id = self.get('PolicyName')
            except (BotoCoreError, ClientError) as e:
                self.physical_resource_id = 'failed-to-create'
                self.fail('Failed to put identity policy {policy}'.format(policy=self.get('PolicyName')))

    def delete(self):
        try:
            current_policies = self.ses.list_identity_policies(Identity=self.get('Identity'))['PolicyNames']
        except (BotoCoreError, ClientError) as e:
            self.fail('Failed to list identity policies')
            return

        if self.get('PolicyName') in current_policies:
            try:
                self.ses.delete_identity_policy(Identity=self.get('Identity'), PolicyName=self.get('PolicyName'))
            except (BotoCoreError, ClientError) as e:
                self.fail('Failed to delete identity policy {policy}'.format(policy=self.get('PolicyName')))

    def get_identity_policy(self, Identity, PolicyName):
        try:
            current_policies = self.ses.get_identity_policies(Identity=Identity, PolicyNames=[PolicyName])['Policies']
            return current_policies[PolicyName] if PolicyName in current_policies else None
        except (BotoCoreError, ClientError) as e:
            self.fail('Failed to retrieve identity policy {policy}'.format(policy=PolicyName))


class Statement(object):

    def __init__(self):
        self.Effect = None
        self.Principal = None
        self.Action = None
        self.Resource = None

    @classmethod
    def from_dict(cls, dict):
        policy = cls()
        policy.Effect = dict['Effect'] if 'Effect' in dict else None
        policy.Principal = dict['Principal'] if 'Principal' in dict else None
        policy.Action = dict['Action'] if 'Action' in dict else None
        policy.Resource = dict['Resource'] if 'Resource' in dict else None
        return policy


class PolicyDocument(object):

    def __init__(self):
        self.Version = "2008-10-17"
        self.Statement = []

    @classmethod
    def from_dict(cls, dict):
        document = cls()
        document.Version = dict['Version'] if 'Version' in dict else None
        if 'Statement' in dict:
            for statement in dict['Statement']:
                document.Statement.append(Statement.from_dict(statement))
        return document

    @classmethod
    def from_json(cls, data):
        try:
            dict = json.loads(data)
            return cls.from_dict(dict)
        except:
            return None

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        statements = []
        for statement in self.Statement:
            statements.append(statement.__dict__)
        return {
            'Version': self.Version,
            'Statement': statements
        }

    def __eq__(self, other):
        if other is None:
            return False
        return self.to_dict() == other.to_dict()


provider = IdentityPolicyProvider()


def handler(request, context):
    return provider.handle(request, context)
