import boto3
from botocore.exceptions import ClientError
from cfn_resource_provider import ResourceProvider


request_schema = {
    "type": "object",
    "oneOf": [{
        "required": ["HostedZoneId"],
        "properties": {
            "HostedZoneId": {
                "type": "string",
                "description": "the hosted zone to add to SES"
            },
            "DKIM": {
                "type": "boolean",
                "description": "create domain keys",
                "default": False
            }
        }
    }, {
        "required": ["DomainName"],
        "properties": {
            "DomainName": {
                "type": "string",
                "description": "the domain name to add to SES"
            },
            "DKIM": {
                "type": "boolean",
                "description": "create domain keys",
                "default": False
            }
        }
    }]
}


class DomainProvider(ResourceProvider):

    def __init__(self):
        super(DomainProvider, self).__init__()
        self.request_schema = request_schema
        self.ses = boto3.client('ses')
        self.route53 = boto3.client('route53')

    def create(self):
        self.upsert()

    def update(self):
        self.upsert()

    def delete(self):
        self.delete_identity()

        if self.is_hosted_zone():
            self.delete_dns_records(self.get('HostedZoneId'))

    def convert_property_types(self):
        self.heuristic_convert_property_types(self.properties)

    def delete_identity(self):
        self.ses.delete_identity(Identity=self.get_domain_name())

    def delete_dns_records(self, hosted_zone_id):
        hosted_zone_name = self.get_hosted_zone_name(hosted_zone_id)

        to_delete = []
        paginator = self.route53.get_paginator('list_resource_record_sets')
        for page in paginator.paginate(HostedZoneId=hosted_zone_id):
            for rr in page['ResourceRecordSets']:
                if rr['Type'] == 'CNAME' and rr['Name'].endswith('._domainkey.%s' % hosted_zone_name):
                    to_delete.append(rr)
                elif rr['Type'] == 'TXT' and rr['Name'] == '_amazonses.%s' % hosted_zone_name:
                    to_delete.append(rr)

        if len(to_delete) > 0:
            batch = {'Changes': [{'Action': 'DELETE', 'ResourceRecordSet': rr} for rr in to_delete]}
            r = self.route53.change_resource_record_sets(HostedZoneId=hosted_zone_id, ChangeBatch=batch)
            self.set_attribute('ChangeId', r['ChangeInfo']['Id'])

    def is_hosted_zone(self):
        return self.get('HostedZoneId') is not None

    def get_hosted_zone_name(self, hosted_zone_id):
        response = self.route53.get_hosted_zone(Id=hosted_zone_id)
        return response['HostedZone']['Name']

    def get_domain_name(self):
        if self.is_hosted_zone():
            hosted_zone_name = self.get_hosted_zone_name(self.get('HostedZoneId'))
            return hosted_zone_name.rstrip('.')
        else:
            return self.get('DomainName')

    def upsert(self):
        try:
            domain_name = self.get_domain_name()

            verification_token = self.ses.verify_domain_identity(Domain=domain_name)['VerificationToken']

            dkim_tokens = None
            if (self.get('DKIM')):
                dkim_tokens = self.ses.verify_domain_dkim(Domain=domain_name)['DkimTokens']

            if self.is_hosted_zone():
                self.upsert_dns_records(self.get('HostedZoneId'), verification_token, dkim_tokens)

            self.physical_resource_id = domain_name
        except ClientError as e:
            self.physical_resource_id = 'could-not-create'
            self.fail(e.message)

    def upsert_dns_records(self, hosted_zone_id, verification_token, dkim_tokens=None):
        hosted_zone_name = self.get_hosted_zone_name(hosted_zone_id)

        batch = {'Changes': []}

        batch['Changes'] = [
            {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': '_amazonses.%s' % hosted_zone_name,
                    'Type': 'TXT',
                    'TTL': 60,
                    'ResourceRecords': [
                        {
                            'Value': '"%s"' % verification_token
                        }
                    ]
                }
            }
        ]

        if dkim_tokens is not None:
            for dkim_token in dkim_tokens:
                change = {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': '%s._domainkey.%s' % (dkim_token, hosted_zone_name),
                        'Type': 'CNAME',
                        'TTL': 60,
                        'ResourceRecords': [
                            {
                                'Value': '%s.dkim.amazonses.com' % dkim_token
                            }
                        ]
                    }
                }
                batch['Changes'].append(change)

        r = self.route53.change_resource_record_sets(HostedZoneId=hosted_zone_id, ChangeBatch=batch)
        self.set_attribute('ChangeId', r['ChangeInfo']['Id'])


provider = DomainProvider()


def handler(request, context):
    return provider.handle(request, context)
