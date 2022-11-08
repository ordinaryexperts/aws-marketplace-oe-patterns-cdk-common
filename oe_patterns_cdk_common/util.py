from aws_cdk import (
    Aws,
    aws_ec2,
    Fn
)

class Util:

    # utility function to parse the unique id from the stack id for                                                 
    # shorter resource names using cloudformation functions
    @staticmethod
    def append_stack_uuid(name):
        return Fn.join("-", [
            name,
	    Fn.select(2, Fn.split("/", Aws.STACK_ID))
        ])

    @staticmethod
    def add_sg_ingress(resource, sg):
        ingress = aws_ec2.CfnSecurityGroupIngress(
            resource,
            "SgIngress",
            source_security_group_id=sg.ref,
            from_port=resource.port,
            group_id=resource.sg.ref,
            ip_protocol="tcp",
            to_port=resource.port
        )
        ingress.override_logical_id(f"{resource.id}SgIngress")
        return ingress
