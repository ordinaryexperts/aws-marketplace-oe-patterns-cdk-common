from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.db_secret import DbSecret

def test_db_secret():
  stack = Stack()
  DbSecret(stack, "TestDbSecret")
  template = assertions.Template.from_stack(stack)

  template.resource_count_is("AWS::SSM::Parameter", 1)
