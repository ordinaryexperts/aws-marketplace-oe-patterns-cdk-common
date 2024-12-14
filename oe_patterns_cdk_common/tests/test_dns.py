from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.dns import Dns
from oe_patterns_cdk_common.alb import Alb
from oe_patterns_cdk_common.asg import Asg

def test_dns():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  asg = Asg(stack, "TestAsg", vpc=vpc)
  alb = Alb(stack, "TestAlb", asg=asg, vpc=vpc)
  dns = Dns(stack, "TestDns")
  dns.add_alb(alb)
  template = assertions.Template.from_stack(stack)
  # import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))

  template.resource_count_is("AWS::Route53::RecordSetGroup", 1)

def test_dns_add_wildcard():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  asg = Asg(stack, "TestAsg", vpc=vpc)
  alb = Alb(stack, "TestAlb", asg=asg, vpc=vpc)
  dns = Dns(stack, "TestDns")
  dns.add_alb(alb, add_wildcard=True)
  template = assertions.Template.from_stack(stack)
  # import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))

  template.resource_count_is("AWS::Route53::RecordSetGroup", 2)
