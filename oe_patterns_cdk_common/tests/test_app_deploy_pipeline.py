from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.app_deploy_pipeline import AppDeployPipeline

def test_app_deploy_pipeline():
  stack = Stack()
  AppDeployPipeline(stack, "TestAppDeployPipeline")
  template = assertions.Template.from_stack(stack)

  import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))
  # template.resource_count_is("AWS::S3::Bucket", 1)
