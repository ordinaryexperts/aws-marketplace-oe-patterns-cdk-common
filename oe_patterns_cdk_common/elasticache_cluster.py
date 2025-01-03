from aws_cdk import (
    Aws,
    aws_ec2,
    aws_elasticache,
    CfnParameter
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
            custom_parameters: dict = {},
            default_instance_type: str = 'cache.t4g.micro',
            **props):
        super().__init__(scope, id, **props)

        self.id = id
        self.allowed_instance_types = allowed_instance_types
        self.default_instance_type = default_instance_type
        self.default_allowed_instance_types = [
            "cache.m6g.large",
            "cache.m6g.xlarge",
            "cache.m6g.2xlarge",
            "cache.m6g.4xlarge",
            "cache.m6g.8xlarge",
            "cache.m6g.12xlarge",
            "cache.m6g.16xlarge",
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
            "cache.t4g.micro",
            "cache.t4g.small",
            "cache.t4g.medium",
            "cache.t3.micro",
            "cache.t3.small",
            "cache.t3.medium",
            "cache.r6g.large",
            "cache.r6g.xlarge",
            "cache.r6g.2xlarge",
            "cache.r6g.4xlarge",
            "cache.r6g.8xlarge",
            "cache.r6g.12xlarge",
            "cache.r6g.16xlarge",
            "cache.r5.large",
            "cache.r5.xlarge",
            "cache.r5.2xlarge",
            "cache.r5.4xlarge",
            "cache.r5.12xlarge",
            "cache.r5.24xlarge",
            "cache.r4.large",
            "cache.r4.xlarge",
            "cache.r4.2xlarge",
            "cache.r4.4xlarge",
            "cache.r4.8xlarge",
            "cache.r4.16xlarge"
        ]

        self.elasticache_cluster_cache_node_type_param = CfnParameter(
            self,
            "ElastiCacheClusterCacheNodeType",
            allowed_values=self.allowed_instance_types if self.allowed_instance_types else self.default_allowed_instance_types,
            default=self.default_instance_type,
            description="Required: Instance type for the cluster nodes."
        )
        self.elasticache_cluster_cache_node_type_param.override_logical_id(f"{id}ClusterCacheNodeType")
        self.elasticache_cluster_num_cache_nodes_param = CfnParameter(
            self,
            "ElastiCacheClusterNumCacheNodes",
            default=1,
            description="Required: The number of cache nodes in the cluster.",
            min_value=1,
            max_value=20,
            type="Number"
        )
        self.elasticache_cluster_num_cache_nodes_param.override_logical_id(f"{id}ClusterNumCacheNodes")
        self.sg = aws_ec2.CfnSecurityGroup(
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
        self.sg.override_logical_id(f"{id}Sg")
        self.elasticache_subnet_group = aws_elasticache.CfnSubnetGroup(
            self,
            "ElastiCacheSubnetGroup",
            description="ElastiCache subnet group",
            subnet_ids=vpc.private_subnet_ids()
        )
        self.elasticache_subnet_group.override_logical_id(f"{id}SubnetGroup")

        self.elasticache_parameter_group = aws_elasticache.CfnParameterGroup(
            self,
            "ElastiCacheParameterGroup",
            cache_parameter_group_family=self.parameter_group_family,
            description="ElastiCache parameter group",
            properties=custom_parameters
        )
        self.elasticache_parameter_group.override_logical_id(f"{id}ParameterGroup")

        if self.engine == "redis":
            az_mode = Aws.NO_VALUE
        else:
            az_mode = "cross-az" # TODO fix for memcached case of single node
        self.elasticache_cluster = aws_elasticache.CfnCacheCluster(
            self,
            "ElastiCacheCluster",
            az_mode=az_mode,
            cache_node_type=self.elasticache_cluster_cache_node_type_param.value_as_string,
            cache_parameter_group_name=self.elasticache_parameter_group.ref,
            cache_subnet_group_name=self.elasticache_subnet_group.ref,
            engine=self.engine,
            engine_version=self.engine_version,
            num_cache_nodes=self.elasticache_cluster_num_cache_nodes_param.value_as_number,
            vpc_security_group_ids=[ self.sg.ref ]
        )
        self.elasticache_cluster.override_logical_id(f"{id}Cluster")

    def metadata_parameter_group(self):
        return [
            {
                "Label": {
                    "default": "ElastiCache Configuration"
                },
                "Parameters": [
                    self.elasticache_cluster_cache_node_type_param.logical_id,
                    self.elasticache_cluster_num_cache_nodes_param.logical_id
                ]
            }
        ]

    def metadata_parameter_labels(self):
        return {
            self.elasticache_cluster_cache_node_type_param.logical_id: {
                "default": "ElastiCache Instance Type"
            },
            self.elasticache_cluster_num_cache_nodes_param.logical_id: {
                "default": "ElastiCache Cache Nodes Number"
            }
        }

class ElasticacheMemcached(ElasticacheCluster):
    def __init__(
            self,
            scope: Construct,
            id: str,
            vpc: Vpc,
            allowed_instance_types: 'list[str]' = [],
            custom_parameters: dict = {},
            default_instance_type: str = 'cache.t3.micro',
            **props):

        self.engine = "memcached"
        self.engine_version = "1.6.6"
        self.parameter_group_family = "memcached1.6"
        self.port = 11211

        super().__init__(
            scope,
            id,
            vpc=vpc,
            allowed_instance_types=allowed_instance_types,
            custom_parameters=custom_parameters,
            default_instance_type=default_instance_type,
            **props)

class ElasticacheRedis(ElasticacheCluster):
    def __init__(
            self,
            scope: Construct,
            id: str,
            vpc: Vpc,
            allowed_instance_types: 'list[str]' = [],
            custom_parameters: dict = {},
            default_instance_type: str = 'cache.t3.micro',
            **props):

        self.engine = "redis"
        self.engine_version = "6.2"
        self.parameter_group_family = "redis6.x"
        self.port = 6379

        super().__init__(
            scope,
            id,
            vpc=vpc,
            allowed_instance_types=allowed_instance_types,
            custom_parameters=custom_parameters,
            default_instance_type=default_instance_type,
            **props)
