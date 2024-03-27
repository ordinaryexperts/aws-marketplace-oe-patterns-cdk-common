from aws_cdk import (
  assertions,
  Stack
)

from oe_patterns_cdk_common.vpc import Vpc
from oe_patterns_cdk_common.asg import Asg
from oe_patterns_cdk_common.app_deploy_pipeline import AppDeployPipeline
# from . import print_resource

def test_app_deploy_pipeline():
  stack = Stack()
  vpc = Vpc(stack, 'TestVpc')
  pipeline = AppDeployPipeline(stack, "TestAppDeployPipeline", demo_source_url="TESTURL", notification_topic_arn="TESTARN")
  template = assertions.Template.from_stack(stack)

  template.resource_count_is("AWS::CodePipeline::Pipeline", 1)

def test_app_deploy_pipeline_with_asg():
  stack = Stack()
  vpc = Vpc(stack, 'TestVpc')
  asg = Asg(stack, 'TestAsg', vpc=vpc)
  AppDeployPipeline(stack, "TestAppDeployPipeline", asg=asg, demo_source_url="TESTURL", notification_topic_arn="TESTARN")
  template = assertions.Template.from_stack(stack)

  # import json; print(json.dumps(template.to_json(), indent=4, sort_keys=True))
  template.resource_count_is("AWS::CodePipeline::Pipeline", 1)

def test_app_deploy_pipeline_buildspec():
  stack = Stack()
  vpc = Vpc(stack, 'TestVpc')
  after_build_commands = [
    "echo one",
    "echo two"
  ]
  after_deploy_commands = [
    "rm -rf /app/cache",
    "service apache2 reload"
  ]
  pipeline = AppDeployPipeline(
    stack,
    "TestAppDeployPipeline",
    after_build_commands=after_build_commands,
    after_deploy_commands=after_deploy_commands,
    demo_source_url="TESTURL",
    notification_topic_arn="TESTARN"
  )
  template = assertions.Template.from_stack(stack)

  project = template.find_resources("AWS::CodeBuild::Project")
  # print(project)
  buildspec = project['TestAppDeployPipelineCodeBuildTransformProject']['Properties']['Source']['BuildSpec']

  desired = """
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
        rm -rf /app/cache
        service apache2 reload
        echo "$(date): Finished after-install.sh."
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
      - echo one
      - echo two
    finally:
      - echo Finished build
artifacts:
  files:
    - "**/*"
"""
  assert desired == buildspec
  
def test_app_deploy_pipeline_buildspec_default():
  stack = Stack()
  vpc = Vpc(stack, 'TestVpc')
  after_build_commands = [
    "echo one",
    "echo two"
  ]
  after_deploy_commands = [
    "rm -rf /app/cache",
    "service apache2 reload"
  ]
  pipeline = AppDeployPipeline(
    stack,
    "TestAppDeployPipeline",
    demo_source_url="TESTURL",
    notification_topic_arn="TESTARN"
  )
  template = assertions.Template.from_stack(stack)

  project = template.find_resources("AWS::CodeBuild::Project")
  # print(project)
  buildspec = project['TestAppDeployPipelineCodeBuildTransformProject']['Properties']['Source']['BuildSpec']

  desired = """
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
        echo "$(date): Finished after-install.sh."
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
    finally:
      - echo Finished build
artifacts:
  files:
    - "**/*"
"""
  assert desired == buildspec
