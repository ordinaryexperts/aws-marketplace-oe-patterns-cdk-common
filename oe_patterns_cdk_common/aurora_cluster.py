from aws_cdk import (
    Aws,
    aws_ec2,
    aws_rds,
    CfnCondition,
    CfnParameter,
    CfnRule,
    CfnRuleAssertion,
    Fn,
    Tags,
    Token
)

from constructs import Construct
from oe_patterns_cdk_common.db_secret import DbSecret
from oe_patterns_cdk_common.vpc import Vpc

class AuroraCluster(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str,
            db_secret: DbSecret,
            vpc: Vpc,
            allowed_instance_types: 'list[str]' = [],
            database_name: str = None,
            default_instance_type: str = 'db.t4g.medium',
            **props):
        super().__init__(scope, id, **props)

        self.id = id
        self.allowed_instance_types = allowed_instance_types
        self.database_name = database_name

        self.default_instance_type = default_instance_type
        self.default_allowed_instance_types = [
            "db.t3.medium",
            "db.t3.large",
            "db.t4g.medium",
            "db.t4g.large",
            "db.r5.large",
            "db.r5.xlarge",
            "db.r5.2xlarge",
            "db.r5.4xlarge",
            "db.r5.8xlarge",
            "db.r5.12xlarge",
            "db.r5.16xlarge",
            "db.r5.24xlarge",
            "db.r6i.large",
            "db.r6i.xlarge",
            "db.r6i.2xlarge",
            "db.r6i.4xlarge",
            "db.r6i.8xlarge",
            "db.r6i.12xlarge",
            "db.r6i.16xlarge",
            "db.r6i.24xlarge",
            "db.r6i.32xlarge",
            "db.r6g.large",
            "db.r6g.xlarge",
            "db.r6g.2xlarge",
            "db.r6g.4xlarge",
            "db.r6g.8xlarge",
            "db.r6g.12xlarge",
            "db.r6g.16xlarge",
            "db.x2g.large",
            "db.x2g.xlarge",
            "db.x2g.2xlarge",
            "db.x2g.4xlarge",
            "db.x2g.8xlarge",
            "db.x2g.12xlarge",
            "db.x2g.16xlarge"
        ]

        #
        # PARAMETERS
        #

        self.db_backup_retention_period_param = CfnParameter(
            self,
            "DbBackupRetentionPeriod",
            type="Number",
            min_value=1,
            max_value=35,
            default="7",
            description="Required: The number of days to retain automated db backups."
        )
        self.db_backup_retention_period_param.override_logical_id(f"{id}BackupRetentionPeriod")
        self.db_instance_class_param = CfnParameter(
            self,
            "DbInstanceClass",
            allowed_values=self.allowed_instance_types if self.allowed_instance_types else self.default_allowed_instance_types,
            default=self.default_instance_type,
            description="Required: The class profile for memory and compute capacity for the database instance."
        )
        self.db_instance_class_param.override_logical_id(f"{id}InstanceClass")
        self.db_snapshot_identifier_param = CfnParameter(
            self,
            "DbSnapshotIdentifier",
            default="",
            description="Optional: RDS snapshot ARN from which to restore. If specified, manually edit the secret values to specify the snapshot credentials for the application. WARNING: Changing this value will re-provision the database."
        )
        self.db_snapshot_identifier_param.override_logical_id(f"{id}SnapshotIdentifier")

        #
        # CONDITIONS
        #

        self.db_snapshot_identifier_exists_condition = CfnCondition(
            self,
            "DbSnapshotIdentifierExistsCondition",
            expression=Fn.condition_not(Fn.condition_equals(self.db_snapshot_identifier_param.value, ""))
        )
        self.db_snapshot_identifier_exists_condition.override_logical_id(f"{id}SnapshotIdentifierExistsCondition")
        self.db_snapshot_secret_rule = CfnRule(
            self,
            "DbSnapshotIdentifierAndSecretRequiredRule",
            assertions=[
                CfnRuleAssertion(
                    assert_=Fn.condition_not(Fn.condition_equals(db_secret.secret_arn_param.value_as_string, "")),
                    assert_description="When restoring the database from a snapshot, a secret ARN must also be supplied, prepopulated with username and password key-value pairs which correspond to the snapshot image"
                )
            ],
            rule_condition=Fn.condition_not(
                Fn.condition_equals(self.db_snapshot_identifier_param.value_as_string, "")
            )
        )
        self.db_snapshot_secret_rule.override_logical_id(f"{id}SnapshotIdentifierAndSecretRequiredRule")

        #
        # RESOURCES
        #
        self.sg = aws_ec2.CfnSecurityGroup(
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
        self.sg.override_logical_id(f"{id}Sg")

        self.db_subnet_group = aws_rds.CfnDBSubnetGroup(
            self,
            "DbSubnetGroup",
            db_subnet_group_description="Aurora Postgresql DB Subnet Group",
            subnet_ids=vpc.private_subnet_ids()
        )
        self.db_subnet_group.override_logical_id(f"{id}SubnetGroup")

        self.db_cluster = aws_rds.CfnDBCluster(
            self,
            "DbCluster",
            backup_retention_period=self.db_backup_retention_period_param.value_as_number,
            database_name=self.database_name,
            db_cluster_parameter_group_name=self.parameter_group_name,
            db_subnet_group_name=self.db_subnet_group.ref,
            engine=self.engine,
            engine_mode="provisioned",
            engine_version=self.engine_version,
            master_username=Token.as_string(
                Fn.condition_if(
                    self.db_snapshot_identifier_exists_condition.logical_id,
                    Aws.NO_VALUE,
                    Fn.condition_if(
                        db_secret.secret_arn_exists_condition.logical_id,
                        Fn.sub("{{resolve:secretsmanager:${DbSecretArn}:SecretString:username}}"),
                        Fn.sub("{{resolve:secretsmanager:${DbSecret}:SecretString:username}}")
                    ),
                )
            ),
            master_user_password=Token.as_string(
                Fn.condition_if(
                    self.db_snapshot_identifier_exists_condition.logical_id,
                    Aws.NO_VALUE,
                    Fn.condition_if(
                        db_secret.secret_arn_exists_condition.logical_id,
                        Fn.sub("{{resolve:secretsmanager:${DbSecretArn}:SecretString:password}}"),
                        Fn.sub("{{resolve:secretsmanager:${DbSecret}:SecretString:password}}"),
                    ),
                )
            ),
            port=self.port,
            snapshot_identifier=Token.as_string(
                Fn.condition_if(
                    self.db_snapshot_identifier_exists_condition.logical_id,
                    self.db_snapshot_identifier_param.value_as_string,
                    Aws.NO_VALUE
                )
            ),
            storage_encrypted=True,
            vpc_security_group_ids=[ self.sg.ref ]
        )
        self.db_cluster.override_logical_id(f"{id}Cluster")
        Tags.of(self.db_cluster).add(
            "oe:patterns:db:secretarn",
            db_secret.secret_arn()
        )
        self.db_primary_instance = aws_rds.CfnDBInstance(
            self,
            "DbPrimaryInstance",
            db_cluster_identifier=self.db_cluster.ref,
            db_instance_class=self.db_instance_class_param.value_as_string,
            db_instance_identifier=Token.as_string(
                Fn.condition_if(
                    self.db_snapshot_identifier_exists_condition.logical_id,
                    Aws.NO_VALUE,
                    Fn.join("-", [
                        "db",
                        Fn.select(2, Fn.split("/", Aws.STACK_ID))
                    ])
                )
            ),
            db_parameter_group_name=self.parameter_group_name,
            db_subnet_group_name=self.db_subnet_group.ref,
            engine=self.engine,
            publicly_accessible=False
        )
        self.db_primary_instance.override_logical_id(f"{id}PrimaryInstance")

    def metadata_parameter_group(self):
        return [
            {
                "Label": {
                    "default": "Database Configuration"
                },
                "Parameters": [
                    self.db_backup_retention_period_param.logical_id,
                    self.db_instance_class_param.logical_id,
                    self.db_snapshot_identifier_param.logical_id
                ]
            }
        ]

    def metadata_parameter_labels(self):
        return {
            self.db_backup_retention_period_param.logical_id: {
                "default": "Database Backup Retention Period"
            },
            self.db_instance_class_param.logical_id: {
                "default": "Database Instance Type"
            },
            self.db_snapshot_identifier_param.logical_id: {
                "default": "Database Snapshot Identifier"
            }
        }

class AuroraMysql(AuroraCluster):
    def __init__(
            self,
            scope: Construct,
            id: str,
            db_secret: DbSecret,
            vpc: Vpc,
            allowed_instance_types: 'list[str]' = [],
            default_instance_type: str = '',
            **props):

        self.engine = "aurora-mysql"
        self.engine_version = "5.7.mysql_aurora.2.11.1"
        self.parameter_group_name = "default.aurora-mysql5.7"
        self.port = 3306

        super().__init__(
            scope,
            id,
            db_secret=db_secret,
            vpc=vpc,
            allowed_instance_types=allowed_instance_types,
            default_instance_type=default_instance_type,
            **props)

class AuroraPostgresql(AuroraCluster):
    def __init__(
            self,
            scope: Construct,
            id: str,
            db_secret: DbSecret,
            vpc: Vpc,
            allowed_instance_types: 'list[str]' = [],
            default_instance_type: str = '',
            **props):

        self.engine = "aurora-postgresql"
        self.engine_version = "13.7"
        self.parameter_group_name = "default.aurora-postgresql13"
        self.port = 5432

        super().__init__(
            scope,
            id,
            db_secret=db_secret,
            vpc=vpc,
            allowed_instance_types=allowed_instance_types,
            default_instance_type=default_instance_type,
            **props)
