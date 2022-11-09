from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.open_search_service import OpenSearchService

def test_open_search_service():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  OpenSearchService(stack, "TestOpenSearchService", vpc=vpc)
  template = assertions.Template.from_stack(stack)
  # import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))

  template.resource_count_is("AWS::OpenSearchService::Domain", 1)
