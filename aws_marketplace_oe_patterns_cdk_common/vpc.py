from aws_cdk import (
    aws_ec2,
    core
)

class Vpc(core.Construct):

    def __init__(self, scope: core.Construct, id: str, **props):
        super().__init__(scope, id)

        # parameters

        self.vpc_id_param = core.CfnParameter(
            self,
            "Id",
            default="",
            description="Optional: Specify the VPC ID. If not specified, a VPC will be created."
        )
        self.vpc_id_param.override_logical_id(f"{id}Id")
        self.vpc_private_subnet_id1_param = core.CfnParameter(
            self,
            "PrivateSubnetId1",
            default="",
            description="Optional: Specify Subnet ID for first private subnet."
        )
        self.vpc_private_subnet_id1_param.override_logical_id(f"{id}PrivateSubnetId1")
        self.vpc_private_subnet_id2_param = core.CfnParameter(
            self,
            "PrivateSubnetId2",
            default="",
            description="Optional: Specify Subnet ID for second private subnet."
        )
        self.vpc_private_subnet_id2_param.override_logical_id(f"{id}PrivateSubnetId2")
        self.vpc_public_subnet_id1_param = core.CfnParameter(
            self,
            "PublicSubnetId1",
            default="",
            description="Optional: Specify Subnet ID for first public subnet."
        )
        self.vpc_public_subnet_id1_param.override_logical_id(f"{id}PublicSubnetId1")
        self.vpc_public_subnet_id2_param = core.CfnParameter(
            self,
            "PublicSubnetId2",
            default="",
            description="Optional: Specify Subnet ID for second public subnet."
        )
        self.vpc_public_subnet_id2_param.override_logical_id(f"{id}PublicSubnetId2")

        # conditions

        self.vpc_given_condition = core.CfnCondition(
            self,
            "Given",
            expression=core.Fn.condition_not(core.Fn.condition_equals(self.vpc_id_param.value, ""))
        )
        self.vpc_given_condition.override_logical_id(f"{id}Given")
        self.vpc_not_given_condition = core.CfnCondition(
            self,
            "NotGiven",
            expression=core.Fn.condition_equals(self.vpc_id_param.value, "")
        )
        self.vpc_not_given_condition.override_logical_id(f"{id}NotGiven")

        # resources

        self.vpc = aws_ec2.CfnVPC(
            self,
            f"{id}",
            cidr_block="10.0.0.0/16",
            enable_dns_hostnames=True,
            enable_dns_support=True,
            instance_tenancy="default",
            tags=[core.CfnTag(key="Name", value="{}/Vpc".format(core.Aws.STACK_NAME))]
        )
        self.vpc.cfn_options.condition=self.vpc_not_given_condition
        self.vpc.override_logical_id(f"{id}")

        self.vpc_igw = aws_ec2.CfnInternetGateway(
            self,
            "InternetGateway",
            tags=[core.CfnTag(key="Name", value="{}/Vpc".format(core.Aws.STACK_NAME))]
        )
        self.vpc_igw.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_igw.override_logical_id(f"{id}InternetGateway")

        self.vpc_igw_attachment = aws_ec2.CfnVPCGatewayAttachment(
            self,
            "IGWAttachment",
            vpc_id=self.vpc.ref,
            internet_gateway_id=self.vpc_igw.ref
        )
        self.vpc_igw_attachment.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_igw_attachment.override_logical_id(f"{id}IGWAttachment")

        self.vpc_public_route_table = aws_ec2.CfnRouteTable(
            self,
            "PublicRouteTable",
            vpc_id=self.vpc.ref,
            tags=[core.CfnTag(key="Name", value="{}/Vpc/PublicRouteTable".format(core.Aws.STACK_NAME))]
        )
        self.vpc_public_route_table.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_route_table.override_logical_id(f"{id}PublicRouteTable")

        self.vpc_public_default_route = aws_ec2.CfnRoute(
            self,
            "PublicDefaultRoute",
            route_table_id=self.vpc_public_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=self.vpc_igw.ref
        )
        self.vpc_public_default_route.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_default_route.override_logical_id(f"{id}PublicDefaultRoute")

        self.vpc_public_subnet1 = aws_ec2.CfnSubnet(
            self,
            "PublicSubnet1",
            cidr_block="10.0.0.0/18",
            vpc_id=self.vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(0, core.Fn.get_azs()),
            map_public_ip_on_launch=True,
            tags=[
                core.CfnTag(key="Name", value="{}/Vpc/PublicSubnet1".format(core.Aws.STACK_NAME))
            ]
        )
        self.vpc_public_subnet1.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_subnet1.override_logical_id(f"{id}PublicSubnet1")

        self.vpc_public_subnet1_route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
            self,
            "PublicSubnet1RouteTableAssociation",
            route_table_id=self.vpc_public_route_table.ref,
            subnet_id=self.vpc_public_subnet1.ref
        )
        self.vpc_public_subnet1_route_table_association.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_subnet1_route_table_association.override_logical_id(f"{id}PublicSubnet1RouteTableAssociation")

        self.vpc_public_subnet1_eip = aws_ec2.CfnEIP(
            self,
            "PublicSubnet1EIP",
            domain="vpc"
        )
        self.vpc_public_subnet1_eip.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_subnet1_eip.override_logical_id(f"{id}PublicSubnet1EIP")

        self.vpc_public_subnet1_nat_gateway = aws_ec2.CfnNatGateway(
            self,
            "PublicSubnet1NATGateway",
            allocation_id=self.vpc_public_subnet1_eip.attr_allocation_id,
            subnet_id=self.vpc_public_subnet1.ref,
            tags=[core.CfnTag(key="Name", value="{}/Vpc/PublicSubnet1".format(core.Aws.STACK_NAME))]
        )
        self.vpc_public_subnet1_nat_gateway.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_subnet1_nat_gateway.override_logical_id(f"{id}PublicSubnet1NATGateway")

        self.vpc_public_subnet2 = aws_ec2.CfnSubnet(
            self,
            "PublicSubnet2",
            cidr_block="10.0.64.0/18",
            vpc_id=self.vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(1, core.Fn.get_azs()),
            map_public_ip_on_launch=True,
            tags=[
                core.CfnTag(key="Name", value="{}/Vpc/PublicSubnet2".format(core.Aws.STACK_NAME))
            ]
        )
        self.vpc_public_subnet2.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_subnet2.override_logical_id(f"{id}PublicSubnet2")

        self.vpc_public_subnet2_route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
            self,
            "PublicSubnet2RouteTableAssociation",
            route_table_id=self.vpc_public_route_table.ref,
            subnet_id=self.vpc_public_subnet2.ref
        )
        self.vpc_public_subnet2_route_table_association.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_subnet2_route_table_association.override_logical_id(f"{id}PublicSubnet2RouteTableAssociation")

        self.vpc_public_subnet2_eip = aws_ec2.CfnEIP(
            self,
            "PublicSubnet2EIP",
            domain="vpc"
        )
        self.vpc_public_subnet2_eip.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_subnet2_eip.override_logical_id(f"{id}PublicSubnet2EIP")

        self.vpc_public_subnet2_nat_gateway = aws_ec2.CfnNatGateway(
            self,
            "PublicSubnet2NATGateway",
            allocation_id=self.vpc_public_subnet2_eip.attr_allocation_id,
            subnet_id=self.vpc_public_subnet1.ref,
            tags=[core.CfnTag(key="Name", value="{}/Vpc/PublicSubnet2".format(core.Aws.STACK_NAME))]
        )
        self.vpc_public_subnet2_nat_gateway.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_subnet2_nat_gateway.override_logical_id(f"{id}PublicSubnet2NATGateway")

        self.vpc_private_subnet1 = aws_ec2.CfnSubnet(
            self,
            "PrivateSubnet1",
            cidr_block="10.0.128.0/18",
            vpc_id=self.vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(0, core.Fn.get_azs()),
            map_public_ip_on_launch=False,
            tags=[
                core.CfnTag(key="Name", value="{}/Vpc/PrivateSubnet1".format(core.Aws.STACK_NAME))
            ]
        )
        self.vpc_private_subnet1.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_private_subnet1.override_logical_id(f"{id}PrivateSubnet1")

        self.vpc_private_subnet1_route_table = aws_ec2.CfnRouteTable(
            self,
            "PrivateSubnet1RouteTable",
            vpc_id=self.vpc.ref,
            tags=[core.CfnTag(key="Name", value="{}/Vpc/PrivateSubnet1".format(core.Aws.STACK_NAME))]
        )
        self.vpc_private_subnet1_route_table.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_private_subnet1_route_table.override_logical_id(f"{id}PrivateSubnet1RouteTable")

        self.vpc_private_subnet1_route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
            self,
            "PrivateSubnet1RouteTableAssociation",
            route_table_id=self.vpc_private_subnet1_route_table.ref,
            subnet_id=self.vpc_private_subnet1.ref
        )
        self.vpc_private_subnet1_route_table_association.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_private_subnet1_route_table_association.override_logical_id(f"{id}PrivateSubnet1RouteTableAssociation")

        self.vpc_private_subnet1_default_route = aws_ec2.CfnRoute(
            self,
            "PrivateSubnet1DefaultRoute",
            route_table_id=self.vpc_private_subnet1_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            nat_gateway_id=self.vpc_public_subnet1_nat_gateway.ref
        )
        self.vpc_private_subnet1_default_route.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_private_subnet1_default_route.override_logical_id(f"{id}PrivateSubnet1DefaultRoute")

        self.vpc_private_subnet2 = aws_ec2.CfnSubnet(
            self,
            "PrivateSubnet2",
            cidr_block="10.0.192.0/18",
            vpc_id=self.vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(1, core.Fn.get_azs()),
            map_public_ip_on_launch=False,
            tags=[
                core.CfnTag(key="Name", value="{}/Vpc/PrivateSubnet2".format(core.Aws.STACK_NAME))
            ]
        )
        self.vpc_private_subnet2.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_private_subnet2.override_logical_id(f"{id}PrivateSubnet2")

        self.vpc_private_subnet2_route_table = aws_ec2.CfnRouteTable(
            self,
            "PrivateSubnet2RouteTable",
            vpc_id=self.vpc.ref,
            tags=[core.CfnTag(key="Name", value="{}/Vpc/PrivateSubnet2".format(core.Aws.STACK_NAME))]
        )
        self.vpc_private_subnet2_route_table.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_private_subnet2_route_table.override_logical_id(f"{id}PrivateSubnet2RouteTable")

        self.vpc_private_subnet2_route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
            self,
            "PrivateSubnet2RouteTableAssociation",
            route_table_id=self.vpc_private_subnet2_route_table.ref,
            subnet_id=self.vpc_private_subnet2.ref
        )
        self.vpc_private_subnet2_route_table_association.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_private_subnet2_route_table_association.override_logical_id(f"{id}PrivateSubnet2RouteTableAssociation")

        self.vpc_private_subnet2_default_route = aws_ec2.CfnRoute(
            self,
            "PrivateSubnet2DefaultRoute",
            route_table_id=self.vpc_private_subnet2_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            nat_gateway_id=self.vpc_public_subnet2_nat_gateway.ref
        )
        self.vpc_private_subnet2_default_route.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_private_subnet2_default_route.override_logical_id(f"{id}PrivateSubnet2DefaultRoute")

    # helpers

    def id(self):
        return core.Token.as_string(
            core.Fn.condition_if(
	        self.vpc_not_given_condition.logical_id,
                self.vpc.ref,
                self.vpc_id_param.value_as_string
            )
        )

    def subnet_ids(self):
        core.Token.as_list(
            core.Fn.condition_if(
                vpc.vpc_not_given_condition.logical_id,
                [
                    vpc.vpc_private_subnet1.ref,
                    vpc.vpc_private_subnet2.ref
                ],
                [
                    vpc.vpc_private_subnet_id1_param.value_as_string,
		    vpc.vpc_private_subnet_id2_param.value_as_string
                ]
            )
        )
