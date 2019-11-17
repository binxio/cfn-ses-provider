# Custom::SESActiveReceiptRuleSet
The `Custom::SESActiveReceiptRuleSet` manages the active receipt rule set.

## Syntax
To declare this entity in your AWS CloudFormation template, use the following syntax:

```yaml
  Type : "Custom::SESActiveReceiptRuleSet"
  Properties:
    RuleSetName: String
    Region: String
    ServiceToken : !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider'
```
It will activate the specified receipt rule set. If one is already set, an error is reported.

## Properties
You can specify the following properties:

    "RuleSetName" - to activate
    "Region" - to activate the receipt rule set in
    "ServiceToken" - pointing to the custom SES provider

## Return values
'Ref' will return `activate-receipt-rule-set@Region`.
