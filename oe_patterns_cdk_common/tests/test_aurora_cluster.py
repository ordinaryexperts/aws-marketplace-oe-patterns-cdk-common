from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.asg import Asg
from oe_patterns_cdk_common.db_secret import DbSecret
from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.aurora_cluster import AuroraPostgresql

def test_aurora_postgresql():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  asg = Asg(stack, "TestAsg", vpc=vpc)
  db_secret = DbSecret(stack, "TestDbSecret")
  aurora = AuroraPostgresql(stack, "TestAurora", db_secret=db_secret, vpc=vpc)
  aurora.add_asg_ingress(asg)
  template = assertions.Template.from_stack(stack)
  # print(json.dumps(template.to_json(), indent=4, sort_keys=True))

  template.resource_count_is("AWS::RDS::DBCluster", 1)
