from aws_cdk import (
    aws_ec2,
    aws_elasticache,
    CfnParameter,
    CfnResource
)

from constructs import Construct
from oe_patterns_cdk_common.vpc import Vpc

class ElasticacheCluster(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str,
            vpc: Vpc,
            allowed_instance_types: 'list[str]' = [],
            default_instance_type: str = 'cache.t3.micro',
            **props):
        super().__init__(scope, id, **props)

        self.allowed_instance_types = allowed_instance_types
        self.default_instance_type = default_instance_type
        self.default_allowed_instance_types = [
            "cache.m5.large",
            "cache.m5.xlarge",
            "cache.m5.2xlarge",
            "cache.m5.4xlarge",
            "cache.m5.12xlarge",
            "cache.m5.24xlarge",
            "cache.m4.large",
            "cache.m4.xlarge",
            "cache.m4.2xlarge",
            "cache.m4.4xlarge",
            "cache.m4.10xlarge",
            "cache.t3.micro",
            "cache.t3.small",
            "cache.t3.medium"
        ]

        self.elasticache_cluster_cache_node_type_param = CfnParameter(
            self,
            "ElastiCacheClusterCacheNodeType",
            allowed_values=self.allowed_instance_types if self.allowed_instance_types else self.default_allowed_instance_types,
            default=self.default_instance_type,
            description="Required: Instance type for the cluster nodes."
        )
        self.elasticache_cluster_engine_version_param = CfnParameter(
            self,
            "ElastiCacheClusterEngineVersion",
            allowed_values=[ "1.4.14", "1.4.24", "1.4.33", "1.4.34", "1.4.5", "1.5.10", "1.5.16" ],
            default="1.5.16",
            description="Required: The version of the cache cluster."
        )
        self.elasticache_cluster_num_cache_nodes_param = CfnParameter(
            self,
            "ElastiCacheClusterNumCacheNodes",
            default=2,
            description="Required: The number of cache nodes in the memcached cluster (only applies ElastiCache enabled).",
            min_value=1,
            max_value=20,
            type="Number"
        )
        self.elasticache_sg = aws_ec2.CfnSecurityGroup(
            self,
            "ElastiCacheSg",
            group_description="ElastiCache SG",
            security_group_egress=[
                aws_ec2.CfnSecurityGroup.EgressProperty(
                    ip_protocol="-1",
                    cidr_ip="0.0.0.0/0",
                    description="all IPv4 egress traffic allowed"
                )
            ],
            vpc_id=vpc.id()
        )
        self.elasticache_subnet_group = CfnResource(
            self,
            "ElastiCacheSubnetGroup",
            type="AWS::ElastiCache::SubnetGroup",
            properties={
                "Description": "ElastiCache subnet group.",
                "SubnetIds":  vpc.private_subnet_ids()
            }
        )
        self.elasticache_cluster = aws_elasticache.CfnCacheCluster(
            self,
            "ElastiCacheCluster",
            az_mode="cross-az",
            cache_node_type=self.elasticache_cluster_cache_node_type_param.value_as_string,
            cache_subnet_group_name=self.elasticache_subnet_group.ref,
            engine=self.engine,
            engine_version=self.elasticache_cluster_engine_version_param.value_as_string,
            num_cache_nodes=self.elasticache_cluster_num_cache_nodes_param.value_as_number,
            vpc_security_group_ids=[ self.elasticache_sg.ref ]
        )


class ElasticacheRedis(ElasticacheCluster):
    def __init__(
            self,
            scope: Construct,
            id: str,
            vpc: Vpc,
            allowed_instance_types: 'list[str]' = [],
            default_instance_type: str = 'cache.t3.micro',
            **props):

        self.engine = "redis"

        super().__init__(
            scope,
            id,
            vpc=vpc,
            allowed_instance_types=allowed_instance_types,
            default_instance_type=default_instance_type,
            **props)
