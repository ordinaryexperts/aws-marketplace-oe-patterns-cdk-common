from aws_cdk import (
    aws_autoscaling,
    aws_ec2,
    aws_efs,
    aws_elasticloadbalancingv2,
    aws_iam,
    Aws,
    CfnCondition,
    CfnParameter,
    Fn,
    Tags
)

from constructs import Construct
from oe_patterns_cdk_common.asg import Asg
from oe_patterns_cdk_common.vpc import Vpc

class Alb(Construct):

    def __init__(
            self,
            scope: Construct,
            id: str,
            vpc: Vpc,
            asg: Asg,
            **props):
        super().__init__(scope, id, **props)

        #
        # PARAMETERS
        #

        self.certificate_arn_param = CfnParameter(
            self,
            "CertificateArn",
            default="",
            description="Optional: Specify the ARN of a ACM Certificate to configure HTTPS."
        )
        self.certificate_arn_param.override_logical_id(f"{id}CertificateArn")
        self.alb_ingress_cidr_param = CfnParameter(
            self,
            "AlbIngressCidr",
            allowed_pattern=r"^((\d{1,3})\.){3}\d{1,3}/\d{1,2}$",
            default="0.0.0.0/0",
            description="Optional: VPC IPv4 CIDR block to restrict public access to ALB (default is 0.0.0.0/0 which is open to internet)."
        )
        self.alb_ingress_cidr_param.override_logical_id(f"{id}IngressCidr")

        self.sg = aws_ec2.CfnSecurityGroup(
            self,
            "AlbSg",
            group_description="{}/AlbSg".format(Aws.STACK_NAME),
            vpc_id=vpc.id()
        )
        self.sg.override_logical_id(f"{id}Sg")
        Tags.of(self.sg).add("Name", "{}/AlbSg".format(Aws.STACK_NAME))
        self.alb_http_ingress = aws_ec2.CfnSecurityGroupIngress(
            self,
            "AlbSgHttpIngress",
            cidr_ip=self.alb_ingress_cidr_param.value_as_string,
            description="Allow HTTP traffic to ALB from anyone",
            from_port=80,
            group_id=self.sg.ref,
            ip_protocol="tcp",
            to_port=80
        )
        self.alb_https_ingress = aws_ec2.CfnSecurityGroupIngress(
            self,
            "AlbSgHttpsIngress",
            cidr_ip=self.alb_ingress_cidr_param.value_as_string,
            description="Allow HTTPS traffic to ALB from anyone",
            from_port=443,
            group_id=self.sg.ref,
            ip_protocol="tcp",
            to_port=443
        )
        self.sg_https_ingress = aws_ec2.CfnSecurityGroupIngress(
            self,
            "AppSgHttpsIngress",
            description="Allow HTTPS traffic from Alb to App",
            from_port=443,
            group_id=asg.sg.ref,
            ip_protocol="tcp",
            source_security_group_id=self.sg.ref,
            to_port=443
        )

        self.alb = aws_elasticloadbalancingv2.CfnLoadBalancer(
            self,
            "AppAlb",
            scheme="internet-facing",
            security_groups=[ self.sg.ref ],
            subnets=vpc.public_subnet_ids(),
            type="application"
        )
        self.http_listener = aws_elasticloadbalancingv2.CfnListener(
            self,
            "HttpListener",
            # These are updated in the override below to fix case of properties - see below
            default_actions=[
                aws_elasticloadbalancingv2.CfnListener.ActionProperty(
                    redirect_config=aws_elasticloadbalancingv2.CfnListener.RedirectConfigProperty(
                        host="#{host}",
                        path="/#{path}",
                        port="443",
                        protocol="HTTPS",
                        query="#{query}",
                        status_code="HTTP_301"
                    ),
                    type="redirect"
                )
            ],
            load_balancer_arn=self.alb.ref,
            port=80,
            protocol="HTTP"
        )
        # CDK generates ActionProperty with lowercase properties - need to override due to following error:
        # Stack operations on resource HttpListener would fail starting from 03/01/2021 as the template has invalid properties.
        # Please refer to the resource documentation to fix the template.
        # Properties validation failed for resource HttpListener with message:
        # #/DefaultActions/0: required key [Type] not found
        # #/DefaultActions/0: extraneous key [type] is not permitted
        # #/DefaultActions/0: extraneous key [redirectConfig] is not permitted
        self.http_listener.add_override(
            "Properties.DefaultActions",
            [
                {
                    'Type': 'redirect',
                    'RedirectConfig': {
                        'Host': "#{host}",
                        'Path': "/#{path}",
                        'Port': "443",
                        'Protocol': "HTTPS",
                        'Query': "#{query}",
                        'StatusCode': "HTTP_301"
                    }
                }
            ]
        )

        self.https_target_group = aws_elasticloadbalancingv2.CfnTargetGroup(
            self,
            "AsgHttpsTargetGroup",
            health_check_enabled=None,
            health_check_interval_seconds=None,
            port=443,
            protocol="HTTPS",
            target_group_attributes=[
                aws_elasticloadbalancingv2.CfnTargetGroup.TargetGroupAttributeProperty(
                    key='deregistration_delay.timeout_seconds',
                    value='10'
                )
            ],
            target_type="instance",
            vpc_id=vpc.id()
        )
        # TODO moved to calling stack?
        # self.asg.asg.target_group_arns = [ self.https_target_group.ref ]
        self.https_listener = aws_elasticloadbalancingv2.CfnListener(
            self,
            "HttpsListener",
            certificates=[
                aws_elasticloadbalancingv2.CfnListener.CertificateProperty(
                    certificate_arn=self.certificate_arn_param.value_as_string
                )
            ],
            default_actions=[
                aws_elasticloadbalancingv2.CfnListener.ActionProperty(
                    target_group_arn=self.https_target_group.ref,
                    type="forward"
                )
            ],
            load_balancer_arn=self.alb.ref,
            port=443,
            protocol="HTTPS"
        )

    def metadata_parameter_group(self):
        return [
            {
                "Label": {
                    "default": "ALB Configuration"
                },
                "Parameters": [
                    self.certificate_arn_param.logical_id,
                    self.alb_ingress_cidr_param.logical_id
                ],
            }
        ]

    def metadata_parameter_labels(self):
        return {
            self.certificate_arn_param.logical_id: {
                "default": "ALB ACM Certificate ARN"
            },
            self.alb_ingress_cidr_param.logical_id: {
                "default": "ALB Ingress CIDR"
            }
        }
