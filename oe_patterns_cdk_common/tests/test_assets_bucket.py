from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.assets_bucket import AssetsBucket

def test_assets_bucket():
  stack = Stack()
  AssetsBucket(stack, "TestAssetsBucket")
  template = assertions.Template.from_stack(stack)

  # import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))
  template.resource_count_is("AWS::S3::Bucket", 1)