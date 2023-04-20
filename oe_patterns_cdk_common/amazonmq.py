from aws_cdk import (
    aws_amazonmq,
    aws_ec2,
    CfnParameter,
    Fn
)

from constructs import Construct
from oe_patterns_cdk_common.secret import Secret
from oe_patterns_cdk_common.util import Util
from oe_patterns_cdk_common.vpc import Vpc

DEFAULT_INSTANCE_TYPE = 'mq.t3.micro'

class AmazonMQ(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str,
            secret: Secret,
            vpc: Vpc,
            allowed_instance_types: 'list[str]' = [],
            default_instance_type: str = DEFAULT_INSTANCE_TYPE,
            **props):
        super().__init__(scope, id, **props)

        self.id = id
        self.allowed_instance_types = allowed_instance_types
        self.default_instance_type = default_instance_type
        self.default_allowed_instance_types = [
            "mq.t3.micro",
            "mq.m5.large",
            "mq.m5.xlarge",
            "mq.m5.2xlarge",
            "mq.m5.4xlarge"
        ]

        #
        # RESOURCES
        #
        self.instance_class_param = CfnParameter(
            self,
            "BrokerInstanceClass",
            allowed_values=self.allowed_instance_types if self.allowed_instance_types else self.default_allowed_instance_types,
            default=self.default_instance_type,
            description="Required: The class profile for memory and compute capacity for the database instance."
        )
        self.instance_class_param.override_logical_id(f"{id}InstanceClass")

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
            broker_name=Util.append_stack_uuid("rabbitmq"),
            deployment_mode="SINGLE_INSTANCE",
            engine_type=self.engine_type,
            engine_version=self.engine_version,
            host_instance_type=self.instance_class_param.value_as_string,
            publicly_accessible=False,
            users=[],
            logs=aws_amazonmq.CfnBroker.LogListProperty(
                general=True
            ),
            security_groups=[self.sg.ref],
            subnet_ids=[vpc.private_subnet1_id()]
        )
        self.broker.override_logical_id(f"{id}Broker")
        self.broker.add_override(
            "Properties.Users",
            [
                Fn.condition_if(
                    secret.secret_arn_exists_condition.logical_id,
                    {
                        'Password':Fn.sub(f"{{{{resolve:secretsmanager:${{{secret.secret_arn_param.logical_id}}}:SecretString:password}}}}"),
                        'Username':Fn.sub(f"{{{{resolve:secretsmanager:${{{secret.secret_arn_param.logical_id}}}:SecretString:username}}}}")
                    },
                    {
                        'Password':Fn.sub(f"{{{{resolve:secretsmanager:${{{secret.secret.logical_id}}}:SecretString:password}}}}"),
                        'Username':Fn.sub(f"{{{{resolve:secretsmanager:${{{secret.secret.logical_id}}}:SecretString:username}}}}")
                    }
                )
            ]
        )


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
            secret: Secret,
            vpc: Vpc,
            allowed_instance_types: 'list[str]' = [],
            default_instance_type: str = DEFAULT_INSTANCE_TYPE,
            **props):

        self.engine_type = "RABBITMQ"
        self.engine_version = "3.10.20"
        self.port = 5671

        super().__init__(
            scope,
            id,
            secret=secret,
            vpc=vpc,
            allowed_instance_types=allowed_instance_types,
            default_instance_type=default_instance_type,
            **props)
