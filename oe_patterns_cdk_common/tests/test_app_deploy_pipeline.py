from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.asg import Asg
from oe_patterns_cdk_common.app_deploy_pipeline import AppDeployPipeline
# from . import print_resource

def test_app_deploy_pipeline():
  stack = Stack()
  vpc = Vpc(stack, 'TestVpc')
  asg = Asg(stack, 'TestAsg', vpc=vpc)
  AppDeployPipeline(stack, "TestAppDeployPipeline", asg=asg, demo_source_url="TESTURL", notification_topic_arn="TESTARN")
  template = assertions.Template.from_stack(stack)

  import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))
  # template.resource_count_is("AWS::S3::Bucket", 1)
