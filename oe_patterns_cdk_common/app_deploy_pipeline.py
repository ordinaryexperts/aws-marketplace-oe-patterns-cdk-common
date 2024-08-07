from aws_cdk import (
    Aws,
    aws_cloudformation,
    aws_codebuild,
    aws_codedeploy,
    aws_codepipeline,
    aws_iam,
    aws_lambda,
    aws_s3,
    Arn,
    ArnComponents,
    CfnCondition,
    CfnDeletionPolicy,
    CfnOutput,
    CfnParameter,
    Fn,
    Token
)

from constructs import Construct
from oe_patterns_cdk_common.asg import Asg
from oe_patterns_cdk_common.util import Util

class AppDeployPipeline(Construct):

    def __init__(
            self,
            scope: Construct,
            id: str,
            # TODO add list[str]type hints after upgrade of devenv to python 3.10 or higher
            after_build_commands = None,  # list[str]
            after_deploy_commands = None, # list[str]
            asg: Asg = None,
            demo_source_url: str = None,
            notification_topic_arn: str = None,
            **props):
        super().__init__(scope, id)

        self.initialize_demo_param = CfnParameter(
            self,
            "InitializeDemo",
            allowed_values=[ "true", "false" ],
            default="true",
            description="Optional: Trigger the first deployment with a copy of a demo sample codebase from Ordinary Experts."
        )
        self.initialize_demo_param.override_logical_id(f"{id}InitializeDemoParam")
        self.pipeline_artifact_bucket_name_param = CfnParameter(
            self,
            "PipelineArtifactBucketName",
            default="",
            description="Optional: Specify a bucket name for the CodePipeline pipeline to use. The bucket must be in this same AWS account. This can be handy when re-creating this template many times."
        )
        self.pipeline_artifact_bucket_name_param.override_logical_id(f"{id}PipelineArtifactBucketNameParam")
        self.source_artifact_bucket_name_param = CfnParameter(
            self,
            "SourceArtifactBucketName",
            default="",
            description="Optional: Specify a S3 bucket name which will contain the build artifacts for the application. If not specified, a bucket will be created."
        )
        self.source_artifact_bucket_name_param.override_logical_id(f"{id}SourceArtifactBucketNameParam")
        self.source_artifact_object_key_param = CfnParameter(
            self,
            "SourceArtifactObjectKey",
            default="artifact.zip",
            description="Required: AWS S3 object key (path) for the build artifact for the application. Updates to this object will trigger a deployment."
        )
        self.source_artifact_object_key_param.override_logical_id(f"{id}SourceArtifactObjectKeyParam")
        #
        # CONDITIONS
        #
        self.initialize_demo_condition = CfnCondition(
            self,
            "InitializeDemoCondition",
            expression=Fn.condition_equals(self.initialize_demo_param.value, "true")
        )
        self.initialize_demo_condition.override_logical_id(f"{id}InitializeDemoCondition")
        self.pipeline_artifact_bucket_name_not_exists_condition = CfnCondition(
            self,
            "PipelineArtifactBucketNameNotExists",
            expression=Fn.condition_equals(self.pipeline_artifact_bucket_name_param.value, "")
        )
        self.pipeline_artifact_bucket_name_not_exists_condition.override_logical_id(f"{id}PipelineArtifactBucketNameNotExists")
        self.pipeline_artifact_bucket_name_exists_condition = CfnCondition(
            self,
            "PipelineArtifactBucketNameExists",
            expression=Fn.condition_not(Fn.condition_equals(self.pipeline_artifact_bucket_name_param.value, ""))
        )
        self.pipeline_artifact_bucket_name_exists_condition.override_logical_id(f"{id}PipelineArtifactBucketNameExists")
        self.source_artifact_bucket_name_exists_condition = CfnCondition(
            self,
            "SourceArtifactBucketNameExists",
            expression=Fn.condition_not(Fn.condition_equals(self.source_artifact_bucket_name_param.value, ""))
        )
        self.source_artifact_bucket_name_exists_condition.override_logical_id(f"{id}SourceArtifactBucketNameExists")
        self.source_artifact_bucket_name_not_exists_condition = CfnCondition(
            self,
            "SourceArtifactBucketNameNotExists",
            expression=Fn.condition_equals(self.source_artifact_bucket_name_param.value, "")
        )
        self.source_artifact_bucket_name_not_exists_condition.override_logical_id(f"{id}SourceArtifactBucketNameNotExists")
        pipeline_artifact_bucket = aws_s3.CfnBucket(
            self,
            "PipelineArtifactBucket",
            access_control="Private",
            bucket_encryption=aws_s3.CfnBucket.BucketEncryptionProperty(
                server_side_encryption_configuration=[
                    aws_s3.CfnBucket.ServerSideEncryptionRuleProperty(
                        server_side_encryption_by_default=aws_s3.CfnBucket.ServerSideEncryptionByDefaultProperty(
                            sse_algorithm="AES256"
                        )
                    )
                ]
            ),
            public_access_block_configuration=aws_s3.BlockPublicAccess.BLOCK_ALL
        )
        pipeline_artifact_bucket.override_logical_id(f"{id}PipelineArtifactBucket")
        pipeline_artifact_bucket.cfn_options.condition=self.pipeline_artifact_bucket_name_not_exists_condition
        pipeline_artifact_bucket.cfn_options.deletion_policy = CfnDeletionPolicy.RETAIN
        pipeline_artifact_bucket.cfn_options.update_replace_policy = CfnDeletionPolicy.RETAIN
        self.pipeline_artifact_bucket_arn = Arn.format(
            components=ArnComponents(
                account="",
                partition=Aws.PARTITION,
                region="",
                resource=Token.as_string(
                    Fn.condition_if(
                        self.pipeline_artifact_bucket_name_exists_condition.logical_id,
                        self.pipeline_artifact_bucket_name_param.value_as_string,
                        pipeline_artifact_bucket.ref
                    )
                ),
                resource_name="*",
                service="s3"
            )
        )
        source_artifact_bucket = aws_s3.CfnBucket(
            self,
            "SourceArtifactBucket",
            access_control="Private",
            bucket_encryption=aws_s3.CfnBucket.BucketEncryptionProperty(
                server_side_encryption_configuration=[
                    aws_s3.CfnBucket.ServerSideEncryptionRuleProperty(
                        server_side_encryption_by_default=aws_s3.CfnBucket.ServerSideEncryptionByDefaultProperty(
                            sse_algorithm="AES256"
                        )
                    )
                ]
            ),
            public_access_block_configuration=aws_s3.BlockPublicAccess.BLOCK_ALL,
            versioning_configuration=aws_s3.CfnBucket.VersioningConfigurationProperty(
                status="Enabled"
            )
        )
        source_artifact_bucket.override_logical_id(f"{id}SourceArtifactBucket")
        source_artifact_bucket.cfn_options.condition = self.source_artifact_bucket_name_not_exists_condition
        source_artifact_bucket.cfn_options.deletion_policy = CfnDeletionPolicy.RETAIN
        source_artifact_bucket.cfn_options.update_replace_policy = CfnDeletionPolicy.RETAIN
        source_artifact_bucket_name = Token.as_string(
            Fn.condition_if(
                self.source_artifact_bucket_name_exists_condition.logical_id,
                self.source_artifact_bucket_name_param.value_as_string,
                source_artifact_bucket.ref
            )
        )
        source_artifact_bucket_arn = Arn.format(
            components=ArnComponents(
                account="",
                partition=Aws.PARTITION,
                region="",
                resource=source_artifact_bucket_name,
                service="s3"
            )
        )
        source_artifact_object_key_arn = Arn.format(
            components=ArnComponents(
                account="",
                partition=Aws.PARTITION,
                region="",
                resource=source_artifact_bucket_name,
                resource_name=self.source_artifact_object_key_param.value_as_string,
                service="s3"
            )
        )
        # codebuild
        codebuild_transform_service_role = aws_iam.CfnRole(
            self,
            "CodeBuildTransformServiceRole",
            assume_role_policy_document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[ "sts:AssumeRole" ],
                        principals=[ aws_iam.ServicePrincipal("codebuild.amazonaws.com") ]
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
                                    "logs:CreateLogGroup",
                                    "logs:CreateLogStream",
                                    "logs:PutLogEvents"
                                ],
                                resources=[ "*" ]
                            ),
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "s3:GetObject",
                                    "s3:PutObject"
                                ],
                                resources=[ self.pipeline_artifact_bucket_arn ]
                            )
                        ]
                    ),
                    policy_name="TransformRolePermssions"
                )
            ]
        )
        codebuild_transform_service_role.override_logical_id(f"{id}CodeBuildTransformServiceRole")
        codebuild_transform_service_role_arn = Arn.format(
            components=ArnComponents(
                account=Aws.ACCOUNT_ID,
                partition=Aws.PARTITION,
                region="",
                resource="role",
                resource_name=codebuild_transform_service_role.ref,
                service="iam"
            )
        )
        buildspec_beginning = """
version: 0.2

phases:
  build:
    commands:
      - |
        cat << EOF > after-install.sh;
        #!/bin/bash
        echo "$(date): Starting after-install.sh..."
        ###
        # Custom Commands
        ###
"""
        if after_deploy_commands:
            for command in after_deploy_commands:
                buildspec_beginning += f"        {command}\n"
        buildspec_middle = """        echo "$(date): Finished after-install.sh."
        EOF
        cat << EOF > appspec.yml;
        version: 0.0
        os: linux
        hooks:
          AfterInstall:
            - location: after-install.sh
              runas: root
        EOF
      - cat appspec.yml
      - cat after-install.sh
"""
        if after_build_commands:
            for command in after_build_commands:
                buildspec_middle += f"      - {command}\n"
        buildspec_end = """    finally:
      - echo Finished build
artifacts:
  files:
    - "**/*"
"""
        codebuild_transform_project_buildspec = buildspec_beginning + buildspec_middle + buildspec_end
        self.codebuild_transform_project = aws_codebuild.CfnProject(
            self,
            "CodeBuildTransformProject",
            artifacts=aws_codebuild.CfnProject.ArtifactsProperty(
                type="CODEPIPELINE",
            ),
            environment=aws_codebuild.CfnProject.EnvironmentProperty(
                compute_type="BUILD_GENERAL1_SMALL",
                environment_variables=[],
                image="aws/codebuild/standard:7.0",
                type="LINUX_CONTAINER"
            ),
            name="{}-transform".format(Aws.STACK_NAME),
            service_role=codebuild_transform_service_role_arn,
            source=aws_codebuild.CfnProject.SourceProperty(
                build_spec=codebuild_transform_project_buildspec,
                type="CODEPIPELINE"
            )
        )
        self.codebuild_transform_project.override_logical_id(f"{id}CodeBuildTransformProject")
        codedeploy_application = aws_codedeploy.CfnApplication(
            self,
            "CodeDeployApplication",
            application_name=Aws.STACK_NAME,
            compute_platform="Server"
        )
        codedeploy_application.override_logical_id(f"{id}CodeDeployApplication")
        codedeploy_role = aws_iam.CfnRole(
             self,
            "CodeDeployRole",
            assume_role_policy_document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[ "sts:AssumeRole" ],
                        principals=[ aws_iam.ServicePrincipal("codedeploy.{}.amazonaws.com".format(Aws.REGION)) ]
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
                                    "s3:GetObject",
                                    "s3:PutObject"
                                ],
                                resources=[ self.pipeline_artifact_bucket_arn ]
                            ),
                        ]
                    ),
                    policy_name="DeployRolePermssions"
                )
            ],
            managed_policy_arns=[ "arn:aws:iam::aws:policy/service-role/AWSCodeDeployRole" ]
        )
        codedeploy_role.override_logical_id(f"{id}CodeDeployRole")
        codedeploy_role_arn = Arn.format(
            components=ArnComponents(
                account=Aws.ACCOUNT_ID,
                partition=Aws.PARTITION,
                region="",
                resource="role",
                resource_name=codedeploy_role.ref,
                service="iam"
            )
        )
        self.codedeploy_deployment_group = aws_codedeploy.CfnDeploymentGroup(
            self,
            "CodeDeployDeploymentGroup",
            application_name=codedeploy_application.application_name,
            deployment_group_name="{}-app".format(Aws.STACK_NAME),
            deployment_config_name=aws_codedeploy.ServerDeploymentConfig.ONE_AT_A_TIME.deployment_config_name,
            service_role_arn=codedeploy_role_arn,
            trigger_configurations=[
                aws_codedeploy.CfnDeploymentGroup.TriggerConfigProperty(
                    trigger_events=[
                        "DeploymentSuccess",
                        "DeploymentRollback"
                    ],
                    trigger_name="DeploymentNotification",
                    trigger_target_arn=notification_topic_arn
                )
            ]
        )
        if asg:
            self.codedeploy_deployment_group.auto_scaling_groups = [ asg.asg.ref ]
        self.codedeploy_deployment_group.override_logical_id(f"{id}CodeDeployDeploymentGroup")

        # codepipeline
        codepipeline_role = aws_iam.CfnRole(
            self,
            "PipelineRole",
            assume_role_policy_document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[ "sts:AssumeRole" ],
                        principals=[ aws_iam.ServicePrincipal("codepipeline.amazonaws.com") ]
                    )
                ]
            )
        )
        codepipeline_role.override_logical_id(f"{id}PipelineRole")
        codepipeline_role_arn = Arn.format(
            components=ArnComponents(
                account=Aws.ACCOUNT_ID,
                partition=Aws.PARTITION,
                region="",
                resource="role",
                resource_name=codepipeline_role.ref,
                service="iam"
            )
        )
        codepipeline_source_stage_role = aws_iam.CfnRole(
            self,
            "SourceStageRole",
            assume_role_policy_document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[ "sts:AssumeRole" ],
                        principals=[ aws_iam.ArnPrincipal(codepipeline_role_arn) ]
                    )
                ],
            ),
            policies=[
                aws_iam.CfnRole.PolicyProperty(
                    policy_document=aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "s3:Get*",
                                    "s3:Head*"
                                ],
                                resources=[ source_artifact_object_key_arn ]
                            ),
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[ "s3:GetBucketVersioning" ],
                                resources=[
                                    Arn.format(
                                        components=ArnComponents(
                                            account="",
                                            partition=Aws.PARTITION,
                                            region="",
                                            resource=source_artifact_bucket_name,
                                            service="s3"
                                        )
                                    )
                                ]
                            ),
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "s3:GetObject",
                                    "s3:PutObject"
                                ],
                                resources=[ self.pipeline_artifact_bucket_arn ]
                            )
                        ]
                    ),
                    policy_name="SourceRolePerms"
                )
            ]
        )
        codepipeline_source_stage_role.override_logical_id(f"{id}SourceStageRole")
        codepipeline_source_stage_role_arn = Arn.format(
            components=ArnComponents(
                account=Aws.ACCOUNT_ID,
                partition=Aws.PARTITION,
                region="",
                resource="role",
                resource_name=codepipeline_source_stage_role.ref,
                service="iam"
            )
        )
        codepipeline_transform_stage_role = aws_iam.CfnRole(
            self,
            "TransformStageRole",
            assume_role_policy_document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[ "sts:AssumeRole" ],
                        principals= [ aws_iam.ArnPrincipal(codepipeline_role_arn) ]
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
                                    "codebuild:BatchGetBuilds",
                                    "codebuild:StartBuild"
                                ],
                                resources=[ self.codebuild_transform_project.attr_arn ],
                            )
                        ]
                    ),
                    policy_name="TransformRolePerms"
                )
            ]
        )
        codepipeline_transform_stage_role.override_logical_id(f"{id}TransformStageRole")
        codepipeline_transform_stage_role_arn = Arn.format(
            components=ArnComponents(
                account=Aws.ACCOUNT_ID,
                partition=Aws.PARTITION,
                region="",
                resource="role",
                resource_name=codepipeline_transform_stage_role.ref,
                service="iam"
            )
        )
        codepipeline_deploy_stage_role = aws_iam.CfnRole(
            self,
            "DeployStageRole",
            assume_role_policy_document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[ "sts:AssumeRole" ],
                        principals= [ aws_iam.ArnPrincipal(codepipeline_role_arn) ]
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
                                    "codedeploy:GetApplication",
                                    "codedeploy:RegisterApplicationRevision"
                                ],
                                resources=[
                                    f"arn:{Aws.PARTITION}:codedeploy:{Aws.REGION}:{Aws.ACCOUNT_ID}:application:{codedeploy_application.application_name}"
                                ],
                                sid="codedeployapplication"
                            ),
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "codedeploy:CreateDeployment",
                                    "codedeploy:GetDeployment",
                                    "codedeploy:GetDeploymentGroup"
                                ],
                                resources=[
                                    f"arn:{Aws.PARTITION}:codedeploy:{Aws.REGION}:{Aws.ACCOUNT_ID}:deploymentgroup:{codedeploy_application.application_name}/{self.codedeploy_deployment_group.deployment_group_name}"
                                ],
                                sid="codedeploydeploymentgroup"
                            ),
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "s3:GetObject",
                                    "s3:PutObject"
                                ],
                                resources=[ self.pipeline_artifact_bucket_arn ]
                            ),
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "codedeploy:GetDeploymentConfig"
                                ],
                                resources=[
                                    f"arn:{Aws.PARTITION}:codedeploy:{Aws.REGION}:{Aws.ACCOUNT_ID}:deploymentconfig:CodeDeployDefault.AllAtOnce",
                                    f"arn:{Aws.PARTITION}:codedeploy:{Aws.REGION}:{Aws.ACCOUNT_ID}:deploymentconfig:CodeDeployDefault.OneAtATime"
                                ],
                                sid="codedeploydeploymentconfig"
                            )
                        ]
                    ),
                    policy_name="DeployRolePerms"
                )
            ]
        )
        codepipeline_deploy_stage_role.override_logical_id(f"{id}DeployStageRole")
        codepipeline_deploy_stage_role_arn = Arn.format(
            components=ArnComponents(
                account=Aws.ACCOUNT_ID,
                partition=Aws.PARTITION,
                region="",
                resource="role",
                resource_name=codepipeline_deploy_stage_role.ref,
                service="iam"
            )
        )
        pipeline = aws_codepipeline.CfnPipeline(
            self,
            "Pipeline",
            artifact_store=aws_codepipeline.CfnPipeline.ArtifactStoreProperty(
                location=Token.as_string(
                    Fn.condition_if(
                        self.pipeline_artifact_bucket_name_exists_condition.logical_id,
                        self.pipeline_artifact_bucket_name_param.value_as_string,
                        pipeline_artifact_bucket.ref
                    )
                ),
                type="S3"
            ),
            role_arn=codepipeline_role_arn,
            stages=[
                aws_codepipeline.CfnPipeline.StageDeclarationProperty(
                    name="Source",
                    actions=[
                        aws_codepipeline.CfnPipeline.ActionDeclarationProperty(
                            action_type_id=aws_codepipeline.CfnPipeline.ActionTypeIdProperty(
                                category="Source",
                                owner="AWS",
                                provider="S3",
                                version="1"
                            ),
                            configuration={
                                "S3Bucket": source_artifact_bucket_name,
                                "S3ObjectKey": self.source_artifact_object_key_param.value_as_string
                            },
                            output_artifacts=[
                                aws_codepipeline.CfnPipeline.OutputArtifactProperty(
                                    name="build"
                                )
                            ],
                            name="SourceAction",
                            role_arn=codepipeline_source_stage_role_arn
                        )
                    ]
                ),
                aws_codepipeline.CfnPipeline.StageDeclarationProperty(
                    name="Transform",
                    actions=[
                        aws_codepipeline.CfnPipeline.ActionDeclarationProperty(
                            action_type_id=aws_codepipeline.CfnPipeline.ActionTypeIdProperty(
                                category="Build",
                                owner="AWS",
                                provider="CodeBuild",
                                version="1"
                            ),
                            configuration={
                                "ProjectName": self.codebuild_transform_project.ref
                            },
                            input_artifacts=[
                                aws_codepipeline.CfnPipeline.InputArtifactProperty(
                                    name="build",
                                )
                            ],
                            name="TransformAction",
                            output_artifacts=[
                                aws_codepipeline.CfnPipeline.OutputArtifactProperty(
                                    name="transformed"
                                )
                            ],
                            role_arn=codepipeline_transform_stage_role_arn
                        )
                    ]
                ),
                aws_codepipeline.CfnPipeline.StageDeclarationProperty(
                    name="Deploy",
                    actions=[
                        aws_codepipeline.CfnPipeline.ActionDeclarationProperty(
                            action_type_id=aws_codepipeline.CfnPipeline.ActionTypeIdProperty(
                                category="Deploy",
                                owner="AWS",
                                provider="CodeDeploy",
                                version="1"
                            ),
                            configuration={
                                "ApplicationName": codedeploy_application.ref,
                                "DeploymentGroupName": self.codedeploy_deployment_group.ref,
                            },
                            input_artifacts=[
                                aws_codepipeline.CfnPipeline.InputArtifactProperty(
                                    name="transformed"
                                )
                            ],
                            name="DeployAction",
                            role_arn=codepipeline_deploy_stage_role_arn
                        )
                    ]
                )
            ]
        )
        pipeline.override_logical_id(f"{id}Pipeline")

        iam_notification_publish_policy = aws_iam.PolicyDocument(
            statements=[
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[ "sns:Publish" ],
                    resources=[ notification_topic_arn ]
                )
            ]
        )

        # default app
        initialize_demo_lambda_function_role = aws_iam.CfnRole(
            self,
            "InitializeDemoLambdaFunctionRole",
            assume_role_policy_document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[ "sts:AssumeRole" ],
                        principals=[ aws_iam.ServicePrincipal("lambda.amazonaws.com") ]
                    )
                ]
            ),
            managed_policy_arns=[
                "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            ],
            policies=[
                # OE default artifact should be public, so no policy needed for s3:GetObject
                aws_iam.CfnRole.PolicyProperty(
                    policy_document=aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[ "s3:ListBucket" ],
                                resources=[ source_artifact_bucket_arn ]
                            ),
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "s3:HeadObject",
                                    "s3:PutObject"
                                ],
                                resources=[ source_artifact_object_key_arn ]
                            )
                        ]
                    ),
                    policy_name="PutDemoArtifact"
                ),
                aws_iam.CfnRole.PolicyProperty(
                    policy_document=iam_notification_publish_policy,
                    policy_name="SnsPublishToNotificationTopic"
                )
            ]
        )
        initialize_demo_lambda_function_role.override_logical_id(f"{id}InitializeDemoLambdaFunctionRole")
        initialize_demo_lambda_function_role.cfn_options.condition = self.initialize_demo_condition
        demo_lambda_function_code_path = Util.local_path("app_deploy_pipeline/initialize_demo_lambda_function_code.py")
        with open(demo_lambda_function_code_path) as f:
            initialize_demo_lambda_function_code = f.read()
        initialize_demo_lambda_function = aws_lambda.CfnFunction(
            self,
            "InitializeDemoLambdaFunction",
            code=aws_lambda.CfnFunction.CodeProperty(
                zip_file=initialize_demo_lambda_function_code
            ),
            dead_letter_config=aws_lambda.CfnFunction.DeadLetterConfigProperty(
                target_arn=notification_topic_arn
            ),
            environment=aws_lambda.CfnFunction.EnvironmentProperty(
                variables={
                    "DemoSourceUrl": demo_source_url,
                    "SourceArtifactBucket": source_artifact_bucket_name,
                    "SourceArtifactObjectKey": self.source_artifact_object_key_param.value_as_string,
                    "StackName": Aws.STACK_NAME
                }
            ),
            handler="index.lambda_handler",
            role=initialize_demo_lambda_function_role.attr_arn,
            runtime="python3.12",
            timeout=300
        )
        initialize_demo_lambda_function.override_logical_id(f"{id}InitializeDemoLambdaFunction")
        initialize_demo_lambda_function.cfn_options.condition = self.initialize_demo_condition
        initialize_demo_custom_resource = aws_cloudformation.CfnCustomResource(
            self,
            "InitializeDemoCustomResource",
            service_token=initialize_demo_lambda_function.attr_arn
        )
        initialize_demo_custom_resource.override_logical_id(f"{id}InitializeDemoCustomResource")
        initialize_demo_custom_resource.cfn_options.condition = self.initialize_demo_condition


        #
        # OUTPUTS
        #
        source_artifact_bucket_name_output = CfnOutput(
            self,
            "SourceArtifactBucketNameOutput",
            description="The source artifact S3 bucket name that is monitored for updates to be deployed",
            value=source_artifact_bucket_name
        )
        source_artifact_bucket_name_output.override_logical_id(f"{id}SourceArtifactBucketNameOutput")
        source_artifact_object_key_output = CfnOutput(
            self,
            "SourceArtifactObjectKeyOutput",
            description="The source artifact S3 object key that is monitored for updates to be deployed",
            value=self.source_artifact_object_key_param.value_as_string
        )
        source_artifact_object_key_output.override_logical_id(f"{id}SourceArtifactObjectKeyOutput")

    def add_codebuild_transform_environment_variable(self, name, value):
        self.codebuild_transform_project.environment.environment_variables.append(
            aws_codebuild.CfnProject.EnvironmentVariableProperty(
                name=name,
                value=value
            )
        )

    def add_asg_to_deployment_group(self, asg):
        self.codedeploy_deployment_group.auto_scaling_groups = [ asg.asg.ref ]

    def metadata_parameter_group(self):
        params = [
            self.initialize_demo_param.logical_id,
            self.pipeline_artifact_bucket_name_param.logical_id,
            self.source_artifact_bucket_name_param.logical_id,
            self.source_artifact_object_key_param.logical_id
        ]
        return [
            {
                "Label": {
                    "default": "Deploy Pipeline Configuration"
                },
                "Parameters": params
            }
        ]

    def metadata_parameter_labels(self):
        params = {
            self.initialize_demo_param.logical_id: {
                "default": "Initialize Demo"
            },
            self.pipeline_artifact_bucket_name_param.logical_id: {
                "default": "Pipeline Artifact Bucket Name"
            },
            self.source_artifact_bucket_name_param.logical_id: {
                "default": "Source Artifact Bucket Name"
            },
            self.source_artifact_object_key_param.logical_id: {
                "default": "Source Artifact Object Key"
            },
        }
        return params
