from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.db_secret import DbSecret

def test_db_secret():
  stack = Stack()
  DbSecret(stack, "TestDbSecret")
  template = assertions.Template.from_stack(stack)
  import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))

  template.resource_count_is("AWS::SSM::Parameter", 1)

def test_db_secret_custom_username():
  stack = Stack()
  DbSecret(stack, "TestDbSecret", username="customuser")
  template = assertions.Template.from_stack(stack)
  # import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))

  template.resource_count_is("AWS::SSM::Parameter", 1)
