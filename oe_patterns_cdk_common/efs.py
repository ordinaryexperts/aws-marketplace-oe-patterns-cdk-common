from aws_cdk import (
    aws_autoscaling,
    aws_ec2,
    aws_efs,
    aws_iam,
    Aws,
    CfnCondition,
    CfnParameter,
    Fn,
    Tags
)

from constructs import Construct
from oe_patterns_cdk_common.vpc import Vpc

class Efs(Construct):

    def __init__(
            self,
            scope: Construct,
            id: str,
            vpc: Vpc,
            app_sg: aws_ec2.CfnSecurityGroup,
            **props):
        super().__init__(scope, id, **props)

        self.efs_automatic_backups_enabled_param = CfnParameter(
            self,
            "EfsAutomaticBackupsStatus",
            allowed_values=[ "ENABLED", "DISABLED" ],
            default="ENABLED",
            description="Optional: status of automatic backups of EFS"
        )
        self.efs_automatic_backups_enabled_param.override_logical_id(f"{id}AutomaticBackupsStatus")
        self.efs_transition_to_ia_param = CfnParameter(
            self,
            "EfsTransitionToIa",
            allowed_values=[ "", "AFTER_7_DAYS", "AFTER_14_DAYS", "AFTER_30_DAYS", "AFTER_60_DAYS", "AFTER_90_DAYS" ],
            default="",
            description="Describes the period of time that a file is not accessed, after which it transitions to IA storage. Metadata operations such as listing the contents of a directory don't count as file access events."
        )
        self.efs_transition_to_ia_param.override_logical_id(f"{id}TransitionToIa")
        self.efs_transition_to_primary_storage_class_param = CfnParameter(
            self,
            "EfsTransitionToPrimaryStorageClass",
            allowed_values=[ "", "AFTER_1_ACCESS" ],
            default="",
            description="Describes when to transition a file from IA storage to primary storage. Metadata operations such as listing the contents of a directory don't count as file access events."
        )
        self.efs_transition_to_primary_storage_class_param.override_logical_id(f"{id}TransitionToPrimaryStorageClass")
        self.efs_transition_to_ia_enabled_condition = CfnCondition(
            self,
            "TransitionToIaEnabledCondition",
            expression=Fn.condition_not(Fn.condition_equals(self.efs_transition_to_ia_param.value, ""))
        )
        self.efs_transition_to_ia_enabled_condition.override_logical_id(f"{id}TransitionToIaEnabledCondition")
        self.efs_transition_to_primary_storage_class_enabled_condition = CfnCondition(
            self,
            "TransitionToPrimaryStorageClassEnabledCondition",
            expression=Fn.condition_not(Fn.condition_equals(self.efs_transition_to_primary_storage_class_param.value, ""))
        )
        self.efs_transition_to_primary_storage_class_enabled_condition.override_logical_id(f"{id}TransitionToPrimaryStorageClassEnabledCondition")
        # efs
        self.efs_sg = aws_ec2.CfnSecurityGroup(
            self,
            "EfsSg",
            group_description="{}/Efs".format(Aws.STACK_NAME),
            vpc_id=vpc.id()
        )
        self.efs_sg.override_logical_id(f"{id}Sg")
        self.efs_sg_ingress = aws_ec2.CfnSecurityGroupIngress(
            self,
            "EfsSgIngress",
            description="Allow EFS traffic from AppSg to EfsSg",
            from_port=2049,
            group_id=self.efs_sg.ref,
            ip_protocol="tcp",
            source_security_group_id=app_sg.ref,
            to_port=2049
        )
        self.efs_sg.override_logical_id(f"{id}SgIngress")
        self.efs = aws_efs.CfnFileSystem(
            self,
            "AppEfs",
            encrypted=True,
            backup_policy=aws_efs.CfnFileSystem.BackupPolicyProperty(
                status=self.efs_automatic_backups_enabled_param.value_as_string
            ),
            lifecycle_policies=[
                Fn.condition_if(
                    self.efs_transition_to_ia_enabled_condition.logical_id,
                    aws_efs.CfnFileSystem.LifecyclePolicyProperty(
                        transition_to_ia=self.efs_transition_to_ia_param.value_as_string
                    ),
                    Aws.NO_VALUE
                ),
                Fn.condition_if(
                    self.efs_transition_to_primary_storage_class_enabled_condition.logical_id,
                    aws_efs.CfnFileSystem.LifecyclePolicyProperty(
                        transition_to_primary_storage_class=self.efs_transition_to_primary_storage_class_param.value_as_string
                    ),
                    Aws.NO_VALUE
                )
            ]
        )
        self.efs.override_logical_id(f"App{id}")
        # taskcat lint fails on valid LifecyclePolicy configurations
        self.efs.cfn_options.metadata = {
            "cfn-lint": {
                "config": {
                    "ignore_checks": ['E3002']
                }
            }
        }
        Tags.of(self.efs).add("Name", "{}/Efs".format(Aws.STACK_NAME))
        self.efs_mount_target1 = aws_efs.CfnMountTarget(
            self,
            "AppEfsMountTarget1",
            file_system_id=self.efs.ref,
            security_groups=[ self.efs_sg.ref ],
            subnet_id=vpc.private_subnet1_id()
        )
        self.efs_mount_target1.override_logical_id(f"App{id}MountTarget1")
        self.efs_mount_target2 = aws_efs.CfnMountTarget(
            self,
            "AppEfsMountTarget2",
            file_system_id=self.efs.ref,
            security_groups=[ self.efs_sg.ref ],
            subnet_id=vpc.private_subnet2_id()
        )
        self.efs_mount_target2.override_logical_id(f"App{id}MountTarget2")
                    # {
                    #     "Label": {
                    #         "default": "EFS Configuration"
                    #     },
                    #     "Parameters": [
                    #         self.efs_automatic_backups_enabled_param.logical_id,
                    #         efs_transition_to_ia_param.logical_id,
                    #         efs_transition_to_primary_storage_class_param.logical_id
                    #     ]
                    # },


    def metadata_parameter_group(self):
        return [
            {
                "Label": {
                    "default": "EFS Configuration"
                },
                "Parameters": [
                    self.efs_automatic_backups_enabled_param.logical_id,
                    self.efs_transition_to_ia_param.logical_id,
                    self.efs_transition_to_primary_storage_class_param.logical_id
                ],
            }
        ]

    def metadata_parameter_labels(self):
        return {
            self.efs_automatic_backups_enabled_param.logical_id: {
                "default": "EFS Automatic Backups Enabled"
            },
            self.efs_transition_to_ia_param.logical_id: {
                "default": "EFS Transition to IA"
            },
            self.efs_transition_to_primary_storage_class_param: {
                "default": "EFS Transition to Primary Storage Class"
            }
        }

