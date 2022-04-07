from aws_cdk import (
    aws_ec2,
    core
)

class Vpc(core.Construct):

    def __init__(self, scope: core.Construct, id: str, **props):
        super().__init__(scope, id)

        #
        # PARAMETERS
        #

        self.id_param = core.CfnParameter(
            self,
            "Id",
            default="",
            description="Optional: Specify the VPC ID. If not specified, a VPC will be created."
        )
        self.id_param.override_logical_id(f"{id}Id")
        self.cidr_param = core.CfnParameter(
            self,
            "Cidr",
            allowed_pattern="^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/(1[6-9]|2[0-8]))$",
            default="10.0.0.0/16",
            description="Optional: VPC IPv4 CIDR block if no VPC provided."
        )
        self.cidr_param.override_logical_id(f"{id}Cidr")

        self.nat_gateway_per_subnet_param = core.CfnParameter(
            self,
            "NatGatewayPerSubnet",
            allowed_values=[ "true", "false" ],
            default="false",
            description="Optional: Set to 'true' to provision a NAT Gateway in each public subnet for AZ HA."
        )
        self.nat_gateway_per_subnet_param.override_logical_id(f"{id}NatGatewayPerSubnet")

        self.private_subnet1_id_param = core.CfnParameter(
            self,
            "PrivateSubnet1Id",
            default="",
            description="Optional: Specify Subnet ID for private subnet 1."
        )
        self.private_subnet1_id_param.override_logical_id(f"{id}PrivateSubnet1Id")
        self.private_subnet1_cidr_param = core.CfnParameter(
            self,
            "PrivateSubnet1Cidr",
            allowed_pattern="^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/(1[6-9]|2[0-8]))$",
            default="10.0.128.0/18",
            description="Optional: VPC IPv4 CIDR block of private subnet 1 if no VPC provided."
        )
        self.private_subnet1_cidr_param.override_logical_id(f"{id}PrivateSubnet1Cidr")

        self.private_subnet2_id_param = core.CfnParameter(
            self,
            "PrivateSubnet2Id",
            default="",
            description="Optional: Specify Subnet ID for private subnet 2."
        )
        self.private_subnet2_id_param.override_logical_id(f"{id}PrivateSubnet2Id")
        self.private_subnet2_cidr_param = core.CfnParameter(
            self,
            "PrivateSubnet2Cidr",
            allowed_pattern="^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/(1[6-9]|2[0-8]))$",
            default="10.0.192.0/18",
            description="Optional: VPC IPv4 CIDR block of private subnet 2 if no VPC provided."
        )
        self.private_subnet2_cidr_param.override_logical_id(f"{id}PrivateSubnet2Cidr")

        self.public_subnet1_id_param = core.CfnParameter(
            self,
            "PublicSubnetId1",
            default="",
            description="Optional: Specify Subnet ID for public subnet 1."
        )
        self.public_subnet1_id_param.override_logical_id(f"{id}PublicSubnet1Id")
        self.public_subnet1_cidr_param = core.CfnParameter(
            self,
            "PublicSubnet1Cidr",
            allowed_pattern="^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/(1[6-9]|2[0-8]))$",
            default="10.0.0.0/18",
            description="Optional: VPC IPv4 CIDR block of public subnet 1 if no VPC provided."
        )
        self.public_subnet1_cidr_param.override_logical_id(f"{id}PublicSubnet1Cidr")

        self.public_subnet2_id_param = core.CfnParameter(
            self,
            "PublicSubnet2Id",
            default="",
            description="Optional: Specify Subnet ID for public subnet 2."
        )
        self.public_subnet2_id_param.override_logical_id(f"{id}PublicSubnet2Id")
        self.public_subnet2_cidr_param = core.CfnParameter(
            self,
            "PublicSubnet2Cidr",
            default="10.0.64.0/18",
            description="Optional: VPC IPv4 CIDR block of public subnet 2 if no VPC provided."
        )
        self.public_subnet2_cidr_param.override_logical_id(f"{id}PublicSubnet2Cidr")

        #
        # CONDITIONS
        #

        self.not_given_condition = core.CfnCondition(
            self,
            "NotGiven",
            expression=core.Fn.condition_equals(self.id_param.value, "")
        )
        self.not_given_condition.override_logical_id(f"{id}NotGiven")

        self.not_given_and_nat_gateway_per_subnet_condition = core.CfnCondition(
            self,
            "NotGivenAndNatGatewayPerSubnetCondition",
            expression=core.Fn.condition_and(
                core.Fn.condition_equals(self.id_param.value, ""),
                core.Fn.condition_equals(self.nat_gateway_per_subnet_param.value, "true")
            )
        )
        self.not_given_and_nat_gateway_per_subnet_condition.override_logical_id(f"{id}NotGivenAndNatGatewayPerSubnet")

        #
        # RESOURCES
        #

        self.vpc = aws_ec2.CfnVPC(
            self,
            f"{id}",
            cidr_block=self.cidr_param.value_as_string,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            instance_tenancy="default",
            tags=[core.CfnTag(key="Name", value=f"{core.Aws.STACK_NAME}/{id}")]
        )
        self.vpc.cfn_options.condition=self.not_given_condition
        self.vpc.override_logical_id(f"{id}")

        self.igw = aws_ec2.CfnInternetGateway(
            self,
            "InternetGateway",
            tags=[core.CfnTag(key="Name", value=f"{core.Aws.STACK_NAME}/{id}")]
        )
        self.igw.cfn_options.condition=self.not_given_condition
        self.igw.override_logical_id(f"{id}InternetGateway")

        self.igw_attachment = aws_ec2.CfnVPCGatewayAttachment(
            self,
            "IGWAttachment",
            vpc_id=self.vpc.ref,
            internet_gateway_id=self.igw.ref
        )
        self.igw_attachment.cfn_options.condition=self.not_given_condition
        self.igw_attachment.override_logical_id(f"{id}IGWAttachment")

        self.public_route_table = aws_ec2.CfnRouteTable(
            self,
            "PublicRouteTable",
            vpc_id=self.vpc.ref,
            tags=[core.CfnTag(key="Name", value=f"{core.Aws.STACK_NAME}/{id}/PublicRouteTable")]
        )
        self.public_route_table.cfn_options.condition=self.not_given_condition
        self.public_route_table.override_logical_id(f"{id}PublicRouteTable")

        self.public_default_route = aws_ec2.CfnRoute(
            self,
            "PublicDefaultRoute",
            route_table_id=self.public_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=self.igw.ref
        )
        self.public_default_route.cfn_options.condition=self.not_given_condition
        self.public_default_route.override_logical_id(f"{id}PublicDefaultRoute")

        self.public_subnet1 = aws_ec2.CfnSubnet(
            self,
            "PublicSubnet1",
            cidr_block=self.public_subnet1_cidr_param.value_as_string,
            vpc_id=self.vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(0, core.Fn.get_azs()),
            map_public_ip_on_launch=True,
            tags=[
                core.CfnTag(key="Name", value=f"{core.Aws.STACK_NAME}/{id}/PublicSubnet1")
            ]
        )
        self.public_subnet1.cfn_options.condition=self.not_given_condition
        self.public_subnet1.override_logical_id(f"{id}PublicSubnet1")

        self.public_subnet1_route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
            self,
            "PublicSubnet1RouteTableAssociation",
            route_table_id=self.public_route_table.ref,
            subnet_id=self.public_subnet1.ref
        )
        self.public_subnet1_route_table_association.cfn_options.condition=self.not_given_condition
        self.public_subnet1_route_table_association.override_logical_id(f"{id}PublicSubnet1RouteTableAssociation")

        self.public_subnet1_eip = aws_ec2.CfnEIP(
            self,
            "PublicSubnet1EIP",
            domain="vpc"
        )
        self.public_subnet1_eip.cfn_options.condition=self.not_given_condition
        self.public_subnet1_eip.override_logical_id(f"{id}PublicSubnet1EIP")

        self.public_subnet1_nat_gateway = aws_ec2.CfnNatGateway(
            self,
            "PublicSubnet1NATGateway",
            allocation_id=self.public_subnet1_eip.attr_allocation_id,
            subnet_id=self.public_subnet1.ref,
            tags=[core.CfnTag(key="Name", value=f"{core.Aws.STACK_NAME}/{id}/PublicSubnet1")]
        )
        self.public_subnet1_nat_gateway.cfn_options.condition=self.not_given_condition
        self.public_subnet1_nat_gateway.override_logical_id(f"{id}PublicSubnet1NATGateway")

        self.public_subnet2 = aws_ec2.CfnSubnet(
            self,
            "PublicSubnet2",
            cidr_block=self.public_subnet2_cidr_param.value_as_string,
            vpc_id=self.vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(1, core.Fn.get_azs()),
            map_public_ip_on_launch=True,
            tags=[
                core.CfnTag(key="Name", value=f"{core.Aws.STACK_NAME}/{id}/PublicSubnet2")
            ]
        )
        self.public_subnet2.cfn_options.condition=self.not_given_condition
        self.public_subnet2.override_logical_id(f"{id}PublicSubnet2")

        self.public_subnet2_route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
            self,
            "PublicSubnet2RouteTableAssociation",
            route_table_id=self.public_route_table.ref,
            subnet_id=self.public_subnet2.ref
        )
        self.public_subnet2_route_table_association.cfn_options.condition=self.not_given_condition
        self.public_subnet2_route_table_association.override_logical_id(f"{id}PublicSubnet2RouteTableAssociation")

        self.public_subnet2_eip = aws_ec2.CfnEIP(
            self,
            "PublicSubnet2EIP",
            domain="vpc"
        )
        self.public_subnet2_eip.cfn_options.condition=self.not_given_and_nat_gateway_per_subnet_condition
        self.public_subnet2_eip.override_logical_id(f"{id}PublicSubnet2EIP")

        self.public_subnet2_nat_gateway = aws_ec2.CfnNatGateway(
            self,
            "PublicSubnet2NATGateway",
            allocation_id=self.public_subnet2_eip.attr_allocation_id,
            subnet_id=self.public_subnet2.ref,
            tags=[core.CfnTag(key="Name", value=f"{core.Aws.STACK_NAME}/{id}/PublicSubnet2")]
        )
        self.public_subnet2_nat_gateway.cfn_options.condition=self.not_given_and_nat_gateway_per_subnet_condition
        self.public_subnet2_nat_gateway.override_logical_id(f"{id}PublicSubnet2NATGateway")

        self.private_subnet1 = aws_ec2.CfnSubnet(
            self,
            "PrivateSubnet1",
            cidr_block=self.private_subnet1_cidr_param.value_as_string,
            vpc_id=self.vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(0, core.Fn.get_azs()),
            map_public_ip_on_launch=False,
            tags=[
                core.CfnTag(key="Name", value=f"{core.Aws.STACK_NAME}/{id}/PrivateSubnet1")
            ]
        )
        self.private_subnet1.cfn_options.condition=self.not_given_condition
        self.private_subnet1.override_logical_id(f"{id}PrivateSubnet1")

        self.private_subnet1_route_table = aws_ec2.CfnRouteTable(
            self,
            "PrivateSubnet1RouteTable",
            vpc_id=self.vpc.ref,
            tags=[core.CfnTag(key="Name", value=f"{core.Aws.STACK_NAME}/{id}/PrivateSubnet1")]
        )
        self.private_subnet1_route_table.cfn_options.condition=self.not_given_condition
        self.private_subnet1_route_table.override_logical_id(f"{id}PrivateSubnet1RouteTable")

        self.private_subnet1_route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
            self,
            "PrivateSubnet1RouteTableAssociation",
            route_table_id=self.private_subnet1_route_table.ref,
            subnet_id=self.private_subnet1.ref
        )
        self.private_subnet1_route_table_association.cfn_options.condition=self.not_given_condition
        self.private_subnet1_route_table_association.override_logical_id(f"{id}PrivateSubnet1RouteTableAssociation")

        self.private_subnet1_default_route = aws_ec2.CfnRoute(
            self,
            "PrivateSubnet1DefaultRoute",
            route_table_id=self.private_subnet1_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            nat_gateway_id=self.public_subnet1_nat_gateway.ref
        )
        self.private_subnet1_default_route.cfn_options.condition=self.not_given_condition
        self.private_subnet1_default_route.override_logical_id(f"{id}PrivateSubnet1DefaultRoute")

        self.private_subnet2 = aws_ec2.CfnSubnet(
            self,
            "PrivateSubnet2",
            cidr_block=self.private_subnet2_cidr_param.value_as_string,
            vpc_id=self.vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(1, core.Fn.get_azs()),
            map_public_ip_on_launch=False,
            tags=[
                core.CfnTag(key="Name", value=f"{core.Aws.STACK_NAME}/{id}/PrivateSubnet2")
            ]
        )
        self.private_subnet2.cfn_options.condition=self.not_given_condition
        self.private_subnet2.override_logical_id(f"{id}PrivateSubnet2")

        self.private_subnet2_route_table = aws_ec2.CfnRouteTable(
            self,
            "PrivateSubnet2RouteTable",
            vpc_id=self.vpc.ref,
            tags=[core.CfnTag(key="Name", value=f"{core.Aws.STACK_NAME}/{id}/PrivateSubnet2")]
        )
        self.private_subnet2_route_table.cfn_options.condition=self.not_given_condition
        self.private_subnet2_route_table.override_logical_id(f"{id}PrivateSubnet2RouteTable")

        self.private_subnet2_route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
            self,
            "PrivateSubnet2RouteTableAssociation",
            route_table_id=self.private_subnet2_route_table.ref,
            subnet_id=self.private_subnet2.ref
        )
        self.private_subnet2_route_table_association.cfn_options.condition=self.not_given_condition
        self.private_subnet2_route_table_association.override_logical_id(f"{id}PrivateSubnet2RouteTableAssociation")

        self.private_subnet2_default_route = aws_ec2.CfnRoute(
            self,
            "PrivateSubnet2DefaultRoute",
            route_table_id=self.private_subnet2_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            nat_gateway_id=core.Token.as_string(
                core.Fn.condition_if(
                    self.not_given_and_nat_gateway_per_subnet_condition.logical_id,
                    self.public_subnet2_nat_gateway.ref,
                    self.public_subnet1_nat_gateway.ref
                )
            )
        )
        self.private_subnet2_default_route.cfn_options.condition=self.not_given_condition
        self.private_subnet2_default_route.override_logical_id(f"{id}PrivateSubnet2DefaultRoute")

        #
        # OUTPUTS
        #

        self.id_output = core.CfnOutput(
            self,
            "IdOutput",
            description="The ID of the VPC.",
            value=self.id()
        )
        self.id_output.override_logical_id(f"{id}IdOutput")
        self.private_subnet1_id_output = core.CfnOutput(
            self,
            "PrivateSubnet1IdOutput",
            description="The ID of the first private VPC subnet.",
            value=self.private_subnet1_id()
        )
        self.private_subnet1_id_output.override_logical_id(f"{id}PrivateSubnet1IdOutput")
        self.private_subnet2_id_output = core.CfnOutput(
            self,
            "PrivateSubnet2IdOutput",
            description="The ID of the second private VPC subnet.",
            value=self.private_subnet2_id()
        )
        self.private_subnet2_id_output.override_logical_id(f"{id}PrivateSubnet2IdOutput")
        self.public_subnet1_id_output = core.CfnOutput(
            self,
            "PublicSubnet1IdOutput",
            description="The ID of the first public VPC subnet.",
            value=self.public_subnet1_id()
        )
        self.public_subnet1_id_output.override_logical_id(f"{id}PublicSubnet1IdOutput")
        self.public_subnet2_id_output = core.CfnOutput(
            self,
            "PublicSubnet2IdOutput",
            description="The ID of the second public VPC subnet.",
            value=self.public_subnet2_id()
        )
        self.public_subnet2_id_output.override_logical_id(f"{id}PublicSubnet2IdOutput")

    #
    # HELPERS
    #

    def id(self):
        return core.Token.as_string(
            core.Fn.condition_if(
                self.not_given_condition.logical_id,
                self.vpc.ref,
                self.id_param.value_as_string
            )
        )

    def metadata_parameter_group(self):
        return [
            {
                "Label": {
                    "default": "VPC: Use Existing"
                },
                "Parameters": [
                    self.id_param.logical_id,
                    self.private_subnet1_id_param.logical_id,
                    self.private_subnet2_id_param.logical_id,
                    self.public_subnet1_id_param.logical_id,
                    self.public_subnet2_id_param.logical_id
                ],
            },
            {
                "Label": {
                    "default": "VPC: Create New"
                },
                "Parameters": [
                    self.cidr_param.logical_id,
                    self.nat_gateway_per_subnet_param.logical_id,
                    self.private_subnet1_cidr_param.logical_id,
                    self.private_subnet2_cidr_param.logical_id,
                    self.public_subnet1_cidr_param.logical_id,
                    self.public_subnet2_cidr_param.logical_id
                ]
            }
        ]

    def metadata_parameter_labels(self):
        return {
            self.cidr_param.logical_id: {
                "default": "VPC IPv4 CIDR"
            },
            self.id_param.logical_id: {
                "default": "VPC ID"
            },
            self.nat_gateway_per_subnet_param.logical_id: {
                "default": "Provision NAT Gateways Per Public Subnet (for HA but with higher cost)"
            },
            self.private_subnet1_cidr_param.logical_id: {
                "default": "Private Subnet 1 IPv4 CIDR"
            },
            self.private_subnet1_id_param.logical_id: {
                "default": "Private Subnet 1 ID"
            },
            self.private_subnet2_cidr_param.logical_id: {
                "default": "Private Subnet 2 IPv4 CIDR"
            },
            self.private_subnet2_id_param.logical_id: {
                "default": "Private Subnet 2 ID"
            },
            self.public_subnet1_id_param.logical_id: {
                "default": "Public Subnet 1 ID"
            },
            self.public_subnet1_cidr_param.logical_id: {
                "default": "Public Subnet 1 IPv4 CIDR"
            },
            self.public_subnet2_id_param.logical_id: {
                "default": "Public Subnet 2 ID"
            },
            self.public_subnet2_cidr_param.logical_id: {
                "default": "Public Subnet 2 IPv4 CIDR"
            }
        }

    def private_subnet1_id(self):
        return core.Token.as_string(
            core.Fn.condition_if(
                self.not_given_condition.logical_id,
                self.private_subnet1.ref,
                self.private_subnet1_id_param.value_as_string
            )
        )

    def private_subnet2_id(self):
        return core.Token.as_string(
            core.Fn.condition_if(
                self.not_given_condition.logical_id,
                self.private_subnet2.ref,
                self.private_subnet2_id_param.value_as_string
            )
        )

    def private_subnet_ids(self):
        return core.Token.as_list(
            core.Fn.condition_if(
                self.not_given_condition.logical_id,
                [
                    self.private_subnet1.ref,
                    self.private_subnet2.ref
                ],
                [
                    self.private_subnet1_id_param.value_as_string,
                    self.private_subnet2_id_param.value_as_string
                ]
            )
        )

    def public_subnet1_id(self):
        return core.Token.as_string(
            core.Fn.condition_if(
                self.not_given_condition.logical_id,
                self.public_subnet1.ref,
                self.public_subnet1_id_param.value_as_string
            )
        )

    def public_subnet2_id(self):
        return core.Token.as_string(
            core.Fn.condition_if(
                self.not_given_condition.logical_id,
                self.public_subnet2.ref,
                self.public_subnet2_id_param.value_as_string
            )
        )

    def public_subnet_ids(self):
        return core.Token.as_list(
            core.Fn.condition_if(
                self.not_given_condition.logical_id,
                [
                    self.public_subnet1.ref,
                    self.public_subnet2.ref
                ],
                [
                    self.public_subnet1_id_param.value_as_string,
                    self.public_subnet2_id_param.value_as_string
                ]
            )
        )
