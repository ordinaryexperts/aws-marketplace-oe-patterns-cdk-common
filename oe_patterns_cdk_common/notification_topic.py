from aws_cdk import (
    Aws,
    aws_iam,
    aws_sns,
    CfnCondition,
    CfnOutput,
    CfnParameter,
    Fn,
    Token
)

from constructs import Construct
from oe_patterns_cdk_common.util import Util

class NotificationTopic(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str,
            **props):
        super().__init__(scope, id, **props)

        #
        # PARAMETERS
        #

        self.notification_topic_email_param = CfnParameter(
            self,
            "NotificationTopicEmail",
            default="",
            description="Optional: Specify an email address to get emails about stack events. This email is only used within this stack to subscribe to an SNS topic and is not sent to any third party."
        )
        self.notification_topic_email_param.override_logical_id(f"{id}Email")

        self.notification_topic_arn_param = CfnParameter(
            self,
            "NotificationTopicArn",
            default="",
            description="Optional: Specify an ARN of an existing SNS topic to use for stack notifications. If you do not specify one, a topic will be created."
        )
        self.notification_topic_arn_param.override_logical_id(f"{id}Arn")

        #
        # CONDITIONS
        #

        self.notification_topic_email_exists_condition = CfnCondition(
            self,
            "NotificationTopicEmailExists",
            expression=Fn.condition_not(Fn.condition_equals(self.notification_topic_email_param.value, ""))
        )
        self.notification_topic_email_exists_condition.override_logical_id(f"{id}EmailExists")

        self.notification_topic_arn_not_given_condition = CfnCondition(
            self,
            "NotificationTopicArnNotGiven",
            expression=Fn.condition_equals(self.notification_topic_arn_param.value, "")
        )
        self.notification_topic_arn_not_given_condition.override_logical_id(f"{id}ArnExists")

        #
        # RESOURCES
        #

        self.notification_topic = aws_sns.CfnTopic(
            self,
            "NotificationTopic",
            topic_name=Util.append_stack_uuid(f"{Aws.STACK_NAME}-notifications")
        )
        self.notification_topic.override_logical_id(id)
        self.notification_topic.cfn_options.condition = self.notification_topic_arn_not_given_condition

        self.notification_topic_subscription = aws_sns.CfnSubscription(
            self,
            "NotificationTopicSubscription",
            protocol="email",
            topic_arn=self.notification_topic_arn(),
            endpoint=self.notification_topic_email_param.value_as_string
        )
        self.notification_topic_subscription.override_logical_id(f"{id}Subscription")
        self.notification_topic_subscription.cfn_options.condition = self.notification_topic_email_exists_condition

        self.notification_topic_policy_document = aws_iam.PolicyDocument(
            statements=[
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[ "sns:Publish" ],
                    resources=[ self.notification_topic_arn() ]
                )
            ]
        )

        #
        # OUTPUTS
        #

        self.notification_topic_arn_output = CfnOutput(
            self,
            "NotificationTopicArnOutput",
            description="The notification topic ARN",
            value=self.notification_topic_arn()
        )
        self.notification_topic_arn_output.override_logical_id(f"{id}ArnOutput")


    def notification_topic_arn(self):
        return Token.as_string(
            Fn.condition_if(
                self.notification_topic_arn_not_given_condition.logical_id,
                self.notification_topic.ref,
                self.notification_topic_arn_param.value_as_string
            )
        )

        
