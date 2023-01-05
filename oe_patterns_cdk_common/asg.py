import os

from aws_cdk import (
    Aws,
    aws_autoscaling,
    aws_ec2,
    aws_iam,
    aws_lambda,
    aws_logs,
    CfnAutoScalingReplacingUpdate,
    CfnAutoScalingRollingUpdate,
    CfnAutoScalingScheduledAction,
    CfnCondition,
    CfnCreationPolicy,
    CfnDeletionPolicy,
    CfnParameter,
    CfnResourceSignal,
    CfnUpdatePolicy,
    CustomResource,
    Fn,
    Tags,
    Token
)

from constructs import Construct
from oe_patterns_cdk_common.vpc import Vpc

class Asg(Construct):

    TWO_YEARS_IN_DAYS=731

    def __init__(
            self,
            scope: Construct,
            id: str,
            vpc: Vpc,
            additional_iam_role_policies: 'list[object]' = [],
            allow_associate_address: bool = False,
            allowed_instance_types: 'list[str]' = [],
            data_volume_size: int = 0,
            default_instance_type: str = 'm5.xlarge',
            deployment_rolling_update: bool = False,
            health_check_type: str = 'EC2',
            pipeline_bucket_arn: str = None,
            root_volume_device_name: str = "/dev/sda1",
            root_volume_size: int = 0,
            secret_arns: 'list[str]' = [],
            singleton: bool = False,
            use_public_subnets: bool = False,
            user_data_contents: str = None,
            user_data_variables: dict = None,
            **props):
        super().__init__(scope, id, **props)
        self._singleton = singleton

        default_allowed_instance_types = [
            "c5.large",
            "c5.xlarge",
            "c5.2xlarge",
            "c5.4xlarge",
            "c5.9xlarge",
            "c5.12xlarge",
            "c5.18xlarge",
            "c5.24xlarge",
            "c5.metal",
            "c5d.large",
            "c5d.xlarge",
            "c5d.2xlarge",
            "c5d.4xlarge",
            "c5d.9xlarge",
            "c5d.12xlarge",
            "c5d.18xlarge",
            "c5d.24xlarge",
            "m5.large",
            "m5.xlarge",
            "m5.2xlarge",
            "m5.4xlarge",
            "m5.8xlarge",
            "m5.12xlarge",
            "m5.16xlarge",
            "m5.24xlarge",
            "m5.metal",
            "m5d.large",
            "m5d.xlarge",
            "m5d.2xlarge",
            "m5d.4xlarge",
            "m5d.8xlarge",
            "m5d.12xlarge",
            "m5d.16xlarge",
            "m5d.24xlarge",
            "m5d.metal",
            "r5.large",
            "r5.xlarge",
            "r5.2xlarge",
            "r5.4xlarge",
            "r5.8xlarge",
            "r5.12xlarge",
            "r5.16xlarge",
            "r5.24xlarge",
            "r5.metal",
            "r5d.large",
            "r5d.xlarge",
            "r5d.2xlarge",
            "r5d.4xlarge",
            "r5d.8xlarge",
            "r5d.12xlarge",
            "r5d.16xlarge",
            "r5d.24xlarge",
            "r5d.metal",
            "t3.nano",
            "t3.micro",
            "t3.small",
            "t3.medium",
            "t3.large",
            "t3.xlarge",
            "t3.2xlarge"
        ]

        self.instance_type_param = CfnParameter(
            self,
            "AsgInstanceType",
            allowed_values=allowed_instance_types if allowed_instance_types else default_allowed_instance_types,
            default=default_instance_type,
            description="Required: The EC2 instance type for the application Auto Scaling Group."
        )
        self.instance_type_param.override_logical_id(f"{id}InstanceType")
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
        if data_volume_size > 0:
            policies.append(
                aws_iam.CfnRole.PolicyProperty(
                    policy_document=aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "ec2:AttachVolume"
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

        # data volume
        if data_volume_size > 0:
            # lambda to find az from subnet
            lambda_code_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "lambda_subnet_to_az.py"
            )
            with open(lambda_code_path) as f:
                lambda_code = f.read()
            self.subnet_to_az_lambda = aws_lambda.Function(
                self,
                "AsgSubnetToAzLambda",
                runtime=aws_lambda.Runtime.PYTHON_3_8,
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

            self.data_volume_snapshot_param = CfnParameter(
                self,
                "AsgDataVolumeSnapshot",
                default="",
                description="Optional: An EBS snapshot to restore as a starting point for the data volume.",
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
                snapshot_id=Token.as_string(
                    Fn.condition_if(
                        self.data_volume_snapshot_condition.logical_id,
                        self.data_volume_snapshot_param.value_as_string,
                        Aws.NO_VALUE
                    )
                ),
                encrypted=True,
                size=data_volume_size
            )
            self.data_volume.override_logical_id(f"{id}DataVolume")

        user_data = None
        if data_volume_size > 0:
            script_code_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "script_attach_ebs.sh"
            )
            with open(script_code_path) as f:
                script_code = f.read()
            if user_data_contents is None:
                user_data_contents = script_code
            else:
                user_data_contents = script_code + user_data_contents
            user_data_variables['EbsId'] = self.data_volume.ref
            user_data_variables['AsgId'] = id

        reprovision_snippet = "# reprovision string: ${AsgReprovisionString}"
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
                image_id=Fn.find_in_map("AWSAMIRegionMap", Aws.REGION, "AMI"),
                instance_type=self.instance_type_param.value_as_string,
                iam_instance_profile=aws_ec2.CfnLaunchTemplate.IamInstanceProfileProperty(
                    name=self.ec2_instance_profile.ref
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
                timeout="PT15M"
            )
        )
        if singleton:
            self.asg.cfn_options.update_policy=CfnUpdatePolicy(
                auto_scaling_rolling_update=CfnAutoScalingRollingUpdate(
                    max_batch_size=1,
                    min_instances_in_service=0,
                    pause_time="PT15M",
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

    def metadata_parameter_group(self):
        params = [
            self.instance_type_param.logical_id,
            self.reprovision_string_param.logical_id
        ]
        if not self._singleton:
            params += [
                self.desired_capacity_param.logical_id,
                self.max_size_param.logical_id,
                self.min_size_param.logical_id
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
            self.instance_type_param.logical_id: {
                "default": "EC2 instance type"
            },
            self.reprovision_string_param.logical_id: {
                "default": "Auto Scaling Group Reprovision String"
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
        return params
