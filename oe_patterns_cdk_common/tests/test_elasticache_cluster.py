from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.elasticache_cluster import ElasticacheRedis

def test_elasticache_cluster():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  ElasticacheRedis(stack, "TestRedis", vpc=vpc)
  template = assertions.Template.from_stack(stack)
  # import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))

  template.resource_count_is("AWS::ElastiCache::CacheCluster", 1)

def test_elasticache_cluster_custom_parameters():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  custom_params = {
    'test': 'value'
  }
  ElasticacheRedis(stack, "TestRedis", vpc=vpc, custom_parameters=custom_params)
  template = assertions.Template.from_stack(stack)
  # import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))

  group = template.find_resources("AWS::ElastiCache::ParameterGroup")
  assert group['TestRedisParameterGroup']['Properties']['Properties']['test'] == 'value'
