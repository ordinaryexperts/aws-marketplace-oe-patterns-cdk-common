from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.secret import Secret
from . import print_resource

def test_secret():
  stack = Stack()
  db_secret = Secret(stack, "DB")
  rabbitmq_secret = Secret(stack, "RabbitMQ", username="rabbitmq")
  template = assertions.Template.from_stack(stack)
  template.resource_count_is("AWS::SSM::Parameter", 2)
  template.has_resource_properties(
    "AWS::SecretsManager::Secret",
    {
      "GenerateSecretString": {
        "SecretStringTemplate": "{\"username\": \"admin\"}"
      }
    }
  )

def test_secret_custom_username():
  stack = Stack()
  Secret(stack, "TestDbSecret", username="customuser")
  template = assertions.Template.from_stack(stack)
  template.resource_count_is("AWS::SSM::Parameter", 1)
  template.has_resource_properties(
    "AWS::SecretsManager::Secret",
    {
      "GenerateSecretString": {
        "SecretStringTemplate": "{\"username\": \"customuser\"}"
      }
    }
  )

def test_secret_password_length():
  stack = Stack()
  Secret(stack, "TestDbSecret", password_length=50)
  template = assertions.Template.from_stack(stack)
  template.resource_count_is("AWS::SSM::Parameter", 1)
  # print_resource(template, 'AWS::SecretsManager::Secret')
  template.has_resource_properties(
    "AWS::SecretsManager::Secret",
    {
      "GenerateSecretString": {
        "PasswordLength": 50
      }
    }
  )
