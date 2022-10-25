from aws_cdk import (
    aws_route53,
    CfnCondition,
    CfnOutput,
    CfnParameter,
    Fn,
    Token
)

from constructs import Construct

class Dns(Construct):

    def __init__(
            self,
            scope: Construct,
            id: str,
            **props):
        super().__init__(scope, id, **props)

        #
        # PARAMETERS
        #

        self.id = id
        self.route_53_hosted_zone_name_param = CfnParameter(
            self,
            "Route53HostedZoneName",
            default="",
            description="Optional: Route 53 Hosted Zone name in which a DNS record will be created by this template. Must already exist and be the domain part of the Hostname parameter, without trailing dot. E.G. 'internal.mycompany.com'"
        )
        self.route_53_hosted_zone_name_param.override_logical_id(f"{id}Route53HostedZoneName")
        self.hostname_param = CfnParameter(
            self,
            "Hostname",
            allowed_pattern="^(?!.*/).*$",
            constraint_description="Hostname should not have any forward slashes",
            default="",
            description="Optional: The hostname to access the service. E.G. 'app.internal.mycompany.com'"
        )
        self.hostname_param.override_logical_id(f"{id}Hostname")
        self.route_53_hosted_zone_name_exists_condition = CfnCondition(
            self,
            "Route53HostedZoneNameExists",
            expression=Fn.condition_not(Fn.condition_equals(self.route_53_hosted_zone_name_param.value, ""))
        )
        self.route_53_hosted_zone_name_exists_condition.override_logical_id(f"{id}Route53HostedZoneNameExists")
        self.hostname_exists_condition = CfnCondition(
            self,
            "HostnameExists",
            expression=Fn.condition_not(Fn.condition_equals(self.hostname_param.value, ""))
        )
        self.hostname_exists_condition.override_logical_id(f"{id}HostnameExists")

    def add_alb(self, alb):
        # route 53
        self.record_set = aws_route53.CfnRecordSet(
            self,
            "RecordSet",
            hosted_zone_name=f"{self.route_53_hosted_zone_name_param.value_as_string}.",
            name=self.hostname_param.value_as_string,
            resource_records=[ alb.alb.attr_dns_name ],
            type="CNAME"
        )
        self.record_set.override_logical_id(f"{self.id}RecordSet")
        # https://github.com/aws/aws-cdk/issues/8431
        self.record_set.add_property_override("TTL", 60)
        self.record_set.cfn_options.condition = self.route_53_hosted_zone_name_exists_condition
        self.site_url_output = CfnOutput(
            self,
            "SiteUrlOutput",
            description="The URL Endpoint",
            value=Token.as_string(
                Fn.condition_if(
                self.hostname_exists_condition.logical_id,
                "https://{}".format(self.hostname_param.value_as_string),
                "https://{}".format(alb.alb.attr_dns_name)
            ))
        )
        self.site_url_output.override_logical_id(f"{self.id}SiteUrlOutput")

    def metadata_parameter_group(self):
        return [
            {
                "Label": {
                    "default": "DNS Configuration"
                },
                "Parameters": [
                    self.route_53_hosted_zone_name_param.logical_id,
                    self.hostname_param.logical_id
                ],
            }
        ]

    def metadata_parameter_labels(self):
        return {
            self.route_53_hosted_zone_name_param.logical_id: {
                "default": "DNS Route 53 Hosted Zone Name"
            },
            self.hostname_param.logical_id: {
                "default": "DNS Hostname"
            }
        }

    def hostname(self, alb=None):
        if alb:
            return Token.as_string(
                Fn.condition_if(
                    self.hostname_exists_condition.logical_id,
                    self.hostname_param.value_as_string,
                    alb.alb.attr_dns_name
                )
            )
        else:
            return self.hostname_param.value_as_string
