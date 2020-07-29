from aws_cdk import core

class Vpc(core.Construct):

    def __init__(self, scope: core.Construct, id: str, *):

        vpc_id_param = core.CfnParameter(
            self,
            "VpcId",
            default="",
            description="Optional: Specify the VPC ID. If not specified, a VPC will be created."
        )
