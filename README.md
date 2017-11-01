# cfn-ses-provider
A collection of CloudFormation custom providers for managing Simple Email Services

## How do I add a DKIM records to my Route53 domain?
It is quite easy: you specify a CloudFormation resource of type [Custom::DKIM](docs/KongAPI.md):

```json
  "DKIM": {
    "Type": "Custom::DKIM",
    "Properties": {
      "HostedZoneId": { "Ref": "HostedZone" },
      "Region": "eu-west-1"
      "ServiceToken": { "Fn::Join": [ ":", [ "arn:aws:lambda", { "Ref": "AWS::Region" }, { "Ref": "AWS::AccountId" }, "function:binxio-cfn-kong-provider" ]]}
    }
  }
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

This CloudFormation template will use our pre-packaged provider from `s3://binxio-public/lambdas/cfn-kong-provider-latest.zip`.


## Demo
To install the demo of this Custom Resource, type:

```sh
aws cloudformation create-stack --stack-name cfn-ses-provider-demo \
	--template-body file://cloudformation/demo-stack.json

aws cloudformation wait stack-create-complete  --stack-name cfn-ses-provider-demo
```
