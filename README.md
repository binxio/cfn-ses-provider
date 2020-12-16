# cfn-ses-provider
A  CloudFormation custom provider for managing SES Domain Identities, Identity Notifications, DKIM tokens and the active receipt rule set.

Read the blog on [How to configure SES domain identities and DKIM records using cloudformation](https://binx.io/blog/2019/11/14/how-to-deploy-aws-ses-domain-identities-dkim-records-using-cloudformation/)

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
This will create a domain identity in the region, and return the DNS entry as attributes, so you can proof you own the domain by adding a Route53 record:

```yaml
  DomainVerificationRecord:
    Type: AWS::Route53::RecordSetGroup
    Properties:
        Comment: !Sub 'SES identity for ${ExternalDomainName}'
        HostedZoneId: !Ref 'HostedZone'
        RecordSets: !GetAtt 'DomainIdentity.RecordSets'
	RecordSetDefaults:
	  TTL: 60
	  Weight: 1
	  SetIdentifier: !Ref 'AWS::Region'
```

To wait until the domain identity is verified, add a [Custom::VerifiedIdentity](docs/VerifiedIdentity.md):
```yaml
  VerifiedDomainIdentity:
    Type: Custom::VerifiedIdentity
    Properties:
      Identity: !GetAtt 'DomainIdentity.Domain'
      Region: !GetAtt 'DomainIdentity.Region'
      ServiceToken: !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider'
```

If you wish to add a MAIL FROM domain, add a [Custom::MailFromDomain](docs/MailFromDomain.md):
```yaml
Resources:
  MailFromDomain:
    Type: Custom::MailFromDomain
    Properties:
      Domain: !Ref 'ExternalDomainName'
      Region: !Ref 'EmailRegion'
      MailFromSubdomain: 'mail'
      ServiceToken: !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider'
```

You can verify the MAIL FROM domain in Route53 like this:
```yaml
  MailFromDomainVerificationRecords:
    Type: AWS::Route53::RecordSetGroup
    Properties:
        Comment: !Sub 'SES MAIL FROM domain for ${ExternalDomainName}'
        HostedZoneId: !Ref 'HostedZone'
        RecordSets: !GetAtt 'MailFromDomain.RecordSets'
	RecordSetDefaults:
	  TTL: 60
	  Weight: 1
	  SetIdentifier: !Ref 'AWS::Region'
```

To wait until the MAIL FROM domain is verified, add a [Custom::VerifiedMailFromDomain](docs/VerifiedMailFromDomain.md):
```yaml
  VerifiedMailFromDomain:
    Type: Custom::VerifiedMailFromDomain
    Properties:
      Identity: !GetAtt 'DomainIdentity.Domain'
      Region: !GetAtt 'DomainIdentity.Region'
      ServiceToken: !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider'
```

If you wish to configure the notifications, add a [Custom::IdentityNotifications](docs/IdentityNotifications.md):
```yaml
  DomainNotifications:
    Type: Custom::IdentityNotifications
    Properties:
      Identity: !GetAtt 'DomainIdentity.Domain'
      Region: !GetAtt 'DomainIdentity.Region'
      BounceTopic: !Ref BounceTopic
      ComplaintTopic: !Ref ComplaintTopic
      HeadersInBounceNotificationsEnabled: true
      HeadersInComplaintNotificationsEnabled: true
      ForwardingEnabled: false
      ServiceToken: !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider'
```

If you wish to activate a SES Receipt Rule set, add a [Custom::ActiveReceiptRuleSet](docs/ActiveReceiptRuleSet.md):

```yaml
  Type: Custom::ActiveReceiptRuleSet
  Properties:
    Region: !Ref 'AWS::Region'
    RuleSetName: !Ref ReceiptRuleSet
    ServiceToken: !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider'
```

If you wish to authorize other AWS accounts, IAM users, and AWS services to send for this identity, add an identity policy:
```yaml
  IdentityPolicy:
    Type: Custom::IdentityPolicy
    Properties:
      Identity: !GetAtt 'DomainIdentity.Domain'
      PolicyName: CrossAccountAllow
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              AWS:
                - 'arn:aws:iam::000111222333:root'
            Action:
              - ses:SendEmail
              - ses:SendRawEmail
            Resource: !Sub 'arn:aws:ses:${AWS::Region}:${AWS::AccountId}:identity/${DomainIdentity.Domain}'
      ServiceToken: !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider'
```

## How do I get DKIM tokens in CloudFormation?
It is quite easy: you specify a CloudFormation resource of type [Custom::DkimTokens](docs/DkimTokens.md):

```yaml
Resources:
  DkimTokens:
    Type: Custom::DkimTokens
    Properties:
      Domain: !GetAtt 'DomainIdentity.Domain'
      Region: !GetAtt 'DomainIdentity.Region'
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
      RecordSets: !GetAtt 'DkimTokens.RecordSets'
```
## Installation
To install these custom resources, type:
```sh
aws cloudformation deploy \
	--capabilities CAPABILITY_IAM \
	--stack-name cfn-ses-provider \
	--template-file ./cloudformation/cfn-resource-provider.yaml
```
This CloudFormation template will use our pre-packaged provider from `s3://binxio-public-{{your-region}}/lambdas/cfn-ses-provider-0.7.0.zip`.

## Demo
To install the demo you need a domain name and a Route53 hosted zone for the domain.
To install the demo of this Custom Resource, type:

```sh
read -p "domain name: " DOMAIN_NAME
read -p "hosted zone id: " HOSTED_ZONE
aws --region eu-west-1 \
	cloudformation deploy --stack-name cfn-certificate-provider-demo \
	--template-file cloudformation/demo-stack.yaml \
	--parameter-overrides DomainName=$DOMAIN_NAME HostedZoneId=$HOSTED_ZONE
```
view the installed identity, the notification attributes and route53 records:
```sh
aws --region eu-west-1 ses list-identities
aws --region eu-west-1 ses get-identity-notification-attributes
aws route53 get-resource-record-sets --hosted-zone $HOSTED_ZONE
```
