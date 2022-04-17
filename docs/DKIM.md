# Custom::DKIM
*This custom resource is deprecated. It violates the principle of a CloudFormation resource provider
by managing multiple physical resources.*

Please use [Custom::DomainIdentity](DomainIdentity.md) and [Custom::DkimTokens](DkimTokens.md) instead.

The `Custom::DKIM` creates a SES domain identity, a SES domain verification DNS record and the associated DKIM DNS records.

## Syntax
To declare this entity in your AWS CloudFormation template, use the following syntax:

```json
{
  "Type" : "Custom::DKIM",
  "Properties" : {
    "Domain": String
    "HostedZoneId": String,
    "Region": String,
    "ServiceToken" : String
  }
}

It will create a `_amazonses` TXT record and a number of `_domainkey` records in the
hosted zone for the `Domain` in hosted zone `HostedZoneId`. If Domain is not specified,
the domain name of the hosted zone is used.

```
## Properties
You can specify the following properties:

    "Domain" - to create the DKIM verification records for (not required).
    "HostedZoneId" - in which to create the DKIM verification records  (required).
    "Region" - from which to send emails (default: "eu-west-1")
    "ServiceToken" - pointing to the function implementing this (required)

## Return values
'Ref' will return `Domain`@`HostedZoneId` if a Domain is specified, otherwise `HostedZoneId`.

With 'Fn::GetAtt' the following values are available:

- `ChangeId` - The Route53 ChangeId

For more information about using Fn::GetAtt, see [Fn::GetAtt](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-getatt.html).
