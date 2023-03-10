from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.secret import Secret
from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.amazonmq import RabbitMQ

def test_rabbitmq():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  secret = Secret(stack, "RabbitMQ")
  RabbitMQ(stack, "TestRabbitMQ", secret=secret, vpc=vpc)
  template = assertions.Template.from_stack(stack)
  # import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))

  template.resource_count_is("AWS::AmazonMQ::Broker", 1)
