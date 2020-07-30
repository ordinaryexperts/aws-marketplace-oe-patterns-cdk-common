from aws_cdk import (
    aws_ec2,
    core
)

class Vpc(core.Construct):

    def __init__(self, scope: core.Construct, id: str, **props):
        super().__init__(scope, id)

        self.vpc_id_param = core.CfnParameter(
            self,
            "VpcId",
            default="",
            description="Optional: Specify the VPC ID. If not specified, a VPC will be created."
        )
        self.vpc_id_param.override_logical_id("VpcId")
        self.vpc_private_subnet_id1_param = core.CfnParameter(
            self,
            "VpcPrivateSubnetId1",
            default="",
            description="Optional: Specify Subnet ID for first private subnet."
        )
        self.vpc_private_subnet_id1_param.override_logical_id("VpcPrivateSubnetId1")
        self.vpc_private_subnet_id2_param = core.CfnParameter(
            self,
            "VpcPrivateSubnetId2",
            default="",
            description="Optional: Specify Subnet ID for second private subnet."
        )
        self.vpc_private_subnet_id2_param.override_logical_id("VpcPrivateSubnetId2")
        self.vpc_public_subnet_id1_param = core.CfnParameter(
            self,
            "VpcPublicSubnetId1",
            default="",
            description="Optional: Specify Subnet ID for first public subnet."
        )
        self.vpc_public_subnet_id1_param.override_logical_id("VpcPublicSubnetId1")
        self.vpc_public_subnet_id2_param = core.CfnParameter(
            self,
            "VpcPublicSubnetId2",
            default="",
            description="Optional: Specify Subnet ID for second public subnet."
        )
        self.vpc_public_subnet_id2_param.override_logical_id("VpcPublicSubnetId2")

        # conditions
        self.vpc_given_condition = core.CfnCondition(
            self,
            "VpcGiven",
            expression=core.Fn.condition_not(core.Fn.condition_equals(self.vpc_id_param.value, ""))
        )
        self.vpc_not_given_condition = core.CfnCondition(
            self,
            "VpcNotGiven",
            expression=core.Fn.condition_equals(self.vpc_id_param.value, "")
        )

        self.vpc = aws_ec2.CfnVPC(
            self,
            "Vpc",
            cidr_block="10.0.0.0/16",
            enable_dns_hostnames=True,
            enable_dns_support=True,
            instance_tenancy="default",
            tags=[core.CfnTag(key="Name", value="{}/Vpc".format(core.Aws.STACK_NAME))]
        )
        self.vpc.cfn_options.condition=self.vpc_not_given_condition
        self.vpc.override_logical_id("Vpc")

        self.vpc_igw = aws_ec2.CfnInternetGateway(
            self,
            "VpcInternetGateway",
            tags=[core.CfnTag(key="Name", value="{}/Vpc".format(core.Aws.STACK_NAME))]
        )
        self.vpc_igw.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_igw.override_logical_id("VpcInternetGateway")

        self.vpc_igw_attachment = aws_ec2.CfnVPCGatewayAttachment(
            self,
            "VpcIGWAttachment",
            vpc_id=self.vpc.ref,
            internet_gateway_id=self.vpc_igw.ref
        )
        self.vpc_igw_attachment.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_igw_attachment.overide_logical_id("VpcIGWAttachment")

        self.vpc_public_route_table = aws_ec2.CfnRouteTable(
            self,
            "VpcPublicRouteTable",
            vpc_id=self.vpc.ref,
            tags=[core.CfnTag(key="Name", value="{}/Vpc/PublicRouteTable".format(core.Aws.STACK_NAME))]
        )
        self.vpc_public_route_table.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_route_table.override_logical_id("VpcPublicRouteTable")

        self.vpc_public_default_route = aws_ec2.CfnRoute(
            self,
            "VpcPublicDefaultRoute",
            route_table_id=self.vpc_public_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=self.vpc_igw.ref
        )
        self.vpc_public_default_route.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_default_route.override_logical_id("VpcPublicDefaultRoute")

        self.vpc_public_subnet1 = aws_ec2.CfnSubnet(
            self,
            "VpcPublicSubnet1",
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
        self.vpc_public_subnet1.override_logical_id("VpcPublicSubnet1")

        self.vpc_public_subnet1_route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
            self,
            "VpcPublicSubnet1RouteTableAssociation",
            route_table_id=self.vpc_public_route_table.ref,
            subnet_id=self.vpc_public_subnet1.ref
        )
        self.vpc_public_subnet1_route_table_association.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_subnet1_route_table_association.override_logical_id("VpcPublicSubnet1RouteTableAssociation")

        self.vpc_public_subnet1_eip = aws_ec2.CfnEIP(
            self,
            "VpcPublicSubnet1EIP",
            domain="vpc"
        )
        self.vpc_public_subnet1_eip.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_subnet1_eip.override_logical_id("VpcPublicSubnet1EIP")

        self.vpc_public_subnet1_nat_gateway = aws_ec2.CfnNatGateway(
            self,
            "VpcPublicSubnet1NATGateway",
            allocation_id=self.vpc_public_subnet1_eip.attr_allocation_id,
            subnet_id=self.vpc_public_subnet1.ref,
            tags=[core.CfnTag(key="Name", value="{}/Vpc/PublicSubnet1".format(core.Aws.STACK_NAME))]
        )
        self.vpc_public_subnet1_nat_gateway.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_subnet1_nat_gateway.override_logical_id("VpcPublicSubnet1NATGateway")

        self.vpc_public_subnet2 = aws_ec2.CfnSubnet(
            self,
            "VpcPublicSubnet2",
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
        self.vpc_public_subnet2.override_logical_id("VpcPublicSubnet2")

        self.vpc_public_subnet2_route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
            self,
            "VpcPublicSubnet2RouteTableAssociation",
            route_table_id=self.vpc_public_route_table.ref,
            subnet_id=self.vpc_public_subnet2.ref
        )
        self.vpc_public_subnet2_route_table_association.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_subnet2_route_table_association.override_logical_id("VpcPublicSubnet2RouteTableAssociation")

        self.vpc_public_subnet2_eip = aws_ec2.CfnEIP(
            self,
            "VpcPublicSubnet2EIP",
            domain="vpc"
        )
        self.vpc_public_subnet2_eip.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_subnet2_eip.override_logical_id("VpcPublicSubnet2EIP")

        self.vpc_public_subnet2_nat_gateway = aws_ec2.CfnNatGateway(
            self,
            "VpcPublicSubnet2NATGateway",
            allocation_id=self.vpc_public_subnet2_eip.attr_allocation_id,
            subnet_id=self.vpc_public_subnet1.ref,
            tags=[core.CfnTag(key="Name", value="{}/Vpc/PublicSubnet2".format(core.Aws.STACK_NAME))]
        )
        self.vpc_public_subnet2_nat_gateway.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_public_subnet2_nat_gateway.override_logical_id("VpcPublicSubnet2NATGateway")

        self.vpc_private_subnet1 = aws_ec2.CfnSubnet(
            self,
            "VpcPrivateSubnet1",
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
        self.vpc_private_subnet1.override_logical_id("VpcPrivateSubnet1")

        self.vpc_private_subnet1_route_table = aws_ec2.CfnRouteTable(
            self,
            "VpcPrivateSubnet1RouteTable",
            vpc_id=self.vpc.ref,
            tags=[core.CfnTag(key="Name", value="{}/Vpc/PrivateSubnet1".format(core.Aws.STACK_NAME))]
        )
        self.vpc_private_subnet1_route_table.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_private_subnet1_route_table.override_logical_id("VpcPrivateSubnet1RouteTable")

        self.vpc_private_subnet1_route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
            self,
            "VpcPrivateSubnet1RouteTableAssociation",
            route_table_id=self.vpc_private_subnet1_route_table.ref,
            subnet_id=self.vpc_private_subnet1.ref
        )
        self.vpc_private_subnet1_route_table_association.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_private_subnet1_route_table_association.override_logical_id("VpcPublicSubnet1RouteTableAssociation")

        self.vpc_private_subnet1_default_route = aws_ec2.CfnRoute(
            self,
            "VpcPrivateSubnet1DefaultRoute",
            route_table_id=self.vpc_private_subnet1_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            nat_gateway_id=self.vpc_public_subnet1_nat_gateway.ref
        )
        self.vpc_private_subnet1_default_route.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_private_subnet1_default_route.override_logical_id("VpcPrivateSubnet1DefaultRoute")

        self.vpc_private_subnet2 = aws_ec2.CfnSubnet(
            self,
            "VpcPrivateSubnet2",
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
        self.vpc_private_subnet2.override_logical_id("VpcPrivateSubnet2")

        self.vpc_private_subnet2_route_table = aws_ec2.CfnRouteTable(
            self,
            "VpcPrivateSubnet2RouteTable",
            vpc_id=self.vpc.ref,
            tags=[core.CfnTag(key="Name", value="{}/Vpc/PrivateSubnet2".format(core.Aws.STACK_NAME))]
        )
        self.vpc_private_subnet2_route_table.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_private_subnet2_route_table.override_logical_id("VpcPrivateSubnet2RouteTable")

        self.vpc_private_subnet2_route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
            self,
            "VpcPrivateSubnet2RouteTableAssociation",
            route_table_id=self.vpc_private_subnet2_route_table.ref,
            subnet_id=self.vpc_private_subnet2.ref
        )
        self.vpc_private_subnet2_route_table_association.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_private_subnet2_route_table_association.override_logical_id("VpcPrivateSubnet2RouteTableAssociation")

        self.vpc_private_subnet2_default_route = aws_ec2.CfnRoute(
            self,
            "VpcPrivateSubnet2DefaultRoute",
            route_table_id=self.vpc_private_subnet2_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            nat_gateway_id=self.vpc_public_subnet2_nat_gateway.ref
        )
        self.vpc_private_subnet2_default_route.cfn_options.condition=self.vpc_not_given_condition
        self.vpc_private_subnet2_default_route.override_logical_id("VpcPrivateSubnet2DefaultRoute")
