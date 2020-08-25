# Custom::DomainIdentity
The `Custom::DomainIdentity` creates a verification token for the domain in SES.

## Syntax
To declare this entity in your AWS CloudFormation template, use the following syntax:

```yaml
  Type : "Custom::DomainIdentity"
  Properties:
    Domain: String
    Region: String
    RecordSetDefaults:
      TTL: 60
    ServiceToken : !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider'
```
It will request a Domain verification token from SES for the `Domain` in the `Region`. It will also return 
the DNS record name, type and value to provide ownership of the domain in DNS. 


## Properties
You can specify the following properties:

    "Domain" - identity to create 
    "Region" - to create the identity in
    "RecordSetDefaults" - for the resulting DNS records, defaults to {"TTL": 60}
    "ServiceToken" - pointing to the domain identity provider

## Return values
'Ref' will return `Domain`@`Region`.

With 'Fn::GetAtt' the following values are available:

- `VerificationToken` - for the `Domain`
- `RecordSets` - Route53 recordset to validate the domain
- `Domain` - the name of the domain identity.
- `Region` - the region of the domain identity.

You can proof ownership of the domain to AWS, as follows:

```yaml
  VerificationTokenRecord:
    Type: AWS::Route53::RecordSetGroup
    Properties:
        Comment: !Sub 'SES identity validation for ${ExternalDomainName}'
        HostedZoneId: !Ref 'HostedZone'
        RecordSets: !GetAtt 'DomainIdentity.RecordSets'
```
