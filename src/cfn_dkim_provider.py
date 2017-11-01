import boto3
from botocore.exceptions import ClientError
from cfn_resource_provider import ResourceProvider


request_schema = {
    "type": "object",
    "required": ["HostedZoneId"],
    "properties": {
        "HostedZoneId":  {
            "type": "string",  "description": "to create Domain Keys for"
        },
        "Region":  {
            "type": "string",
            "description": "of the SES endpoint to use",
            "default": "eu-west-1"
        }
    }
}


class DKIMProvider(ResourceProvider):

    def __init__(self):
        self.request_schema = request_schema
        self.route53 = boto3.client('route53')

    def create(self):
        self.upsert()

    def update(self):
        self.upsert()

    def delete(self):
        hosted_zone_id = self.physical_resource_id
        if hosted_zone_id == 'could-not-create':
            return

        paginator = self.route53.get_paginator('list_resource_record_sets')

        hosted_zone = self.get_hosted_zone_name(hosted_zone_id)

        to_delete = []
        suffix = '_domainkey.%s' % hosted_zone
        page_iterator = paginator.paginate(HostedZoneId=hosted_zone_id, StartRecordName=suffix)
        for page in page_iterator:
            records = filter(lambda rr: rr['Type'] == 'CNAME' and rr['Name'].endswith('.%s' % suffix), page['ResourceRecordSets'])
            to_delete.extend(records)

        amazonses = '_amazonses.%s' % hosted_zone
        page_iterator = paginator.paginate(HostedZoneId=hosted_zone_id, StartRecordName=amazonses)
        for page in page_iterator:
            records = filter(lambda rr: rr['Type'] == 'TXT' and rr['Name'] == amazonses, page['ResourceRecordSets'])
            to_delete.extend(records)

        if len(to_delete) > 0:
            batch = {'Changes': [{'Action': 'DELETE', 'ResourceRecordSet': rr} for rr in to_delete]}
            r = self.route53.change_resource_record_sets(HostedZoneId=hosted_zone_id, ChangeBatch=batch)
            self.set_attribute('ChangeId', r['ChangeInfo']['Id'])

    def get_hosted_zone_name(self, hosted_zone_id):
        response = self.route53.get_hosted_zone(Id=hosted_zone_id)
        return response['HostedZone']['Name']

    def upsert(self):
        hosted_zone_id = self.get('HostedZoneId')
        batch = {'Changes': []}
        try:
            ses = boto3.client('ses', region_name=self.get('Region'))
            hosted_zone = self.get_hosted_zone_name(hosted_zone_id=hosted_zone_id)
            domain = hosted_zone.rstrip('.')
            verification_token = ses.verify_domain_identity(Domain=domain)['VerificationToken']
            dkim_tokens = ses.verify_domain_dkim(Domain=domain)['DkimTokens']
            batch['Changes'] = [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': '_amazonses.%s' % domain,
                        'Type': 'TXT',
                        'TTL': 60,
                        'ResourceRecords': [
                            {
                                'Value': '%s' % verification_token
                            }
                        ]
                    }
                }
            ]
            for dkim_token in dkim_tokens:
                change = {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': '%s._domainkey.%s.' % (dkim_token, domain),
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
            self.physical_resource_id = hosted_zone_id
        except ClientError as e:
            self.physical_resource_id = 'could-not-create'
            self.fail(e.message)

provider = DKIMProvider()


def handler(request, context):
    return provider.handle(request, context)
