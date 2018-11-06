# cfn-ses-provider
A  CloudFormation custom provider for managing Simple Email Service and associated DKIM records in route53.

## How do I add a domain to Simple Email Service?
It is quite easy: you specify a CloudFormation resource of type [Custom::Domain](docs/Domain.md):

```yaml
Resources:
  DKIM:
    Type: Custom::Domain
    DependsOn: HostedZone
    Properties:
      HostedZoneId: !Ref 'HostedZone'
      DKIM: true
      ServiceToken: !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider
```

Or, when the domain is not hosted at Route53:
```yaml
Resources:
  DKIM:
    Type: Custom::Domain
    Properties:
      DomainName: example.com
      DKIM: true
      ServiceToken: !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider
```

## Installation
To install these custom resources, type:

```sh
aws cloudformation create-stack \
	--capabilities CAPABILITY_IAM \
	--stack-name cfn-ses-provider \
	--template-body file://cloudformation/cfn-resource-provider.json

aws cloudformation wait stack-create-complete  --stack-name cfn-ses-provider
```

This CloudFormation template will use our pre-packaged provider from `s3://binxio-public-{{your-region}}/lambdas/cfn-ses-provider-0.2.4.zip`.


## Demo
To install the demo of this Custom Resource, type:

```sh
aws cloudformation create-stack --stack-name cfn-ses-provider-demo \
	--template-body file://cloudformation/demo-stack.json

aws cloudformation wait stack-create-complete  --stack-name cfn-ses-provider-demo
```
view the installed identity:

```sh
aws --region eu-west-1 ses list-identities
```
