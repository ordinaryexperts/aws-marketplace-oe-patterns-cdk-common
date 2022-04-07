from aws_cdk import (
    aws_autoscaling,
    aws_ec2,
    aws_efs,
    aws_iam,
    core
)

from oe_patterns_cdk_common.vpc import Vpc

class Efs(core.Construct):

    def __init__(
            self,
            scope: core.Construct,
            id: str,
            vpc: Vpc,
            app_sg: aws_ec2.CfnSecurityGroup,
            **props):
        super().__init__(scope, id, **props)

        efs_automatic_backups_enabled_param = core.CfnParameter(
            self,
            "EfsAutomaticBackupsStatus",
            allowed_values=[ "ENABLED", "DISABLED" ],
            default="ENABLED",
            description="Optional: status of automatic backups of EFS"
        )
        efs_transition_to_ia_param = core.CfnParameter(
            self,
            "EfsTransitionToIa",
            allowed_values=[ "", "AFTER_7_DAYS", "AFTER_14_DAYS", "AFTER_30_DAYS", "AFTER_60_DAYS", "AFTER_90_DAYS" ],
            default="",
            description="Describes the period of time that a file is not accessed, after which it transitions to IA storage. Metadata operations such as listing the contents of a directory don't count as file access events."
        )
        efs_transition_to_primary_storage_class_param = core.CfnParameter(
            self,
            "EfsTransitionToPrimaryStorageClass",
            allowed_values=[ "", "AFTER_1_ACCESS" ],
            default="",
            description="Describes when to transition a file from IA storage to primary storage. Metadata operations such as listing the contents of a directory don't count as file access events."
        )
        efs_transition_to_ia_enabled_condition = core.CfnCondition(
            self,
            "TransitionToIaEnabledCondition",
            expression=core.Fn.condition_not(core.Fn.condition_equals(efs_transition_to_ia_param.value, ""))
        )
        efs_transition_to_primary_storage_class_enabled_condition = core.CfnCondition(
            self,
            "TransitionToPrimaryStorageClassEnabledCondition",
            expression=core.Fn.condition_not(core.Fn.condition_equals(efs_transition_to_primary_storage_class_param.value, ""))
        )
        # efs
        efs_sg = aws_ec2.CfnSecurityGroup(
            self,
            "EfsSg",
            group_description="{}/Efs".format(core.Aws.STACK_NAME),
            vpc_id=vpc.id()
        )
        efs_sg_ingress = aws_ec2.CfnSecurityGroupIngress(
            self,
            "EfsSgIngress",
            description="Allow EFS traffic from AppSg to EfsSg",
            from_port=2049,
            group_id=efs_sg.ref,
            ip_protocol="tcp",
            source_security_group_id=app_sg.ref,
            to_port=2049
        )
        efs = aws_efs.CfnFileSystem(
            self,
            "AppEfs",
            encrypted=True,
            backup_policy=aws_efs.CfnFileSystem.BackupPolicyProperty(
                status=efs_automatic_backups_enabled_param.value_as_string
            ),
            lifecycle_policies=[
                core.Fn.condition_if(
                    efs_transition_to_ia_enabled_condition.logical_id,
                    aws_efs.CfnFileSystem.LifecyclePolicyProperty(
                        transition_to_ia=efs_transition_to_ia_param.value_as_string
                    ),
                    core.Aws.NO_VALUE
                ),
                core.Fn.condition_if(
                    efs_transition_to_primary_storage_class_enabled_condition.logical_id,
                    aws_efs.CfnFileSystem.LifecyclePolicyProperty(
                        transition_to_primary_storage_class=efs_transition_to_primary_storage_class_param.value_as_string
                    ),
                    core.Aws.NO_VALUE
                )
            ]
        )
        # taskcat lint fails on valid LifecyclePolicy configurations
        efs.cfn_options.metadata = {
            "cfn-lint": {
                "config": {
                    "ignore_checks": ['E3002']
                }
            }
        }
        core.Tags.of(efs).add("Name", "{}/Efs".format(core.Aws.STACK_NAME))
        efs_mount_target1 = aws_efs.CfnMountTarget(
            self,
            "AppEfsMountTarget1",
            file_system_id=efs.ref,
            security_groups=[ efs_sg.ref ],
            subnet_id=vpc.private_subnet1_id()
        )
        efs_mount_target2 = aws_efs.CfnMountTarget(
            self,
            "AppEfsMountTarget2",
            file_system_id=efs.ref,
            security_groups=[ efs_sg.ref ],
            subnet_id=vpc.private_subnet2_id()
        )
                    # {
                    #     "Label": {
                    #         "default": "EFS Configuration"
                    #     },
                    #     "Parameters": [
                    #         efs_automatic_backups_enabled_param.logical_id,
                    #         efs_transition_to_ia_param.logical_id,
                    #         efs_transition_to_primary_storage_class_param.logical_id
                    #     ]
                    # },


