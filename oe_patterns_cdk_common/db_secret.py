import json

from aws_cdk import (
    Aws,
    aws_secretsmanager,
    aws_ssm,
    CfnCondition,
    CfnParameter,
    Fn,
    Token
)

from constructs import Construct

# deprecated - use Secret instead
class DbSecret(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str,
            username: str = 'dbadmin',
            **props):
        super().__init__(scope, id, **props)

        self.secret_arn_param = CfnParameter(
            self,
            "DbSecretArn",
            default="",
            description="Optional: SecretsManager secret ARN used to store database credentials and other configuration. If not specified, a secret will be created."
        )
        self.secret_arn_param.override_logical_id(f"{id}Arn")

        self.secret_arn_exists_condition = CfnCondition(
            self,
            "DbSecretArnExistsCondition",
            expression=Fn.condition_not(Fn.condition_equals(self.secret_arn_param.value, ""))
        )
        self.secret_arn_exists_condition.override_logical_id(f"{id}ArnExistsCondition")
        self.secret_arn_not_exists_condition = CfnCondition(
            self,
            "DbSecretArnNotExistsCondition",
            expression=Fn.condition_equals(self.secret_arn_param.value, "")
        )
        self.secret_arn_not_exists_condition.override_logical_id(f"{id}ArnNotExistsCondition")

        self.secret = aws_secretsmanager.CfnSecret(
            self,
            "DbSecret",
            generate_secret_string=aws_secretsmanager.CfnSecret.GenerateSecretStringProperty(
                exclude_characters="\"@/\\\"'$,[]*?{}~#%<>|^",
                exclude_punctuation=True,
                generate_string_key="password",
                secret_string_template=json.dumps({"username":username})
            ),
            name="{}/db/secret".format(Aws.STACK_NAME)
        )
        self.secret.cfn_options.condition = self.secret_arn_not_exists_condition
        self.secret.override_logical_id(id)


        self.db_secret_arn_ssm_param = aws_ssm.CfnParameter(
            self,
            "DbSecretArnParameter",
            type="String",
            value=self.secret_arn(),
            name=Aws.STACK_NAME + "-db-secret-arn"
        )
        self.db_secret_arn_ssm_param.override_logical_id(f"{id}ArnParameter")

    def secret_arn(self):
        return Token.as_string(
            Fn.condition_if(
                self.secret_arn_exists_condition.logical_id,
                self.secret_arn_param.value_as_string,
                self.secret.ref
            )
        )

    def metadata_parameter_group(self):
        return [
            {
                "Label": {
                    "default": "DB Secret Configuration"
                },
                "Parameters": [
                    self.secret_arn_param.logical_id
                ]
            }
        ]

    def metadata_parameter_labels(self):
        return {
            self.secret_arn_param.logical_id: {
                "default": "DB Secret ARN"
            }
        }
