# Custom::DkimTokens
The `Custom::DkimTokens` creates the DKIM tokens for a SES domain.

## Syntax
To declare this entity in your AWS CloudFormation template, use the following syntax:

```yaml
{
  Type : "Custom::DkimTokens"
  Properties:
    Domain: String
    Region: String,
    ServiceToken : !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider'
  }
}
It will request the DKIM tokens from SES for the `Domain` in the `Region`. It will also return 
the DNS record names, types and values to register the DKIM tokens.

```
## Properties
You can specify the following properties:

    "Domain" - to generate the tokens for.
    "Region" - to get the tokens from.
    "ServiceToken" - pointing to the DKIM token provider

## Return values
'Ref' will return `Domain`@`Region`.

With 'Fn::GetAtt' the following values are available:

- `DkimTokens` - array of DKIM tokens for the `Domain` in `Region`
- `DNSRecordNames` - array of DNS entry names for the DKIM tokens
- `DNSRecordTypes` - array of DNS entry types
- `DNSResourceRecords` - array of DNS entry values

The suspicion is that a DKIM token is generated per availability zone in the region. You can use these values to 
create the required DKIM DNS records, as follows:

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

