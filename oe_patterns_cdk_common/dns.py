from aws_cdk import (
    aws_route53,
    CfnOutput,
    CfnParameter
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
            description="Required: Route 53 Hosted Zone name in which a DNS record will be created by this template. Must already exist and be the domain part of the Hostname parameter, without trailing dot. E.G. 'internal.mycompany.com'"
        )
        self.route_53_hosted_zone_name_param.override_logical_id(f"{id}Route53HostedZoneName")
        self.hostname_param = CfnParameter(
            self,
            "Hostname",
            allowed_pattern="^(?!.*/).*$",
            constraint_description="Hostname should not have any forward slashes",
            description="Required: The hostname to access the service. E.G. 'app.internal.mycompany.com'. Must be within the Hosted Zone specified."
        )
        self.hostname_param.override_logical_id(f"{id}Hostname")


        #
        # OUTPUTS
        #

        self.site_url_output = CfnOutput(
            self,
            "SiteUrlOutput",
            description="The URL Endpoint",
            value="https://{}".format(self.hostname_param.value_as_string)
        )
        self.site_url_output.override_logical_id(f"{id}SiteUrlOutput")

    def add_alb(self, alb, add_wildcard=False):
        # route 53
        self.record_set = aws_route53.CfnRecordSetGroup(
            self,
            "RecordSetGroup",
            hosted_zone_name=f"{self.route_53_hosted_zone_name_param.value_as_string}.",
            comment=self.hostname_param.value_as_string,
            record_sets=[
                aws_route53.CfnRecordSetGroup.RecordSetProperty(
                    name=f"{self.hostname_param.value_as_string}.",
                    type="A",
                    alias_target=aws_route53.CfnRecordSetGroup.AliasTargetProperty(
                        dns_name=alb.alb.attr_dns_name,
                        hosted_zone_id=alb.alb.attr_canonical_hosted_zone_id
                    )
                )
            ]
        )
        self.record_set.override_logical_id(f"{self.id}RecordSetGroup")
        if add_wildcard:
            self.subdomain_record_set = aws_route53.CfnRecordSetGroup(
                self,
                "SubdomainRecordSetGroup",
                hosted_zone_name=f"{self.route_53_hosted_zone_name_param.value_as_string}.",
                comment=self.hostname_param.value_as_string,
                record_sets=[
                    aws_route53.CfnRecordSetGroup.RecordSetProperty(
                        name=f"*.{self.hostname_param.value_as_string}.",
                        type="A",
                        alias_target=aws_route53.CfnRecordSetGroup.AliasTargetProperty(
                            dns_name=alb.alb.attr_dns_name,
                            hosted_zone_id=alb.alb.attr_canonical_hosted_zone_id
                        )
                    )
                ]
            )
            self.subdomain_record_set.override_logical_id(f"{self.id}SubdomainRecordSetGroup")


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
        return self.hostname_param.value_as_string
