# Custom::DomainIdentity
The `Custom::DomainIdentity` creates a verification token for the domain in SES.

## Syntax
To declare this entity in your AWS CloudFormation template, use the following syntax:

```yaml
{
  Type : "Custom::DomainIdentity"
  Properties:
    Domain: String
    Region: String,
    ServiceToken : !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider'
  }
}
It will request a Domain verification token from SES for the `Domain` in the `Region`. It will also return 
the DNS record name, type and value to provide ownership of the domain in DNS. 

```
## Properties
You can specify the following properties:

    "Domain" - identity to create 
    "Region" - to create the identity in
    "ServiceToken" - pointing to the domain identity provider

## Return values
'Ref' will return `Domain`@`Region`.

With 'Fn::GetAtt' the following values are available:

- `VerificationToken` - for the `Domain`
- `DNSRecordName` - of the validation token DNS entry
- `DNSRecordType` - of the DNS entry
- `DNSResourceRecords` - for the DNS entry

You can use these values to create the required DNS record to proof ownership of the domain tot AWS, as follows:

```yaml
  VerificationTokenRecord:
    Type: AWS::Route53::RecordSet
    Properties:
        HostedZoneId: !Ref 'HostedZone'
        Comment: !Sub 'SES identity validation for ${ExternalDomainName}'
        Name: !GetAtt 'DomainIdentity.DNSRecordName'
        Type: !GetAtt 'DomainIdentity.DNSRecordType'
        ResourceRecords: !GetAtt 'DomainIdentity.DNSResourceRecords'
        TTL: '60'

```
