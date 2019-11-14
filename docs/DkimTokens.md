# Custom::DkimTokens
The `Custom::DkimTokens` creates the DKIM tokens for a SES domain.

## Syntax
To declare this entity in your AWS CloudFormation template, use the following syntax:

```yaml
  Type : "Custom::DkimTokens"
  Properties:
    Domain: String
    Region: String
    RecordSetDefaults:
      TTL: 60
    ServiceToken : !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider'
```
It will request the DKIM tokens from SES for the `Domain` in the `Region`. It will return DNS
record sets required to register the DKIM tokens.

 
## Properties
You can specify the following properties:

    "Domain" - identity to create 
    "Region" - to create the identity in
    "RecordSetDefaults" - any default values for the resulting RecordSet
    "ServiceToken" - pointing to the domain identity provider

## Return values
'Ref' will return `Domain`@`Region`.

With 'Fn::GetAtt' the following values are available:

- `DkimTokens` - array of DKIM tokens for the `Domain` in `Region`
- `RecordSets` - array of Route53 DKIM RecordSets

You can create the required DKIM DNS records, as follows:

```yaml
  DkimRecords:
    Type: AWS::Route53::RecordSetGroup
    Properties:
      HostedZoneId: !Ref 'HostedZone'
      RecordSets: !Ref 'DkimTokens.RecordSets'
```

