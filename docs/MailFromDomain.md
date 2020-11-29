# Custom::MailFromDomain
The `Custom::MailFromDomain` sets a MAIL FROM value for the domain in SES.

## Syntax
To declare this entity in your AWS CloudFormation template, use the following syntax:

```yaml
  Type : "Custom::MailFromDomain"
  Properties:
    Domain: String
    Region: String
    MailFromSubdomain: String
    BehaviorOnMXFailure: String
    RecordSetDefaults:
      TTL: 60
    ServiceToken : !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider'
```
It will set the MAIL FROM value in SES for the `Domain` in `Region` to be `{MailFromSubdomain}.{Domain}`. It will also return 
the DNS MX and TXT records to demonstrate ownership of the domain in DNS. 


## Properties
You can specify the following properties:

    "Domain" - identity to create 
    "Region" - to create the identity in
    "MailFromSubdomain" - the subdomain to use as the MAIL FROM domain, will be prepended to domain
    "BehaviorOnMXFailure" - action that Amazon SES takes if it cannot successfully read the required MX record when you send an email (UseDefaultValue | RejectMessage, defaults to UseDefaultValue)
    "RecordSetDefaults" - for the resulting DNS records, defaults to {"TTL": 60}
    "ServiceToken" - pointing to the domain identity provider

## Return values
'Ref' will return `Domain`@`Region`.

With 'Fn::GetAtt' the following values are available:

- `RecordSets` - Route53 recordset to validate the mail from domain
- `Domain` - the name of the domain identity.
- `Region` - the region of the domain identity.

You can demonstrate ownership of the domain to AWS, as follows:

```yaml
  VerificationMailFromRecord:
    Type: AWS::Route53::RecordSetGroup
    Properties:
        Comment: !Sub 'SES identity validation for ${ExternalDomainName}'
        HostedZoneId: !Ref 'HostedZone'
        RecordSets: !GetAtt 'MailFromDomain.RecordSets'
```
