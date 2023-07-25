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

class Secret(Construct):
    def __init__(
            self,
            scope: Construct,
            id: str,
            password_length: int = 32,
            username: str = 'admin',
            **props):
        super().__init__(scope, id, **props)

        self.id = id

        self.secret_arn_param = CfnParameter(
            self,
            "SecretArn",
            default="",
            description=f"Optional: Secrets Manager Secret ARN used to store {id} credentials. If not specified, a secret will be created."
        )
        self.secret_arn_param.override_logical_id(f"{id}Arn")

        self.secret_arn_exists_condition = CfnCondition(
            self,
            "SecretArnExistsCondition",
            expression=Fn.condition_not(Fn.condition_equals(self.secret_arn_param.value, ""))
        )
        self.secret_arn_exists_condition.override_logical_id(f"{id}SecretArnExistsCondition")
        self.secret_arn_not_exists_condition = CfnCondition(
            self,
            "SecretArnNotExistsCondition",
            expression=Fn.condition_equals(self.secret_arn_param.value, "")
        )
        self.secret_arn_not_exists_condition.override_logical_id(f"{id}SecretArnNotExistsCondition")

        self.secret = aws_secretsmanager.CfnSecret(
            self,
            "Secret",
            generate_secret_string=aws_secretsmanager.CfnSecret.GenerateSecretStringProperty(
                exclude_characters="\"@/\\\"'$,[]*?{}~#%<>|^",
                exclude_punctuation=True,
                generate_string_key="password",
                password_length=password_length,
                secret_string_template=json.dumps({"username":username})
            ),
            name="{}/{}/secret".format(Aws.STACK_NAME, self.id.lower())
        )
        self.secret.cfn_options.condition = self.secret_arn_not_exists_condition
        self.secret.override_logical_id(f"{id}Secret")

        self.secret_arn_ssm_param = aws_ssm.CfnParameter(
            self,
            "SecretArnParameter",
            type="String",
            value=self.secret_arn(),
            name=Aws.STACK_NAME + f"-{id.lower()}-secret-arn"
        )
        self.secret_arn_ssm_param.override_logical_id(f"{id}SecretArnParameter")

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
                    "default": f"{self.id} Secret Configuration"
                },
                "Parameters": [
                    self.secret_arn_param.logical_id
                ]
            }
        ]

    def metadata_parameter_labels(self):
        return {
            self.secret_arn_param.logical_id: {
                "default": f"{self.id} Secret ARN"
            }
        }
