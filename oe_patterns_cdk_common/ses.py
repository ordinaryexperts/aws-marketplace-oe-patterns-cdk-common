import os

from aws_cdk import (
    Aws,
    aws_iam,
    aws_lambda,
    aws_route53,
    aws_ses,
    CfnCondition,
    CfnParameter,
    CustomResource,
    Fn,
    Token
)

from constructs import Construct

class Ses(Construct):

    def __init__(
            self,
            scope: Construct,
            id: str,
            hosted_zone_name: str,
            additional_iam_user_policies: 'list[object]' = [],
            **props):
        super().__init__(scope, id, **props)

        self.id = id
        self.ttl = "300"

        self.instance_user_access_key_serial_param = CfnParameter(
            self,
            "SesInstanceUserAccessKeySerial",
            type="Number",
            default="1",
            description="Optional: Incrementing this integer value will trigger a rotation of the Instance User Access Key."
        )
        self.instance_user_access_key_serial_param.override_logical_id(f"{id}InstanceUserAccessKeySerial")

        self.create_domain_identity_param = CfnParameter(
            self,
            "SesCreateDomainIdentity",
            allowed_values=[ "true", "false" ],
            default="true",
            description="Optional: If 'true', a SES Domain Identity will be created from the hosted zone."
        )
        self.create_domain_identity_param.override_logical_id(f"{id}CreateDomainIdentity")

        self.create_domain_identity_condition = CfnCondition(
            self,
            "SesCreateDomainIdentityCondition",
            expression=Fn.condition_equals(self.create_domain_identity_param.value, "true")
        )
        self.create_domain_identity_condition.override_logical_id(f"{id}CreateDomainIdentityCondition")

        self.domain_identity = aws_ses.CfnEmailIdentity(
            self,
            "SesDomainIdentity",
            email_identity=hosted_zone_name
        )
        self.domain_identity.cfn_options.condition=self.create_domain_identity_condition
        self.domain_identity.override_logical_id(f"{id}DomainIdentity")

        self.dkim_dns_record_set1 = aws_route53.CfnRecordSet(
            self,
            "SesDkimDnsRecordSet1",
            hosted_zone_name=f"{hosted_zone_name}.",
            name=Token.as_string(self.domain_identity.attr_dkim_dns_token_name1),
            resource_records=[ self.domain_identity.attr_dkim_dns_token_value1 ],
            ttl=self.ttl,
            type="CNAME"
        )
        self.dkim_dns_record_set1.cfn_options.condition=self.create_domain_identity_condition
        self.dkim_dns_record_set1.override_logical_id(f"{id}DkimDnsRecordSet1")

        self.dkim_dns_record_set2 = aws_route53.CfnRecordSet(
            self,
            "DkimDnsRecordSet2",
            hosted_zone_name=f"{hosted_zone_name}.",
            name=Token.as_string(self.domain_identity.attr_dkim_dns_token_name2),
            resource_records=[ Token.as_string(self.domain_identity.attr_dkim_dns_token_value2) ],
            ttl=self.ttl,
            type="CNAME"
        )
        self.dkim_dns_record_set2.cfn_options.condition=self.create_domain_identity_condition
        self.dkim_dns_record_set2.override_logical_id(f"{id}DkimDnsRecordSet2")

        self.dkim_dns_record_set3 = aws_route53.CfnRecordSet(
            self,
            "DkimDnsRecordSet3",
            hosted_zone_name=f"{hosted_zone_name}.",
            name=Token.as_string(self.domain_identity.attr_dkim_dns_token_name3),
            resource_records=[ Token.as_string(self.domain_identity.attr_dkim_dns_token_value3) ],
            ttl=self.ttl,
            type="CNAME"
        )
        self.dkim_dns_record_set3.cfn_options.condition=self.create_domain_identity_condition
        self.dkim_dns_record_set3.override_logical_id(f"{id}DkimDnsRecordSet3")

        policies = [
            aws_iam.CfnUser.PolicyProperty(
                policy_document=aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "ses:SendEmail",
                                "ses:SendRawEmail"
                            ],
                            resources=["*"]
                        )
                    ]
                ),
                policy_name="AllowSendEmail"
            )
        ]

        if additional_iam_user_policies:
            policies.extend(additional_iam_user_policies)

        self.instance_user = aws_iam.CfnUser(
            self,
            "InstanceUser",
            path="/",
            policies=policies,
            user_name=f"{Aws.REGION}-{Aws.STACK_NAME}-instance"
        )
        self.instance_user.override_logical_id(f"{id}InstanceUser")

        # actual creds are required to generate the SMTP password
        self.instance_user_access_key = aws_iam.AccessKey(
            self,
            "InstanceUserAccessKey",
            serial=self.instance_user_access_key_serial_param.value_as_number,
            user=self.instance_user
        )
        self.instance_user_access_key.node.default_child.override_logical_id(f"{id}InstanceUserAccessKey")
        self.instance_user_access_key.node.add_dependency(self.instance_user)

        lambda_code_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "lambda_generate_smtp_password.py"
        )
        with open(lambda_code_path) as f:
            lambda_code = f.read()
        self.generate_smtp_password_lambda = aws_lambda.Function(
            self,
            "GenerateSMTPPasswordLambda",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            handler="index.handler",
            code=aws_lambda.Code.from_inline(lambda_code)
        )
        self.generate_smtp_password_lambda.node.default_child.override_logical_id(f"{id}GenerateSMTPPasswordLambda")
        # cdk generating unnecessary DependsOn to lambda role which breaks taskcat...
        self.generate_smtp_password_lambda.node.default_child.add_override('DependsOn', None)
        self.generate_smtp_password_lambda.role.node.default_child.override_logical_id(f"{id}GenerateSMTPPasswordLambdaRole")

        self.generate_smtp_password_lambda_secret_policy = aws_iam.Policy(
            self,
            "SecretPolicy",
            statements=[
                aws_iam.PolicyStatement(
                    actions=["secretsmanager:ListSecrets"],
                    resources=["*"]
                ),
                aws_iam.PolicyStatement(
                    actions=[
                        "secretsmanager:CreateSecret"
                    ],
                    resources=["*"],
                    conditions={
                        "StringEquals": {
                            "secretsmanager:Name": [f"{Aws.STACK_NAME}/instance/credentials"]
                        }
                    }
                ),
                aws_iam.PolicyStatement(
                    actions=[
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:UpdateSecret"
                    ],
                    resources=[
                        f"arn:{Aws.PARTITION}:secretsmanager:{Aws.REGION}:{Aws.ACCOUNT_ID}:secret:{Aws.STACK_NAME}/instance/credentials-*"
                    ]
                )
            ]
        )
        self.generate_smtp_password_lambda_secret_policy.node.default_child.override_logical_id(f"{id}InstanceUserCreateSecretPolicy")
        self.generate_smtp_password_lambda.role.attach_inline_policy(self.generate_smtp_password_lambda_secret_policy)
        self.generate_smtp_password_custom_resource = CustomResource(
            self,
            "GenerateSMTPPasswordCustomResource",
            service_token=self.generate_smtp_password_lambda.function_arn,
            properties={
                "access_key_id": self.instance_user_access_key.access_key_id,
                "aws_region": Aws.REGION,
                "secret_access_key": self.instance_user_access_key.secret_access_key.unsafe_unwrap(),
                "stack_name": Aws.STACK_NAME
            }
        )
        self.generate_smtp_password_custom_resource.node.default_child.override_logical_id(f"{id}GenerateSMTPPasswordCustomResource")

    def secret_arn(self):
        return Token.as_string(
            self.generate_smtp_password_custom_resource.get_att("arn")
        )

    def metadata_parameter_group(self):
        return [
            {
                "Label": {
                    "default": "Simple Email Service Configuration"
                },
                "Parameters": [
                    self.create_domain_identity_param.logical_id,
                    self.instance_user_access_key_serial_param.logical_id
                ]
            }
        ]

    def metadata_parameter_labels(self):
        return {
            self.create_domain_identity_param.logical_id: {
                "default": "Create SES Domain Identity"
            },
            self.instance_user_access_key_serial_param.logical_id: {
                "default": "Instance User Access Key Serial"
            }
        }
