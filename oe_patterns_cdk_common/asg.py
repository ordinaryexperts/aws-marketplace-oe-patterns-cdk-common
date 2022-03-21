from aws_cdk import (
    aws_ec2,
    core
)

class Asg(core.Construct):

    def __init__(self, scope: core.Construct, id: str, **props):
        super().__init__(scope, id)
