from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.db_secret import DbSecret
from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.amazonmq import RabbitMQ

def test_rabbitmq():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  db_secret = DbSecret(stack, "TestDbSecret")
  RabbitMQ(stack, "TestRabbitMQ", db_secret=db_secret, vpc=vpc)
  template = assertions.Template.from_stack(stack)
  # import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))

  template.resource_count_is("AWS::AmazonMQ::Broker", 1)
