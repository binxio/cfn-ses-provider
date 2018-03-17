# cfn-ses-provider
A  CloudFormation custom provider for managing Simple Email Services DKIM records in route53

## How do I add DKIM records to my Route53 domain?
It is quite easy: you specify a CloudFormation resource of type [Custom::DKIM](docs/DKIM.md):

```yaml
Resources:
  DKIM:
    Type: Custom::DKIM
    DependsOn: HostedZone
    Properties:
      HostedZoneId: !Ref 'HostedZone'
      Region: !Ref 'EmailRegion'
      ServiceToken: !Sub  'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider
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

This CloudFormation template will use our pre-packaged provider from `s3://binxio-public-{{your-region}}/lambdas/cfn-ses-provider-0.2.1.zip`.


## Demo
To install the demo of this Custom Resource, type:

```sh
aws cloudformation create-stack --stack-name cfn-ses-provider-demo \
	--template-body file://cloudformation/demo-stack.json

aws cloudformation wait stack-create-complete  --stack-name cfn-ses-provider-demo
```
view the installed identity:

```
aws --region eu-west-1 ses list-identities
```
