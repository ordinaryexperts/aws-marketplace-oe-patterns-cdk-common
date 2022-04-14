from aws_cdk import (
    aws_autoscaling,
    aws_ec2,
    aws_iam,
    core
)

from oe_patterns_cdk_common.vpc import Vpc

class Asg(core.Construct):

    def __init__(self, scope: core.Construct, id: str, vpc: Vpc, user_data_file_path: str = None, user_data_variables: dict = None, **props):
        super().__init__(scope, id, **props)

        self.instance_type_param = core.CfnParameter(
            self,
            "AsgInstanceType",
            default="m5.xlarge",
            description="Required: The EC2 instance type for the application Auto Scaling Group."
        )
        self.instance_type_param.override_logical_id(f"{id}InstanceType")

        # iam
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
            policies=[
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
                                resources=["*"]
                            )
                        ]
                    ),
                    policy_name="AllowStreamLogsToCloudWatch"
                ),
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
                                actions=[
                                    "ec2:AssociateAddress",
                                ],
                                resources=[ "*" ]
                            )
                        ]
                    ),
                    policy_name="AllowAssociateAddress"
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
                ),
            ],
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

        launch_config_user_data = None
        user_data = None
        if user_data_file_path is not None:
            with open(user_data_file_path) as f:
                launch_config_user_data = f.read()
            if user_data_variables is None:
                user_data_variables = {}
            user_data = (
                core.Fn.base64(
                    core.Fn.sub(
                        launch_config_user_data,
                        **user_data_variables
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
        self.asg.override_logical_id(id)
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
