# Custom::Domain
The `Custom::Domain` adds the domain to Simple Email Service.
When DKIM is enabled is creates DomainKeys Identified Email (DKIM) verification records.

## Syntax
To declare this entity in your AWS CloudFormation template, use the following syntax:

```json
{
  "Type" : "Custom::Domain",
  "Properties" : {
    "HostedZoneId": String,
    "DKIM": Boolean,
    "ServiceToken": String
  }
}
```
It will create a `_amazonses` TXT record and a number of `_domainkey` records in the
hosted zone pointed to by `HostedZoneId`.

Or, when the domain is not hosted at Route53, use the following syntax:
```json
{
  "Type" : "Custom::Domain",
  "Properties" : {
    "DomainName": String,
    "DKIM": Boolean,
    "ServiceToken": String
  }
}
```

## Properties
You can specify the following properties:

    "HostedZoneId" - the Route53 hosted zone (required).
    "DomainName" - the non-Route53 hosted domain name (required).
    "DKIM" - enable DKIM verification records.
    "ServiceToken" - pointing to the function implementing this (required).

## Return values
With 'Fn::GetAtt' the following values are available:

- `ChangeId` - The Route53 ChangeId

For more information about using Fn::GetAtt, see [Fn::GetAtt](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-getatt.html).
