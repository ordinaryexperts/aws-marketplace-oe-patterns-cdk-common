from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.elasticache_cluster import ElasticacheRedis

def test_aurora_postgresql():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  ElasticacheRedis(stack, "TestRedis", vpc=vpc)
  template = assertions.Template.from_stack(stack)
  # print(json.dumps(template.to_json(), indent=4, sort_keys=True))

  template.resource_count_is("AWS::ElastiCache::CacheCluster", 1)
