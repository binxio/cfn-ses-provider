# cfn-ses-provider
A  CloudFormation custom provider for managing SES Domain Identities and DKIM tokens.

## How do I add SES Domain Identity in CloudFormation?
It is quite easy: you specify a CloudFormation resource of type [Custom::DomainIdentity](docs/DomainIdentity.md):

```yaml
Resources:
  DomainIdentity:
    Type: Custom::DomainIdentity
    Properties:
      Domain: !Ref 'ExternalDomainName'
      Region: !Ref 'EmailRegion'
      ServiceToken: !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider'
```
This will create a domain identity in the region, and return the DNS entry as attributes, so you can proof you
own the domain by adding a Route53 record:

```yaml
  DomainVerificationRecord:
    Type: AWS::Route53::RecordSet
    Properties:
        HostedZoneId: !Ref 'HostedZone'
        Comment: !Sub 'SES identity for ${ExternalDomainName}'
        Name: !GetAtt 'DomainIdentity.DNSRecordName'
        Type: !GetAtt 'DomainIdentity.DNSRecordType'
        ResourceRecords: !GetAtt 'DomainIdentity.DNSResourceRecords'
        TTL: '60'
```

## How do I get DKIM tokens in CloudFormation?
It is quite easy: you specify a CloudFormation resource of type [Custom::DkimTokens](docs/DkimTokens.md):

```yaml
Resources:
  DkimTokens:
    Type: Custom::DkimTokens
    Properties:
      Domain: !Ref 'ExternalDomainName'
      Region: !Ref 'EmailRegion'
      ServiceToken: !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider'
```
This will return the DKIM tokens and the DNS entries as attributes, so that
receiver can validate that the messages were sent by the owner of the domain.
You can use these values to create the required DKIM DNS records, as follows:

```yaml
  DkimRecords:
    Type: AWS::Route53::RecordSetGroup
    Properties:
      HostedZoneId: !Ref 'HostedZone'
      RecordSets:
        - Name: !Select [0, !GetAtt 'DkimTokens.DNSRecordNames' ]
          ResourceRecords: !Select [0, !GetAtt 'DkimTokens.DNSResourceRecords' ]
          Type: 'CNAME'
          TTL: '60'
        - Name: !Select [1, !GetAtt 'DkimTokens.DNSRecordNames' ]
          ResourceRecords: !Select [1, !GetAtt 'DkimTokens.DNSResourceRecords' ]
          Type: 'CNAME'
          TTL: '60'
        - Name: !Select [2, !GetAtt 'DkimTokens.DNSRecordNames' ]
          ResourceRecords: !Select [2, !GetAtt 'DkimTokens.DNSResourceRecords' ]
          Type: 'CNAME'
          TTL: '60'
```
## Installation
To install these custom resources, type:
```sh
aws cloudformation deploy \
	--capabilities CAPABILITY_IAM \
	--stack-name cfn-ses-provider \
	--template-file ./cloudformation/cfn-resource-provider.yaml 
```
This CloudFormation template will use our pre-packaged provider from `s3://binxio-public-{{your-region}}/lambdas/cfn-ses-provider-0.5.0.zip`.

## Demo
To install the demo of this Custom Resource, type:

```sh
aws cloudformation deploy --stack-name cfn-ses-provider-demo \
	--template-file ./cloudformation/demo-stack.yaml
```
view the installed identity:
```
aws --region eu-west-1 ses list-identities
```
