from aws_cdk import (
    aws_autoscaling,
    aws_ec2,
    aws_iam,
    core
)

from oe_patterns_cdk_common.vpc import Vpc

class Asg(core.Construct):

    def __init__(
            self,
            scope: core.Construct,
            id: str,
            vpc: Vpc,
            allowed_instance_types: 'list[string]' = [],
            default_instance_type: str = 'm5.xlarge',
            allow_associate_address: bool = False,
            log_group_arns: 'list[string]' = [],
            user_data_contents: str = None,
            user_data_variables: dict = None,
            **props):
        super().__init__(scope, id, **props)

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
            "c5d.12xlarge",
            "c5d.18xlarge",
            "c5d.2xlarge",
            "c5d.4xlarge",
            "c5d.9xlarge",
            "c5d.large",
            "c5d.xlarge",
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

        self.instance_type_param = core.CfnParameter(
            self,
            "AsgInstanceType",
            allowed_values=allowed_instance_types if allowed_instance_types else default_allowed_instance_types,
            default=default_instance_type,
            description="Required: The EC2 instance type for the application Auto Scaling Group."
        )
        self.instance_type_param.override_logical_id(f"{id}InstanceType")

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
        if log_group_arns:
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
                                resources=log_group_arns
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
            vpc_id=vpc.id()
        )
        self.sg.override_logical_id(f"{id}Sg")

        self.ec2_instance_profile = aws_iam.CfnInstanceProfile(
	    self,
	    "AsgInstanceProfile",
            roles=[ self.iam_instance_role.ref ]
        )
        self.ec2_instance_profile.override_logical_id(f"{id}InstanceProfile")

        user_data = None
        if user_data_contents is not None:
            user_data = (
                core.Fn.base64(
                    core.Fn.sub(
                        user_data_contents,
                        user_data_variables
                    )
                )
            )
        self.ec2_launch_config = aws_autoscaling.CfnLaunchConfiguration(
            self,
            f"{id}LaunchConfig",
            image_id=core.Fn.find_in_map("AWSAMIRegionMap", core.Aws.REGION, "AMI"),
            instance_type=self.instance_type_param.value_as_string,
            iam_instance_profile=self.ec2_instance_profile.ref,
            security_groups=[ self.sg.ref ],
            user_data=user_data
        )
        self.ec2_launch_config.override_logical_id(f"{id}LaunchConfig")

        # autoscaling
        self.asg = aws_autoscaling.CfnAutoScalingGroup(
            self,
            "Asg",
            launch_configuration_name=self.ec2_launch_config.ref,
            desired_capacity="1",
            max_size="1",
            min_size="1",
            vpc_zone_identifier=vpc.public_subnet_ids()
        )
        self.asg.override_logical_id(f"{id}Asg")
        self.asg.cfn_options.creation_policy=core.CfnCreationPolicy(
            resource_signal=core.CfnResourceSignal(
                count=1,
                timeout="PT15M"
            )
        )
        self.asg.cfn_options.update_policy=core.CfnUpdatePolicy(
            auto_scaling_rolling_update=core.CfnAutoScalingRollingUpdate(
                max_batch_size=1,
                min_instances_in_service=0,
                pause_time="PT15M",
                wait_on_resource_signals=True
            )
        )
        core.Tags.of(self.asg).add("Name", "{}/Asg".format(core.Aws.STACK_NAME))

    def metadata_parameter_group(self):
        return [
            {
                "Label": {
                    "default": "ASG Configuration"
                },
                "Parameters": [
                    self.instance_type_param.logical_id
                ]
            }
        ]

    def metadata_parameter_labels(self):
        return {
            self.instance_type_param.logical_id: {
                "default": "EC2 instance type"
            }
        }
