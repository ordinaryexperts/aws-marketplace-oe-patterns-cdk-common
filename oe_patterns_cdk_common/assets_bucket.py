from aws_cdk import (
    aws_iam,
    aws_s3,
    Arn,
    ArnComponents,
    CfnCondition,
    CfnDeletionPolicy,
    CfnParameter,
    Fn,
    Stack,
    Token
)

from constructs import Construct

class AssetsBucket(Construct):

    def __init__(
            self,
            scope: Construct,
            id: str,
            allow_open_cors: bool = False,
            object_ownership_value: str = None,
            remove_public_access_block: bool = False,
            **props):
        super().__init__(scope, id, **props)

        self.assets_bucket_name_param = CfnParameter(
            self,
            "AssetsBucketName",
            default="",
            description="Optional: The name of the S3 bucket to store uploaded assets. If not specified, a bucket will be created."
        )
        self.assets_bucket_name_param.override_logical_id(f"{id}Name")
        self.assets_bucket_name_not_exists_condition = CfnCondition(
            self,
            "AssetsBucketNameNotExists",
            expression=Fn.condition_equals(self.assets_bucket_name_param.value, "")
        )
        self.assets_bucket_name_not_exists_condition.override_logical_id(f"{id}NameNotExists")
        self.assets_bucket = aws_s3.CfnBucket(
            self,
            "AssetsBucket",
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
        )
        if allow_open_cors:
            self.assets_bucket.cors_configuration = aws_s3.CfnBucket.CorsConfigurationProperty(
                cors_rules = [
                    aws_s3.CfnBucket.CorsRuleProperty(
                        allowed_headers=['*'],
                        allowed_methods=['GET'],
                        allowed_origins=['*'],
                        exposed_headers=[]
                    )
                ]
            )
        if object_ownership_value:
            self.assets_bucket.ownership_controls=aws_s3.CfnBucket.OwnershipControlsProperty(
                rules=[
                    aws_s3.CfnBucket.OwnershipControlsRuleProperty(
                        object_ownership=object_ownership_value
                    )
                ]
            )
        if remove_public_access_block:
            self.assets_bucket.public_access_block_configuration=aws_s3.CfnBucket.PublicAccessBlockConfigurationProperty(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
            )
        self.assets_bucket.override_logical_id(f"{id}")
        self.assets_bucket.cfn_options.condition=self.assets_bucket_name_not_exists_condition
        self.assets_bucket.cfn_options.deletion_policy = CfnDeletionPolicy.RETAIN
        self.assets_bucket.cfn_options.update_replace_policy = CfnDeletionPolicy.RETAIN
        self.assets_bucket_arn = Arn.format(
            components=ArnComponents(
                account="",
                region="",
                resource=Token.as_string(
                    Fn.condition_if(
                        self.assets_bucket_name_not_exists_condition.logical_id,
                        self.assets_bucket.ref,
                        self.assets_bucket_name_param.value_as_string
                    )
                ),
                service="s3"
            ),
            stack=Stack.of(self)
        )
        # permissions for s3 bucket - needs to be attached to user
        self.user_policy = aws_iam.CfnUser.PolicyProperty(
            policy_document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[
                            "s3:*"
                        ],
                        resources=[ f"{self.assets_bucket_arn}/*" ]
                    ),
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[
                            "s3:GetBucketCORS",
                            "s3:GetBucketLocation",
                            "s3:ListBucket",
                            "s3:PutBucketCORS"
                        ],
                        resources=[ self.assets_bucket_arn ]
                    )
                ]
            ),
            policy_name=f"{id}AllowBucket"
        )


    def bucket_name(self):
        return Token.as_string(
            Fn.condition_if(
                self.assets_bucket_name_not_exists_condition.logical_id,
                self.assets_bucket.ref,
                self.assets_bucket_name_param.value_as_string
            )
        )

    def metadata_parameter_group(self):
        return [
            {
                "Label": {
                    "default": "Assets Bucket Configuration"
                },
                "Parameters": [
                    self.assets_bucket_name_param.logical_id
                ],
            }
        ]

    def metadata_parameter_labels(self):
        return {
            self.assets_bucket_name_param.logical_id: {
                "default": "Assets Bucket Name"
            }
        }
