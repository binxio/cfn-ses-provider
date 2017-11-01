import boto3
import sys
import uuid
import time
import StringIO
import subprocess
from ses import handler


route53 = boto3.client('route53')


def wait_for_change_completion(change_id):
    while not (route53.get_change(Id=change_id)['ChangeInfo']['Status'] == 'INSYNC'):
        time.sleep(3)


def test_create():

    name = '%s.internal' % str(uuid.uuid4())
    hosted_zone_id = None
    try:
        response = route53.create_hosted_zone(Name=name, CallerReference=name)
        hosted_zone_id = response['HostedZone']['Id']
        wait_for_change_completion(response['ChangeInfo']['Id'])

        request = Request('Create', hosted_zone_id)
        response = handler(request, {})
        assert response['Status'] == 'SUCCESS', response['Reason']
        physical_resource_id = response['PhysicalResourceId']
        wait_for_change_completion(response['Data']['ChangeId'])

        request = Request('Update', hosted_zone_id, physical_resource_id)
        response = handler(request, {})
        assert response['Status'] == 'SUCCESS', response['Reason']
        assert physical_resource_id == response['PhysicalResourceId']
        wait_for_change_completion(response['Data']['ChangeId'])

        request = Request('Delete', hosted_zone_id, physical_resource_id)
        response = handler(request, {})
        assert response['Status'] == 'SUCCESS', response['Reason']
        assert physical_resource_id == response['PhysicalResourceId']
        wait_for_change_completion(response['Data']['ChangeId'])

    finally:
        if hosted_zone_id is not None:
            try:
                route53.delete_hosted_zone(Id=hosted_zone_id)
            except Exception as e:
                print e


class Request(dict):

    def __init__(self, request_type, hosted_zone_id, physical_resource_id=None):
        request_id = 'request-%s' % uuid.uuid4()
        self.update({
            'RequestType': request_type,
            'ResponseURL': 'https://httpbin.org/put',
            'StackId': 'arn:aws:cloudformation:us-west-2:EXAMPLE/stack-name/guid',
            'RequestId': request_id,
            'ResourceType': 'Custom::DKIM',
            'LogicalResourceId': 'MyDKIM',
            'ResourceProperties': {
                'HostedZoneId': hosted_zone_id
            }})

        self['PhysicalResourceId'] = physical_resource_id if physical_resource_id is not None else 'initial-%s' % str(uuid.uuid4())
