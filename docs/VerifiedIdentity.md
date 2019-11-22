# Custom::VerifiedIdentity
The `Custom::VerifiedIdentity` waits until a SES identity reaches the state 'Verified'.

## Syntax
To declare this entity in your AWS CloudFormation template, use the following syntax:

```yaml
  Type : "Custom::VerifiedIdentity"
  Properties:
    Identity: String
    Region: String
    ServiceToken : !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider'
```
It will return the identity, once it reaches the state `Verified`

## Properties
You can specify the following properties:

    "Identity" - to await verification
    "Region" - the identity is created in
    "ServiceToken" - pointing to the SES identity provider

## Return values
'Ref' will return `Identity`.

With 'Fn::GetAtt' the following values are available:

- `VerificationToken` - for the `Identity`
- `VerificationStatus` - for the `Identity`
- `Identity` - for the `Identity`
- `Region` - of the `Identity`
