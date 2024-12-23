from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.notification_topic import NotificationTopic

def test_notification_topic():
  stack = Stack()
  NotificationTopic(stack, "TestNotificationTopic")
  template = assertions.Template.from_stack(stack)

  # import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))
  template.resource_count_is("AWS::SNS::Topic", 1)
