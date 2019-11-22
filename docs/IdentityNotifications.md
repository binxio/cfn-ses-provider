# Custom:IdentityNotifications
The `Custom::IdentityNotifications` manages the notifications for a
SES identity. When the notifications are created, the resource expects that the notifications are not set.
When the resource is deleted, the topics are cleared and the booleans returned to their default values.

## Syntax
To declare this entity in your AWS CloudFormation template, use the following syntax:

```yaml
  Type : "Custom::IdentityNotifications"
  Properties:
    Identity: String,
    Region: String,
    BounceTopic: Arn,
    ComplaintTopic: Arn,
    DeliveryTopic: Arn,
    ForwardingEnabled: Boolean,
    HeadersInBounceNotificationsEnabled: Boolean,
    HeadersInComplaintNotificationsEnabled: Boolean,
    HeadersInDeliveryNotificationsEnabled: Boolean
    ForceOverride: Boolean
    ServiceToken : !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:binxio-cfn-ses-provider'
```
It will set the identity notification attributes appropriately.


## Properties
You can specify the following properties:

    "Identity" - to configure the notifications for, required
    "Region" -  of the identity, required
    "BounceTopic" - SNS topic ARN to send Bounce notifications to, optional
    "ComplaintTopic" - SNS topic ARN to send complaint notifications to, optional.
    "DeliveryTopic" - SNS topic ARN to send delivery notifications to, optional
    "ForwardingEnabled" - defaults true
    "HeadersInBounceNotificationsEnabled" - default False
    "HeadersInComplaintNotificationsEnabled" - default False
    "HeadersInDeliveryNotificationsEnabled" - default False
    "ForceOverride" - override existing notification settings, default False
    "ServiceToken" - pointing to the SES identity provider


## Return values
'Ref' will return the Arn of the SES identity.


## Caveats
- the Resource is presented as an atomic configuration, but in reality the configuration consists of 7 API calls. In 
  an error occurs, you may need to specify 'ForceOverride'
