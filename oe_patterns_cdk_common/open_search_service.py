from aws_cdk import (
    Aws,
    aws_cloudformation,
    aws_ec2,
    aws_iam,
    aws_kms,
    aws_opensearchservice,
    CfnCondition,
    CfnParameter,
    Fn
)

from constructs import Construct
from oe_patterns_cdk_common.vpc import Vpc

class OpenSearchService(Construct):

    def __init__(
            self,
            scope: Construct,
            id: str,
            vpc: Vpc,
            allowed_instance_types: 'list[str]' = [],
            default_instance_type: str = 't3.small.search',
            **props):
        super().__init__(scope, id, **props)

        self.id = id
        self.port = 80

        self.default_instance_type = default_instance_type
        self.default_allowed_instance_types = [
            "c5.large.search",
            "c5.xlarge.search",
            "c5.2xlarge.search",
            "c5.4xlarge.search",
            "c5.9xlarge.search",
            "c5.18xlarge.search",
            "c6g.large.search",
            "c6g.xlarge.search",
            "c6g.2xlarge.search",
            "c6g.4xlarge.search",
            "c6g.8xlarge.search",
            "c6g.12xlarge.search",
            "i3.large.search",
            "i3.xlarge.search",
            "i3.2xlarge.search",
            "i3.4xlarge.search",
            "i3.8xlarge.search",
            "i3.16xlarge.search",
            "m5.large.search",
            "m5.xlarge.search",
            "m5.2xlarge.search",
            "m5.4xlarge.search",
            "m5.12xlarge.search",
            "m6g.large.search",
            "m6g.xlarge.search",
            "m6g.2xlarge.search",
            "m6g.4xlarge.search",
            "m6g.8xlarge.search",
            "m6g.12xlarge.search",
            "r5.large.search",
            "r5.xlarge.search",
            "r5.2xlarge.search",
            "r5.4xlarge.search",
            "r5.12xlarge.search",
            "r6g.large.search",
            "r6g.xlarge.search",
            "r6g.2xlarge.search",
            "r6g.4xlarge.search",
            "r6g.8xlarge.search",
            "r6g.12xlarge.search",
            "r6gd.large.search",
            "r6gd.xlarge.search",
            "r6gd.2xlarge.search",
            "r6gd.4xlarge.search",
            "r6gd.8xlarge.search",
            "r6gd.12xlarge.search",
            "r6gd.16xlarge.search",
            "t3.small.search",
            "t3.medium.search"
        ]

        self.open_search_service_ebs_volume_size_param = CfnParameter(
            self,
            "OpenSearchServiceEbsVolumeSize",
            default=10,
            description="Required: The size of the EBS volume for the OpenSearch node.",
            type="Number"
        )
        self.open_search_service_ebs_volume_size_param.override_logical_id(f"{id}EbsVolumeSize")

        self.open_search_service_node_type_param = CfnParameter(
            self,
            "OpenSearchServiceNodeType",
            allowed_values=self.default_allowed_instance_types,
            default=self.default_instance_type,
            description="Required: Instance type for the OpenSearch Service nodes."
        )
        self.open_search_service_node_type_param.override_logical_id(f"{id}NodeType")

        self.key = aws_kms.CfnKey(
            self,
            'OpenSearchServiceKey',
            description="Encrypt OpenSearch",
            enable_key_rotation=True,
            enabled=True,
            key_policy=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["kms:*"],
                        principals=[aws_iam.ArnPrincipal(f"arn:{Aws.PARTITION}:iam::{Aws.ACCOUNT_ID}:root")],
                        resources=["*"]
                    )
                ]
            )
        )
        self.key.override_logical_id(f"{id}Key")

        self.sg = aws_ec2.CfnSecurityGroup(
            self,
            "OpenSearchServiceSg",
            group_description="Open Search Service SG",
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

        self.create_service_linked_role_param = CfnParameter(
            self,
            "OpenSearchServiceCreateServiceLinkedRole",
            allowed_values=[ "true", "false" ],
            default="true",
            description="Whether or not to create a Service Linked Role for OpenSearch VPC access."
        )
        self.create_service_linked_role_param.override_logical_id(f"{id}CreateServiceLinkedRole")

        self.create_service_linked_role_condition = CfnCondition(
            self,
            "OpenSearchServiceCreateServiceLinkedRoleCondition",
            expression=Fn.condition_equals(self.create_service_linked_role_param.value, "true")
        )
        self.create_service_linked_role_condition.override_logical_id(f"{id}CreateServiceLinkedRoleCondition")

        self.service_linked_role = aws_iam.CfnServiceLinkedRole(
            self,
            "OpenSearchServiceServiceLinkedRole",
            aws_service_name="opensearchservice.amazonaws.com"
        )
        self.service_linked_role.cfn_options.condition=self.create_service_linked_role_condition
        self.service_linked_role.override_logical_id(f"{id}ServiceLinkedRole")

        self.service_linked_role_wait_handle = aws_cloudformation.CfnWaitConditionHandle(
            self,
            "OpenSearchServiceWaitConditionHandle"
        )
        self.service_linked_role_wait_handle.override_logical_id(f"{id}WaitConditionHandle")
        self.service_linked_role_wait_handle.cfn_options.metadata = {
            "ServiceLinkedRoleAvailable": Fn.condition_if(
                self.create_service_linked_role_condition.logical_id,
                self.service_linked_role.ref,
                Aws.NO_VALUE
            )
        }

        access_policies=aws_iam.PolicyDocument(
            statements=[
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=["es:*"],
                    principals=[aws_iam.AnyPrincipal()],
                    resources=[
                        f"arn:{Aws.PARTITION}:es:{Aws.REGION}:{Aws.ACCOUNT_ID}:domain/*"
                    ]
                )
            ]
        )

        self.domain = aws_opensearchservice.CfnDomain(
            self,
            "OpenSearchServiceDomain",
            access_policies=access_policies,
            cluster_config=aws_opensearchservice.CfnDomain.ClusterConfigProperty(
                dedicated_master_enabled=False,
                instance_count=1,
                instance_type=self.open_search_service_node_type_param.value_as_string,
                zone_awareness_enabled=False
            ),
            ebs_options=aws_opensearchservice.CfnDomain.EBSOptionsProperty(
                ebs_enabled=True,
                volume_size=self.open_search_service_ebs_volume_size_param.value_as_number,
                volume_type="gp3"
            ),
            encryption_at_rest_options=aws_opensearchservice.CfnDomain.EncryptionAtRestOptionsProperty(
                enabled=True,
                kms_key_id=self.key.attr_key_id
            ),
            engine_version="Elasticsearch_7.10",
            node_to_node_encryption_options=aws_opensearchservice.CfnDomain.NodeToNodeEncryptionOptionsProperty(
                enabled=True
            ),
            vpc_options=aws_opensearchservice.CfnDomain.VPCOptionsProperty(
                security_group_ids=[ self.sg.ref ],
                subnet_ids=[vpc.private_subnet1_id()]
            )
        )
        self.domain.override_logical_id(f"{id}Domain")
        self.domain.node.add_dependency(self.service_linked_role_wait_handle)

    def metadata_parameter_group(self):
        return [
            {
                "Label": {
                    "default": "OpenSearch Service Configuration"
                },
                "Parameters": [
                    self.open_search_service_ebs_volume_size_param.logical_id,
                    self.open_search_service_node_type_param.logical_id,
                    self.create_service_linked_role_param.logical_id
                ]
            }
        ]

    def metadata_parameter_labels(self):
        return {
            self.open_search_service_ebs_volume_size_param.logical_id: {
                "default": "OpenSearch Service EBS Volume Size"
            },
            self.open_search_service_node_type_param.logical_id: {
                "default": "OpenSearch Service Instance Type"
            },
            self.create_service_linked_role_param.logical_id: {
                "default": "OpenSearch Service Create Service Linked Role"
            }
        }
