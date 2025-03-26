from aws_cdk import (
    Aws,
    aws_autoscaling,
    aws_backup,
    aws_cloudwatch,
    aws_ec2,
    aws_events,
    aws_iam,
    aws_lambda,
    aws_logs,
    CfnAutoScalingReplacingUpdate,
    CfnAutoScalingRollingUpdate,
    CfnAutoScalingScheduledAction,
    CfnCondition,
    CfnCreationPolicy,
    CfnDeletionPolicy,
    CfnOutput,
    CfnParameter,
    CfnResourceSignal,
    CfnTag,
    CfnUpdatePolicy,
    CustomResource,
    Duration,
    Fn,
    Tags,
    Token
)

from constructs import Construct
from oe_patterns_cdk_common.util import Util
from oe_patterns_cdk_common.vpc import Vpc

class Asg(Construct):

    TWO_YEARS_IN_DAYS=731

    GRAVITON_INSTANCE_TYPES = [
        "t4g.nano", "t4g.micro", "t4g.small", "t4g.medium", "t4g.large", "t4g.xlarge", "t4g.2xlarge",
        "a1.medium", "a1.large", "a1.xlarge", "a1.2xlarge", "a1.4xlarge", "a1.metal",
        "c7g.medium", "c7g.large", "c7g.xlarge", "c7g.2xlarge", "c7g.4xlarge", "c7g.8xlarge", "c7g.12xlarge", "c7g.16xlarge", "c7g.metal",
        "m7g.medium", "m7g.large", "m7g.xlarge", "m7g.2xlarge", "m7g.4xlarge", "m7g.8xlarge", "m7g.12xlarge", "m7g.16xlarge", "m7g.metal",
        "r7g.medium", "r7g.large", "r7g.xlarge", "r7g.2xlarge", "r7g.4xlarge", "r7g.8xlarge", "r7g.12xlarge", "r7g.16xlarge", "r7g.metal"
    ]

    STANDARD_INSTANCE_TYPES = [
        "t2.nano", "t2.micro", "t2.small", "t2.medium", "t2.large", "t2.xlarge", "t2.2xlarge",
        "t3.nano", "t3.micro", "t3.small", "t3.medium", "t3.large", "t3.xlarge", "t3.2xlarge",
        "c5.large", "c5.xlarge", "c5.2xlarge", "c5.4xlarge", "c5.9xlarge", "c5.12xlarge", "c5.18xlarge", "c5.24xlarge", "c5.metal",
        "c5d.large", "c5d.xlarge", "c5d.2xlarge", "c5d.4xlarge", "c5d.9xlarge", "c5d.12xlarge", "c5d.18xlarge", "c5d.24xlarge",
        "m5.large", "m5.xlarge", "m5.2xlarge", "m5.4xlarge", "m5.8xlarge", "m5.12xlarge", "m5.16xlarge", "m5.24xlarge", "m5.metal",
        "m5d.large", "m5d.xlarge", "m5d.2xlarge", "m5d.4xlarge", "m5d.8xlarge", "m5d.12xlarge", "m5d.16xlarge", "m5d.24xlarge", "m5d.metal",
        "r5.large", "r5.xlarge", "r5.2xlarge", "r5.4xlarge", "r5.8xlarge", "r5.12xlarge", "r5.16xlarge", "r5.24xlarge", "r5.metal",
        "r5d.large", "r5d.xlarge", "r5d.2xlarge", "r5d.4xlarge", "r5d.8xlarge", "r5d.12xlarge", "r5d.16xlarge", "r5d.24xlarge", "r5d.metal"
    ]

    def __init__(
            self,
            scope: Construct,
            id: str,
            ami_id: str,
            vpc: Vpc,
            additional_iam_role_policies: 'list[object]' = [],
            allow_associate_address: bool = False,
            allow_update_secret: bool = False,
            allowed_instance_types: 'list[str]' = [],
            create_and_update_timeout_minutes: int = 15,
            default_instance_type: str = None,
            deployment_rolling_update: bool = False,
            excluded_instance_families: 'list[str]' = [],
            excluded_instance_sizes: 'list[str]' = [],
            health_check_type: str = 'EC2',
            notification_topic_arn: str = None,
            pipeline_bucket_arn: str = None,
            root_volume_device_name: str = "/dev/sda1",
            root_volume_size: int = 0,
            secret_arns: 'list[str]' = [],
            singleton: bool = False,
            use_data_volume: bool = False,
            use_graviton: bool = True,
            use_public_subnets: bool = False,
            user_data_contents: str = None,
            user_data_variables: dict = {},
            **props):
        super().__init__(scope, id, **props)
        self._singleton = singleton
        self._use_data_volume = use_data_volume

        if use_graviton:
            if not default_instance_type:
                default_instance_type = 't4g.small'
            default_allowed_instance_types = Asg.GRAVITON_INSTANCE_TYPES
        else:
            if not default_instance_type:
                default_instance_type = 't3.micro'
            default_allowed_instance_types = Asg.STANDARD_INSTANCE_TYPES

        filtered_defaults = []
        for item in default_allowed_instance_types:
            if not any(item.startswith(family) for family in excluded_instance_families) and \
               not any(item.endswith(size) for size in excluded_instance_sizes):
                filtered_defaults.append(item)

        self.instance_type_param = CfnParameter(
            self,
            "AsgInstanceType",
            allowed_values=allowed_instance_types if allowed_instance_types else filtered_defaults,
            default=default_instance_type,
            description="Required: The EC2 instance type for the application Auto Scaling Group."
        )
        self.instance_type_param.override_logical_id(f"{id}InstanceType")

        self.ami_id_param = CfnParameter(
            self,
            "AsgAmiId",
            default=ami_id,
            description="Required: The AMI id for the application Auto Scaling Group."
        )
        self.ami_id_param.override_logical_id(f"{id}AmiId")

        self.key_name_param = CfnParameter(
            self,
            "AsgKeyName",
            default="",
            description="Optional: The EC2 key pair name for the instance."
        )
        self.key_name_param.override_logical_id(f"{id}KeyName")
        self.key_name_condition = CfnCondition(
            self,
            "AsgKeyNameCondition",
            expression=Fn.condition_not(Fn.condition_equals(self.key_name_param.value, ""))
        )
        self.key_name_condition.override_logical_id(f"{id}KeyNameCondition")

        self.reprovision_string_param = CfnParameter(
            self,
            "AsgReprovisionString",
            default="",
            description="Optional: Changes to this parameter will force instance reprovision on the next CloudFormation update."
        )
        self.reprovision_string_param.override_logical_id(f"{id}ReprovisionString")
        if not singleton:
            self.desired_capacity_param = CfnParameter(
                self,
                "AsgDesiredCapacity",
                default=1,
                description="Required: The desired capacity of the Auto Scaling Group.",
                min_value=0,
                type="Number"
            )
            self.desired_capacity_param.override_logical_id(f"{id}DesiredCapacity")
            self.max_size_param = CfnParameter(
                self,
                "AsgMaxSize",
                default=2,
                description="Required: The maximum size of the Auto Scaling Group.",
                min_value=0,
                type="Number"
            )
            self.max_size_param.override_logical_id(f"{id}MaxSize")
            self.min_size_param = CfnParameter(
                self,
                "AsgMinSize",
                default=1,
                description="Required: The minimum size of the Auto Scaling Group.",
                min_value=0,
                type="Number"
            )
            self.min_size_param.override_logical_id(f"{id}MinSize")

        # cloudwatch
        self.app_log_group = aws_logs.CfnLogGroup(
            self,
            "AppLogGroup",
            retention_in_days=Asg.TWO_YEARS_IN_DAYS
        )
        self.app_log_group.cfn_options.update_replace_policy = CfnDeletionPolicy.RETAIN
        self.app_log_group.cfn_options.deletion_policy = CfnDeletionPolicy.RETAIN
        self.app_log_group.override_logical_id(f"{id}AppLogGroup")
        self.system_log_group = aws_logs.CfnLogGroup(
            self,
            "SystemLogGroup",
            retention_in_days=Asg.TWO_YEARS_IN_DAYS
        )
        self.system_log_group.cfn_options.update_replace_policy = CfnDeletionPolicy.RETAIN
        self.system_log_group.cfn_options.deletion_policy = CfnDeletionPolicy.RETAIN
        self.system_log_group.override_logical_id(f"{id}SystemLogGroup")

        # iam
        policies = [
            aws_iam.CfnRole.PolicyProperty(
                policy_document=aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "ec2:DescribeVolumes",
                                "ec2:DescribeTags",
                                "cloudwatch:GetMetricStatistics",
                                "cloudwatch:ListMetrics",
                                "cloudwatch:PutMetricData"
                            ],
                            resources=[ "*" ]
                        )
                    ]
                ),
                policy_name="AllowStreamMetricsToCloudWatch"
            ),
            aws_iam.CfnRole.PolicyProperty(
                policy_document=aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[ "autoscaling:Describe*" ],
                            resources=[ "*" ]
                        )
                    ]
                ),
                policy_name="AllowDescribeAutoScaling"
            )
        ]
        policies.append(
            aws_iam.CfnRole.PolicyProperty(
                policy_document=aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogStream",
                                "logs:DescribeLogStreams",
                                "logs:PutLogEvents"
                            ],
                            resources=[
                                self.system_log_group.attr_arn,
                                self.app_log_group.attr_arn
                            ]
                        )
                    ]
                ),
                policy_name="AllowStreamLogsToCloudWatch"
            )
        )
        if allow_associate_address:
            policies.append(
                aws_iam.CfnRole.PolicyProperty(
                    policy_document=aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "ec2:AssociateAddress",
                                ],
                                resources=[ "*" ]
                            )
                        ]
                    ),
                    policy_name="AllowAssociateAddress"
                )
            )
        if allow_update_secret:
            policies.append(
                aws_iam.CfnRole.PolicyProperty(
                    policy_document=aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "secretsmanager:UpdateSecret"
                                ],
                                resources=[
                                    f"arn:{Aws.PARTITION}:secretsmanager:{Aws.REGION}:{Aws.ACCOUNT_ID}:secret:{Aws.STACK_NAME}/instance/credentials-*"
                                ]
                            )
                        ]
                    ),
                    policy_name="AllowUpdateInstanceSecret"
                )
            )
        if use_data_volume:
            policies.append(
                aws_iam.CfnRole.PolicyProperty(
                    policy_document=aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "ec2:AttachVolume",
                                    "ec2:DescribeVolumes"
                                ],
                                resources=["*"]
                            )
                        ]
                    ),
                    policy_name="AllowAttachVolume"
                )
            )
        if pipeline_bucket_arn:
            policies.append(
                aws_iam.CfnRole.PolicyProperty(
                    policy_document=aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "s3:Get*",
                                    "s3:Head*"
                                ],
                                resources = [ pipeline_bucket_arn ]
                            )
                        ]
                    ),
                    policy_name="AllowReadFromPipelineBucket"
                )
            )
        if secret_arns:
            policies.append(
                aws_iam.CfnRole.PolicyProperty(
                    policy_document=aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "secretsmanager:ListSecrets"
                                ],
                                resources = ["*"]
                            ),
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "secretsmanager:GetSecretValue"
                                ],
                                resources = Token.as_list(secret_arns)
                            )
                        ]
                    ),
                    policy_name="AllowReadFromSecretsManager"
                )
            )

        if additional_iam_role_policies:
            policies.extend(additional_iam_role_policies)

        self.iam_instance_role = aws_iam.CfnRole(
            self,
            "AsgInstanceRole",
            assume_role_policy_document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[ "sts:AssumeRole" ],
                        principals=[ aws_iam.ServicePrincipal("ec2.amazonaws.com") ]
                    )
                ]
            ),
            policies=policies,
            managed_policy_arns=[
                "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
            ]
        )
        self.iam_instance_role.override_logical_id(f"{id}InstanceRole")

        # ec2
        self.sg = aws_ec2.CfnSecurityGroup(
            self,
            "AsgSg",
            group_description=f"{id} security group",
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

        self.ec2_instance_profile = aws_iam.CfnInstanceProfile(
	    self,
	    "AsgInstanceProfile",
            roles=[ self.iam_instance_role.ref ]
        )
        self.ec2_instance_profile.override_logical_id(f"{id}InstanceProfile")

        self.disk_usage_alarm_threshold_param = CfnParameter(
            self,
            "AsgDiskUsageAlarmThreshold",
            default=80,
            description="Required: The alarm threshold for disk usage percentage.",
            min_value=0,
            max_value=100,
            type="Number"
        )
        self.disk_usage_alarm_threshold_param.override_logical_id(f"{id}DiskUsageAlarmThreshold")

        # data volume
        if use_data_volume:
            # lambda to find az from subnet
            lambda_code_path = Util.local_path("lambda_subnet_to_az.py")
            with open(lambda_code_path) as f:
                lambda_code = f.read()
            self.subnet_to_az_lambda = aws_lambda.Function(
                self,
                "AsgSubnetToAzLambda",
                runtime=aws_lambda.Runtime.PYTHON_3_10,
                timeout=Duration.seconds(300),
                handler="index.handler",
                code=aws_lambda.Code.from_inline(lambda_code)
            )
            self.subnet_to_az_lambda.node.default_child.override_logical_id(f"{id}SubnetToAzLambda")
            self.subnet_to_az_lambda.role.node.default_child.override_logical_id(f"{id}SubnetToAzLambdaRole")
            self.subnet_to_az_lambda_subnet_policy = aws_iam.Policy(
                self,
                "DescribeSubnetsPolicy",
                statements=[
                    aws_iam.PolicyStatement(
                        actions=["ec2:DescribeSubnets"],
                        resources=["*"]
                    )
                ]
            )
            self.subnet_to_az_lambda_subnet_policy.node.default_child.override_logical_id(f"{id}DescribeSubnetsPolicy")
            self.subnet_to_az_lambda.role.attach_inline_policy(self.subnet_to_az_lambda_subnet_policy)
            self.subnet_to_az_custom_resource = CustomResource(
                self,
                "AsgSubnetToAzCustomResource",
                service_token=self.subnet_to_az_lambda.function_arn,
                properties={
                    "aws_region": Aws.REGION,
                    "subnet_id": vpc.public_subnet1_id() if use_public_subnets else vpc.private_subnet1_id()
                }
            )
            self.subnet_to_az_custom_resource.node.default_child.override_logical_id(f"{id}SubnetToAzCustomResource")

            self.data_volume_size_param = CfnParameter(
                self,
                "AsgDataVolumeSize",
                type="Number",
                default="100",
                description="Required: Size of EBS data volume in GiBs."
            )
            self.data_volume_size_param.override_logical_id(f"{id}DataVolumeSize")

            self.data_volume_snapshot_param = CfnParameter(
                self,
                "AsgDataVolumeSnapshot",
                default="",
                description="Optional: An EBS snapshot id to restore as a starting point for the data volume.",
            )
            self.data_volume_snapshot_param.override_logical_id(f"{id}DataVolumeSnapshot")

            self.data_volume_snapshot_condition = CfnCondition(
                self,
                "AsgDataVolumeSnapshotCondition",
                expression=Fn.condition_not(Fn.condition_equals(self.data_volume_snapshot_param.value, ""))
            )
            self.data_volume_snapshot_condition.override_logical_id(f"{id}DataVolumeSnapshotCondition")

            self.data_volume = aws_ec2.CfnVolume(
                self,
                "AsgDataVolume",
                availability_zone=Token.as_string(self.subnet_to_az_custom_resource.get_att('az')),
                encrypted=True,
                snapshot_id=Token.as_string(
                    Fn.condition_if(
                        self.data_volume_snapshot_condition.logical_id,
                        self.data_volume_snapshot_param.value_as_string,
                        Aws.NO_VALUE
                    )
                ),
                size=self.data_volume_size_param.value_as_number,
                volume_type='gp3',
                tags=[CfnTag(key='Name', value=f"{Aws.STACK_NAME}-pds")]
            )
            self.data_volume.override_logical_id(f"{id}DataVolume")
            self.data_volume.cfn_options.deletion_policy = CfnDeletionPolicy.SNAPSHOT
            self.data_volume.cfn_options.update_replace_policy = CfnDeletionPolicy.SNAPSHOT

            self.data_volume_backup_retention_period_param = CfnParameter(
                self,
                "AsgDataVolumeBackupRetentionPeriod",
                type="Number",
                min_value=1,
                max_value=35,
                default="7",
                description="Required: The number of nightly EBS snapshots to retain."
            )
            self.data_volume_backup_retention_period_param.override_logical_id(f"{id}DataVolumeBackupRetentionPeriod")

            self.data_volume_backup_vault_arn_param = CfnParameter(
                self,
                "AsgDataVolumeBackupVaultArn",
                default="",
                description="Optional: An AWS Backup Vault ARN to use for storing EBS backups. If not specified, a vault will be created."
            )
            self.data_volume_backup_vault_arn_param.override_logical_id(f"{id}DataVolumeBackupVaultArn")

            self.data_volume_backup_vault_arn_exists_condition = CfnCondition(
                self,
                "AsgDataVolumeBackupVaultArnExistsCondition",
                expression=Fn.condition_not(Fn.condition_equals(self.data_volume_backup_vault_arn_param.value, ""))
            )
            self.data_volume_backup_vault_arn_exists_condition.override_logical_id(f"{id}DataVolumeBackupVaultArnExistsCondition")
            self.data_volume_backup_vault_arn_not_exists_condition = CfnCondition(
                self,
                "AsgDataVolumeBackupVaultArnNotExistsCondition",
                expression=Fn.condition_equals(self.data_volume_backup_vault_arn_param.value, "")
            )
            self.data_volume_backup_vault_arn_not_exists_condition.override_logical_id(f"{id}DataVolumeBackupVaultArnNotExistsCondition")

            self.data_volume_backup_vault = aws_backup.CfnBackupVault(
                self,
                "AsgDataVolumeBackupVault",
                backup_vault_name=Util.append_stack_uuid('cfn-stack-id')
            )
            self.data_volume_backup_vault.cfn_options.condition = self.data_volume_backup_vault_arn_not_exists_condition
            self.data_volume_backup_vault.cfn_options.deletion_policy = CfnDeletionPolicy.RETAIN
            self.data_volume_backup_vault.cfn_options.update_replace_policy = CfnDeletionPolicy.RETAIN
            self.data_volume_backup_vault.override_logical_id(f"{id}DataVolumeBackupVault")

            self.data_volume_backup_plan = aws_backup.CfnBackupPlan(
                self,
                "AsgDataVolumeBackupPlan",
                backup_plan=aws_backup.CfnBackupPlan.BackupPlanResourceTypeProperty(
                    backup_plan_name=f"{Aws.STACK_NAME}-backup-plan",
                    backup_plan_rule=[
                        aws_backup.CfnBackupPlan.BackupRuleResourceTypeProperty(
                            rule_name=f"{Aws.STACK_NAME}-backup-rule",
                            schedule_expression=aws_events.Schedule.cron(hour="3", minute="0").expression_string,
                            target_backup_vault=self.data_volume_backup_vault_name(),
                            lifecycle=aws_backup.CfnBackupPlan.LifecycleResourceTypeProperty(
                                delete_after_days=self.data_volume_backup_retention_period_param.value_as_number
                            )
                        )
                    ]
                )
            )
            self.data_volume_backup_plan.override_logical_id(f"{id}DataVolumeBackupPlan")
                                      
            volume_arn = f"arn:aws:ec2:{Aws.REGION}:{Aws.ACCOUNT_ID}:volume/{self.data_volume.ref}"
            self.data_volume_backup_selection = aws_backup.CfnBackupSelection(
                self,
                "AsgDataVolumeBackupSelection",
                backup_plan_id=self.data_volume_backup_plan.ref,
                backup_selection=aws_backup.CfnBackupSelection.BackupSelectionResourceTypeProperty(
                    iam_role_arn=f"arn:aws:iam::{Aws.ACCOUNT_ID}:role/service-role/AWSBackupDefaultServiceRole",
                    selection_name=f"{Aws.STACK_NAME}-backup-selection",
                    resources=[volume_arn]
                )
            )
            self.data_volume_backup_selection.override_logical_id(f"{id}DataVolumeBackupSelection")

        user_data = None
        if use_data_volume:
            script_code_path = Util.local_path("script_attach_ebs.sh")
            with open(script_code_path) as f:
                script_code = f.read()
            if user_data_contents is None:
                user_data_contents = script_code
            else:
                user_data_contents = script_code + user_data_contents
            user_data_variables['EbsId'] = self.data_volume.ref
            user_data_variables['AsgId'] = id

        reprovision_snippet = "# reprovision string: ${AsgReprovisionString}"
        user_data_variables['IamRole'] = self.iam_instance_role.ref
        if user_data_contents is None:
            user_data_contents = reprovision_snippet
        else:
            user_data_contents = user_data_contents + "\n" + reprovision_snippet
        user_data = (
            Fn.base64(
                Fn.sub(
                    user_data_contents,
                    user_data_variables
                )
            )
        )

        block_device_mappings = None
        if root_volume_size > 0:
            block_device_mappings = [
                aws_ec2.CfnLaunchTemplate.BlockDeviceMappingProperty(
                    device_name=root_volume_device_name,
                    ebs=aws_ec2.CfnLaunchTemplate.EbsProperty(
                        encrypted=True,
                        volume_size=root_volume_size,
                        volume_type="gp3"
                    )
                )
            ]

        self.ec2_launch_template = aws_ec2.CfnLaunchTemplate(
            self,
            f"{id}LaunchTemplate",
            launch_template_data=aws_ec2.CfnLaunchTemplate.LaunchTemplateDataProperty(
                block_device_mappings=block_device_mappings,
                image_id=self.ami_id_param.value_as_string,
                instance_type=self.instance_type_param.value_as_string,
                iam_instance_profile=aws_ec2.CfnLaunchTemplate.IamInstanceProfileProperty(
                    name=self.ec2_instance_profile.ref
                ),
                key_name=Token.as_string(
                    Fn.condition_if(
                        self.key_name_condition.logical_id,
                        self.key_name_param.value_as_string,
                        Aws.NO_VALUE
                    )
                ),
                metadata_options=aws_ec2.CfnLaunchTemplate.MetadataOptionsProperty(
                    http_tokens="required",
                ),
                security_group_ids=[ self.sg.attr_group_id ],
                user_data=user_data
            )
        )
        self.ec2_launch_template.override_logical_id(f"{id}LaunchTemplate")

        if singleton:
            subnets = [vpc.public_subnet1_id()] if use_public_subnets else [vpc.private_subnet1_id()]
        else:
            subnets = vpc.public_subnet_ids() if use_public_subnets else vpc.private_subnet_ids()

        # autoscaling
        self.asg = aws_autoscaling.CfnAutoScalingGroup(
            self,
            "Asg",
            launch_template=aws_autoscaling.CfnAutoScalingGroup.LaunchTemplateSpecificationProperty(
                version=self.ec2_launch_template.attr_latest_version_number,
                launch_template_id=self.ec2_launch_template.ref
            ),
            desired_capacity="1" if singleton else Token.as_string(self.desired_capacity_param.value),
            health_check_type=health_check_type,
            max_size="1" if singleton else Token.as_string(self.max_size_param.value),
            min_size="1" if singleton else Token.as_string(self.min_size_param.value),
            vpc_zone_identifier=subnets
        )
        self.asg.override_logical_id(id)
        self.asg.cfn_options.creation_policy=CfnCreationPolicy(
            resource_signal=CfnResourceSignal(
                count=1,
                timeout=f"PT{create_and_update_timeout_minutes}M"
            )
        )
        if singleton:
            self.asg.cfn_options.update_policy=CfnUpdatePolicy(
                auto_scaling_rolling_update=CfnAutoScalingRollingUpdate(
                    max_batch_size=1,
                    min_instances_in_service=0,
                    pause_time=f"PT{create_and_update_timeout_minutes}M",
                    wait_on_resource_signals=True
                )
            )
        else:
            if deployment_rolling_update:
                self.asg.cfn_options.update_policy=CfnUpdatePolicy(
                    auto_scaling_rolling_update=CfnAutoScalingRollingUpdate(
                        min_instances_in_service=Token.as_number(self.min_size_param.value),
                        pause_time="PT15M",
                        wait_on_resource_signals=True
                    ),
                    auto_scaling_scheduled_action=CfnAutoScalingScheduledAction(
                        ignore_unmodified_group_size_properties=True
                    )
                )
            else:
                self.asg.cfn_options.update_policy=CfnUpdatePolicy(
                    auto_scaling_replacing_update=CfnAutoScalingReplacingUpdate(
                        will_replace=True
                    )
                )
        Tags.of(self.asg).add("Name", "{}/Asg".format(Aws.STACK_NAME))

        if notification_topic_arn:
            actions=[notification_topic_arn]
        else:
            actions=None
        self.root_disk_alarm = aws_cloudwatch.CfnAlarm(
            self,
            "AsgRootDiskAlarm",
            namespace="CWAgent",
            metric_name="disk_used_percent",
            dimensions=[
                {"name": "AutoScalingGroupName", "value": self.asg.ref },
                {"name": "fstype", "value": "ext4"},
                {"name": "path", "value": "/"}
            ],
            statistic="Average",
            period=300,
            evaluation_periods=1,
            threshold=self.disk_usage_alarm_threshold_param.value_as_number,
            alarm_actions=actions,
            ok_actions=actions,
            comparison_operator="GreaterThanThreshold"
        )
        self.root_disk_alarm.override_logical_id(f"{id}RootDiskAlarm")

        if use_data_volume:
            self.data_disk_alarm = aws_cloudwatch.CfnAlarm(
                self,
                "AsgDataDiskAlarm",
                namespace="CWAgent",
                metric_name="disk_used_percent",
                dimensions=[
                    {"name": "AutoScalingGroupName", "value": self.asg.ref },
                    {"name": "fstype", "value": "xfs"},
                    {"name": "path", "value": "/data"}
                ],
                statistic="Average",
                period=300,
                evaluation_periods=1,
                threshold=self.disk_usage_alarm_threshold_param.value_as_number,
                alarm_actions=actions,
                ok_actions=actions,
                comparison_operator="GreaterThanThreshold"
            )
            self.data_disk_alarm.override_logical_id(f"{id}DataDiskAlarm")

            #
            # OUTPUTS
            #

            self.data_volume_backup_vault_arn_output = CfnOutput(
                self,
                "AsgDataVolumeBackupVaultArnOutput",
                description="The data volume AWS Backup Vault ARN",
                value=self.data_volume_backup_vault_arn()
            )
            self.data_volume_backup_vault_arn_output.override_logical_id(f"{id}DataVolumeBackupVaultArnOutput")

    def data_volume_backup_vault_arn(self):
        if self._use_data_volume:
            return Token.as_string(
                Fn.condition_if(
                    self.data_volume_backup_vault_arn_exists_condition.logical_id,
                    self.data_volume_backup_vault_arn_param.value_as_string,
                    self.data_volume_backup_vault.ref
                )
            )
        else:
            return None

    def data_volume_backup_vault_name(self):
        if self._use_data_volume:
            return Token.as_string(
                Fn.condition_if(
                    self.data_volume_backup_vault_arn_exists_condition.logical_id,
                    Fn.select(
                        6,
                        Fn.split(":", self.data_volume_backup_vault_arn_param.value_as_string)
                    ),
                    self.data_volume_backup_vault.ref
                )
            )
        else:
            return None

    def metadata_parameter_group(self):
        params = [
            self.ami_id_param.logical_id,
            self.instance_type_param.logical_id,
            self.key_name_param.logical_id,
            self.reprovision_string_param.logical_id,
            self.disk_usage_alarm_threshold_param.logical_id
        ]
        if not self._singleton:
            params += [
                self.desired_capacity_param.logical_id,
                self.max_size_param.logical_id,
                self.min_size_param.logical_id
            ]
        if self._use_data_volume:
            params += [
                self.data_volume_size_param.logical_id,
                self.data_volume_snapshot_param.logical_id,
                self.data_volume_backup_retention_period_param.logical_id,
                self.data_volume_backup_vault_arn_param.logical_id
            ]
        return [
            {
                "Label": {
                    "default": "Auto Scaling Group Configuration"
                },
                "Parameters": params
            }
        ]

    def metadata_parameter_labels(self):
        params = {
            self.ami_id_param.logical_id: {
                "default": "AWS Marketplace AMI"
            },
            self.instance_type_param.logical_id: {
                "default": "EC2 instance type"
            },
            self.key_name_param.logical_id: {
                "default": "EC2 Key Pair Name"
            },
            self.reprovision_string_param.logical_id: {
                "default": "Auto Scaling Group Reprovision String"
            },
            self.disk_usage_alarm_threshold_param.logical_id: {
                "default": "Percent Disk Used Alarm Threshold"
            }
        }
        if not self._singleton:
            params = {
                **params,
                self.desired_capacity_param.logical_id: {
                    "default": "Auto Scaling Group Desired Capacity"
                },
                self.max_size_param.logical_id: {
                    "default": "Auto Scaling Group Maximum Size"
                },
                self.min_size_param.logical_id: {
                    "default": "Auto Scaling Group Minimum Size"
                }
            }
        if self._use_data_volume:
            params = {
                **params,
                self.data_volume_size_param.logical_id: {
                    "default": "Auto Scaling Group EBS Snapshot Size"
                },
                self.data_volume_snapshot_param.logical_id: {
                    "default": "Auto Scaling Group EBS Snapshot ID"
                },
                self.data_volume_backup_vault_arn_param.logical_id: {
                    "default": "Auto Scaling Group EBS Backup Vault ARN"
                },
                self.data_volume_backup_retention_period_param.logical_id: {
                    "default": "Auto Scaling Group EBS Backup Retention in Days"
                }
            }
        return params
