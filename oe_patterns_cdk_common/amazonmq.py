from aws_cdk import (
    aws_amazonmq,
    aws_ec2
)

from constructs import Construct
from oe_patterns_cdk_common.db_secret import DbSecret
from oe_patterns_cdk_common.vpc import Vpc

class AmazonMQ(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str,
            db_secret: DbSecret,
            vpc: Vpc,
            allowed_instance_types: 'list[str]' = [],
            default_instance_type: str = 'mq.m5.large',
            **props):
        super().__init__(scope, id, **props)

        self.id = id
        self.allowed_instance_types = allowed_instance_types
        self.default_instance_type = default_instance_type
        self.default_allowed_instance_types = []

        #
        # RESOURCES
        #
        self.sg = aws_ec2.CfnSecurityGroup(
            self,
            "MqSg",
            group_description="AmazonMQ SG",
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

        self.broker = aws_amazonmq.CfnBroker(
            self,
            "Broker",
            auto_minor_version_upgrade=True,
            broker_name="TODO",
            deployment_mode="SINGLE_INSTANCE",
            engine_type="engineType",
            engine_version="RABBITMQ",
            host_instance_type="hostInstanceType",
            publicly_accessible=False,
            users=[aws_amazonmq.CfnBroker.UserProperty(
                password="password",
                username="username"
            )],
            logs=aws_amazonmq.CfnBroker.LogListProperty(
                audit=False,
                general=False
            ),
            security_groups=["securityGroups"],
            subnet_ids=["subnetIds"]
        )
        self.broker.override_logical_id(f"{id}Broker")


    def metadata_parameter_group(self):
        return [
            {
                "Label": {
                    "default": "AmazonMQ Configuration"
                },
                "Parameters": [
                    self.amazonmq_instance_class_param.logical_id
                ]
            }
        ]

    def metadata_parameter_labels(self):
        return {
            self.amazonmq_instance_class_param.logical_id: {
                "default": "AmazonMQ Instance Type"
            }
        }

class RabbitMQ(AmazonMQ):
    def __init__(
            self,
            scope: Construct,
            id: str,
            db_secret: DbSecret,
            vpc: Vpc,
            allowed_instance_types: 'list[str]' = [],
            default_instance_type: str = 'db.r5.large',
            **props):

        self.engine_type = "RABBITMQ"
        self.engine_version = "3.10.10"
        self.port = 5671

        super().__init__(
            scope,
            id,
            db_secret=db_secret,
            vpc=vpc,
            allowed_instance_types=allowed_instance_types,
            default_instance_type=default_instance_type,
            **props)
