from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.elasticache_cluster import ElasticacheRedis, ElasticacheMemcached

def test_elasticache_cluster():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  ElasticacheMemcached(stack, "TestMemcached", vpc=vpc)
  template = assertions.Template.from_stack(stack)
  # import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))

  template.resource_count_is("AWS::ElastiCache::CacheCluster", 1)

def test_elasticache_replication_group():
  stack = Stack()
  vpc = Vpc(stack, "TestVpc")
  ElasticacheRedis(stack, "TestRedis", vpc=vpc)
  template = assertions.Template.from_stack(stack)
  # import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))

  template.resource_count_is("AWS::ElastiCache::ReplicationGroup", 1)
