from aws_cdk import (
        core,
        assertions
    )

from oe_patterns_cdk_common import Vpc

def test_vpc():
  app = core.App()
  stack = Vpc(app, "test")
  template = assertions.Template.from_stack(stack)

  template.has_resource_properties("AWS::SQS::Queue", {
    "VisibilityTimeout": 300
  })
