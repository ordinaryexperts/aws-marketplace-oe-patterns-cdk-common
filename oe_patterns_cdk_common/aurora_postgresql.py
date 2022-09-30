import json

from aws_cdk import (
    Aws,
    aws_ec2,
    aws_rds,
    aws_secretsmanager,
    CfnCondition,
    CfnParameter,
    Fn,
    Tags,
    Token
)

from constructs import Construct
from oe_patterns_cdk_common.vpc import Vpc

class AuroraPostgresql(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str,
            vpc: Vpc,
            allowed_instance_types: 'list[string]' = [],
            default_engine_version: str = '13.7',
            default_instance_type: str = 'db.r5.large',
            **props):
        super().__init__(scope, id, **props)

        # utility function to parse the unique id from the stack id for
        # shorter resource names using cloudformation functions
        def append_stack_uuid(name):
            return Fn.join("-", [
                name,
                Fn.select(2, Fn.split("/", Aws.STACK_ID))
            ])

        engine_versions = [
            "10.17",
            "10.18",
            "10.18",
            "10.19",
            "10.20",
            "10.21",
            "11.9",
            "11.12",
            "11.13",
            "11.13",
            "11.14",
            "11.15",
            "11.16",
            "12.7",
            "12.8",
            "12.9",
            "12.10",
            "12.11",
            "13.3",
            "13.4",
            "13.5",
            "13.6",
            "13.7",
            "14.3"
        ]

        default_allowed_instance_types = [
            "db.r5.large",
            "db.r5.xlarge",
            "db.r5.2xlarge",
            "db.r5.4xlarge",
            "db.r5.8xlarge",
            "db.r5.12xlarge",
            "db.r4.large",
            "db.r4.xlarge",
            "db.r4.2xlarge",
            "db.r4.4xlarge",
            "db.r4.8xlarge",
            "db.r4.16xlarge",
            "db.t3.micro",
            "db.t3.small",
            "db.t3.medium",
            "db.t3.large",
            "db.t3.xlarge",
            "db.t3.2xlarge",
            "db.t2.small",
            "db.t2.medium"
        ]
        #
        # PARAMETERS
        #

        db_backup_retention_period_param = CfnParameter(
            self,
            "DbBackupRetentionPeriod",
            type="Number",
            min_value=1,
            max_value=35,
            default="7",
            description="Required: The number of days to retain automated db backups."
        )
        db_instance_class_param = CfnParameter(
            self,
            "DbInstanceClass",
            allowed_values=allowed_instance_types if allowed_instance_types else default_allowed_instance_types,
            default=default_instance_type,
            description="Required: The class profile for memory and compute capacity for the database instance."
        )
        db_engine_version_param = CfnParameter(
            self,
            "DbEngineVersion",
            allowed_values=engine_versions,
            default=default_engine_version,
            description="Required: The engine version for the the database instance."
        )
        db_snapshot_identifier_param = CfnParameter(
            self,
            "DbSnapshotIdentifier",
            default="",
            description="Optional: RDS snapshot ARN from which to restore. If specified, manually edit the secret values to specify the snapshot credentials for the application. WARNING: Changing this value will re-provision the database."
        )
        secret_arn_param = CfnParameter(
            self,
            "SecretArn",
            default="",
            description="Optional: SecretsManager secret ARN used to store database credentials and other configuration. If not specified, a secret will be created."
        )

        #
        # CONDITIONS
        #

        db_snapshot_identifier_exists_condition = CfnCondition(
            self,
            "DbSnapshotIdentifierExistsCondition",
            expression=Fn.condition_not(Fn.condition_equals(db_snapshot_identifier_param.value, ""))
        )
        secret_arn_exists_condition = CfnCondition(
            self,
            "SecretArnExistsCondition",
            expression=Fn.condition_not(Fn.condition_equals(secret_arn_param.value, ""))
        )
        secret_arn_not_exists_condition = CfnCondition(
            self,
            "SecretArnNotExistsCondition",
            expression=Fn.condition_equals(secret_arn_param.value, "")
        )

        #
        # RESOURCES
        #
        
        db_sg = aws_ec2.CfnSecurityGroup(
            self,
            "DbSg",
            group_description="Database SG",
            security_group_egress=[
                aws_ec2.CfnSecurityGroup.EgressProperty(
                    ip_protocol="-1",
                    cidr_ip="0.0.0.0/0",
                    description="all IPv4 egress traffic allowed"
                )
            ],
            vpc_id=vpc.id()
        )
        db_subnet_group = aws_rds.CfnDBSubnetGroup(
            self,
            "DbSubnetGroup",
            db_subnet_group_description="Aurora Postgresql DB Subnet Group",
            subnet_ids=vpc.private_subnet_ids()
        )
        secret = aws_secretsmanager.CfnSecret(
            self,
            "Secret",
            generate_secret_string=aws_secretsmanager.CfnSecret.GenerateSecretStringProperty(
                exclude_characters="\"@/\\\"'$,[]*?{}~\#%<>|^",
                exclude_punctuation=True,
                generate_string_key="password",
                secret_string_template=json.dumps({"username":"dbadmin"})
            ),
            name="{}/db/secret".format(Aws.STACK_NAME)
        )
        secret.cfn_options.condition = secret_arn_not_exists_condition

        db_cluster = aws_rds.CfnDBCluster(
            self,
            "DbCluster",
            backup_retention_period=db_backup_retention_period_param.value_as_number,
            db_cluster_parameter_group_name="default.aurora-postgresql10",
            db_subnet_group_name=db_subnet_group.ref,
            engine="aurora-postgresql",
            engine_mode="provisioned",
            engine_version=db_engine_version_param.value_as_string,
            master_username=Token.as_string(
                Fn.condition_if(
                    db_snapshot_identifier_exists_condition.logical_id,
                    Aws.NO_VALUE,
                    Fn.condition_if(
                        secret_arn_exists_condition.logical_id,
                        Fn.sub("{{resolve:secretsmanager:${SecretArn}:SecretString:username}}"),
                        Fn.sub("{{resolve:secretsmanager:${Secret}:SecretString:username}}")
                    ),
                )
            ),
            master_user_password=Token.as_string(
                Fn.condition_if(
                    db_snapshot_identifier_exists_condition.logical_id,
                    Aws.NO_VALUE,
                    Fn.condition_if(
                        secret_arn_exists_condition.logical_id,
                        Fn.sub("{{resolve:secretsmanager:${SecretArn}:SecretString:password}}"),
                        Fn.sub("{{resolve:secretsmanager:${Secret}:SecretString:password}}"),
                    ),
                )
            ),
            snapshot_identifier=Token.as_string(
                Fn.condition_if(
                    db_snapshot_identifier_exists_condition.logical_id,
                    db_snapshot_identifier_param.value_as_string,
                    Aws.NO_VALUE
                )
            ),
            storage_encrypted=True,
            vpc_security_group_ids=[ db_sg.ref ]
        )
        Tags.of(db_cluster).add(
            "oe:patterns:db:secretarn",
            Token.as_string(
                Fn.condition_if(
                    secret_arn_exists_condition.logical_id,
                    secret_arn_param.value_as_string,
                    secret.ref
                )
            )
        )
        db_primary_instance = aws_rds.CfnDBInstance(
            self,
            "DbPrimaryInstance",
            db_cluster_identifier=db_cluster.ref,
            db_instance_class=db_instance_class_param.value_as_string,
            db_instance_identifier=Token.as_string(
                Fn.condition_if(
                    db_snapshot_identifier_exists_condition.logical_id,
                    Aws.NO_VALUE,
                    append_stack_uuid("db")
                )
            ),
            db_parameter_group_name="default.aurora-postgresql10",
            db_subnet_group_name=db_subnet_group.ref,
            engine="aurora-postgresql",
            publicly_accessible=False
        )
