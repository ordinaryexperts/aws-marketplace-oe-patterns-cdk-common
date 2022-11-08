from aws_cdk import (
    Aws,
    aws_ec2,
    aws_kms,
    aws_opensearchservice,
    CfnTag
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
            default_instance_type: str = 'm5.large.search',
            **props):
        super().__init__(scope, id, **props)

        self.key = aws_kms.Key(
            self,
            'OpenSearchServiceKey',
            enable_key_rotation=False
        )

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

        self.domain = aws_opensearchservice.CfnDomain(
            self,
            "OpenSearchServiceDomain",
            # access_policies=access_policies,
            advanced_options={
                "override_main_response_version": "true"
            },
            advanced_security_options=aws_opensearchservice.CfnDomain.AdvancedSecurityOptionsInputProperty(
                enabled=True,
                internal_user_database_enabled=True,
                master_user_options=aws_opensearchservice.CfnDomain.MasterUserOptionsProperty(
                    master_user_name="masterUserName",
                    master_user_password="masterUserPassword"
                )
            ),
            cluster_config=aws_opensearchservice.CfnDomain.ClusterConfigProperty(
                dedicated_master_enabled=False,
                instance_count=1,
                instance_type="m5.large.search",
                zone_awareness_enabled=False
            ),
            domain_endpoint_options=aws_opensearchservice.CfnDomain.DomainEndpointOptionsProperty(
                enforce_https=True,
                tls_security_policy="Policy-Min-TLS-1-2-2019-07"
            ),
            # domain_name="domainName",
            # ebs_options=aws_opensearchservice.CfnDomain.EBSOptionsProperty(
            #     ebs_enabled=False
            # ),
            encryption_at_rest_options=aws_opensearchservice.CfnDomain.EncryptionAtRestOptionsProperty(
                enabled=True,
                kms_key_id=self.key.key_id
            ),
            engine_version="Elasticsearch_7.10",
            # log_publishing_options={
            #     "log_publishing_options_key": aws_opensearchservice.CfnDomain.LogPublishingOptionProperty(
            #         cloud_watch_logs_log_group_arn="cloudWatchLogsLogGroupArn",
            #         enabled=True
            #     )
            # },
            node_to_node_encryption_options=aws_opensearchservice.CfnDomain.NodeToNodeEncryptionOptionsProperty(
                enabled=True
            ),
            snapshot_options=aws_opensearchservice.CfnDomain.SnapshotOptionsProperty(
                automated_snapshot_start_hour=1
            ),
            tags=[CfnTag(
                key="key",
                value="value"
            )],
            vpc_options=aws_opensearchservice.CfnDomain.VPCOptionsProperty(
                security_group_ids=[ self.sg.ref ],
                subnet_ids=vpc.private_subnet_ids()
            )
        )
