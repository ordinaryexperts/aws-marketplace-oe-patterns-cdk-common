import json

from aws_cdk import (
  assertions,
  aws_ec2,
  Stack
)

from oe_patterns_cdk_common.ses import Ses

def test_ses():
  stack = Stack()
  ses = Ses(stack, "TestSes", hosted_zone_name="test.patterns.ordinaryexperts.com")
  template = assertions.Template.from_stack(stack)
  # print(json.dumps(template.to_json(), indent=4, sort_keys=True))

  template.resource_count_is("AWS::SES::EmailIdentity", 1)
