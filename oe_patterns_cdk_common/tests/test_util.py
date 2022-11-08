from aws_cdk import (
  assertions,
  aws_ec2,
  Stack,
  Token
)

from oe_patterns_cdk_common.open_search_service import OpenSearchService
from oe_patterns_cdk_common.util import Util
from oe_patterns_cdk_common.vpc import Vpc

def test_util_append_stack_uuid():
  Util.append_stack_uuid("test")

def test_util_add_sg_ingress():
  stack = Stack()
  vpc = Vpc(stack, "test")
  sg = aws_ec2.CfnSecurityGroup(stack, "sg", group_description="test")
  opensearch = OpenSearchService(stack, "TestOpenSearch", vpc=vpc)
  Util.add_sg_ingress(opensearch, sg)
