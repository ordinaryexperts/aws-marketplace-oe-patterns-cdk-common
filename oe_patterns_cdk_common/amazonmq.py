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

        self.cfn_broker = aws_amazonmq.CfnBroker(
            self,
            "MqBroker",
            auto_minor_version_upgrade=True,
            broker_name="TODO",
            deployment_mode="SINGLE_INSTANCE",
            engine_type="engineType",
            engine_version="RABBITMQ",
            host_instance_type="hostInstanceType",
            publicly_accessible=False,
            users=[aws_amazonmq.CfnBroker.UserProperty(
                password="password",
                username="username",

                # the properties below are optional
                console_access=False,
                groups=["groups"]
            )],

            # the properties below are optional
            authentication_strategy="authenticationStrategy",
            configuration=aws_amazonmq.CfnBroker.ConfigurationIdProperty(
                id="id",
                revision=123
            ),
            encryption_options=aws_amazonmq.CfnBroker.EncryptionOptionsProperty(
                use_aws_owned_key=False,

                # the properties below are optional
                kms_key_id="kmsKeyId"
            ),
            ldap_server_metadata=aws_amazonmq.CfnBroker.LdapServerMetadataProperty(
                hosts=["hosts"],
                role_base="roleBase",
                role_search_matching="roleSearchMatching",
                service_account_password="serviceAccountPassword",
                service_account_username="serviceAccountUsername",
                user_base="userBase",
                user_search_matching="userSearchMatching",

                # the properties below are optional
                role_name="roleName",
                role_search_subtree=False,
                user_role_name="userRoleName",
                user_search_subtree=False
            ),
            logs=aws_amazonmq.CfnBroker.LogListProperty(
                audit=False,
                general=False
            ),
            maintenance_window_start_time=aws_amazonmq.CfnBroker.MaintenanceWindowProperty(
                day_of_week="dayOfWeek",
                time_of_day="timeOfDay",
                time_zone="timeZone"
            ),
            security_groups=["securityGroups"],
            storage_type="storageType",
            subnet_ids=["subnetIds"],
            tags=[aws_amazonmq.CfnBroker.TagsEntryProperty(
                key="key",
                value="value"
            )]
        )


    def metadata_parameter_group(self):
        return [
            {
                "Label": {
                    "default": " Configuration"
                },
                "Parameters": [
                    self.db_instance_class_param.logical_id
                ]
            }
        ]

    def metadata_parameter_labels(self):
        return {
            self.db_instance_class_param.logical_id: {
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
