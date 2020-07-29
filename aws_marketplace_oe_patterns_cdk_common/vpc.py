from aws_cdk import core

class Vpc(core.Construct):

    def __init__(self, scope: core.Construct, id: str, *, prefix=None):
        super().__init__(scope, id)

        vpc_id_param = core.CfnParameter(
            self,
            "VpcId",
            default="",
            description="Optional: Specify the VPC ID. If not specified, a VPC will be created."
        )
        vpc_private_subnet_id1_param = core.CfnParameter(
            self,
            "VpcPrivateSubnetId1",
            default="",
            description="Optional: Specify Subnet ID for first private subnet."
        )
        vpc_private_subnet_id2_param = core.CfnParameter(
            self,
            "VpcPrivateSubnetId2",
            default="",
            description="Optional: Specify Subnet ID for second private subnet."
        )
        vpc_public_subnet_id1_param = core.CfnParameter(
            self,
            "VpcPublicSubnetId1",
            default="",
            description="Optional: Specify Subnet ID for first public subnet."
        )
        vpc_public_subnet_id2_param = core.CfnParameter(
            self,
            "VpcPublicSubnetId2",
            default="",
            description="Optional: Specify Subnet ID for second public subnet."
        )
        vpc_given_condition = core.CfnCondition(
            self,
            "VpcGiven",
            expression=core.Fn.condition_not(core.Fn.condition_equals(vpc_id_param.value, ""))
        )
        vpc_not_given_condition = core.CfnCondition(
            self,
            "VpcNotGiven",
            expression=core.Fn.condition_equals(vpc_id_param.value, "")
        )
        vpc = aws_ec2.CfnVPC(
            self,
            "Vpc",
            cidr_block="10.0.0.0/16",
            enable_dns_hostnames=True,
            enable_dns_support=True,
            instance_tenancy="default",
            tags=[core.CfnTag(key="Name", value="{}/Vpc".format(core.Aws.STACK_NAME))]
        )
        vpc.cfn_options.condition=vpc_not_given_condition

        vpc_igw = aws_ec2.CfnInternetGateway(
            self,
            "VpcInternetGateway",
            tags=[core.CfnTag(key="Name", value="{}/Vpc".format(core.Aws.STACK_NAME))]
        )
        vpc_igw.cfn_options.condition=vpc_not_given_condition
        vpc_igw_attachment = aws_ec2.CfnVPCGatewayAttachment(
            self,
            "VpcIGWAttachment",
            vpc_id=vpc.ref,
            internet_gateway_id=vpc_igw.ref
        )
        vpc_igw_attachment.cfn_options.condition=vpc_not_given_condition
        vpc_public_route_table = aws_ec2.CfnRouteTable(
            self,
            "VpcPublicRouteTable",
            vpc_id=vpc.ref,
            tags=[core.CfnTag(key="Name", value="{}/Vpc/PublicRouteTable".format(core.Aws.STACK_NAME))]
        )
        vpc_public_route_table.cfn_options.condition=vpc_not_given_condition
        vpc_public_default_route = aws_ec2.CfnRoute(
            self,
            "VpcPublicDefaultRoute",
            route_table_id=vpc_public_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=vpc_igw.ref
        )
        vpc_public_default_route.cfn_options.condition=vpc_not_given_condition

        vpc_public_subnet1 = aws_ec2.CfnSubnet(
            self,
            "VpcPublicSubnet1",
            cidr_block="10.0.0.0/18",
            vpc_id=vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(0, core.Fn.get_azs()),
            map_public_ip_on_launch=True,
            tags=[
                core.CfnTag(key="Name", value="{}/Vpc/PublicSubnet1".format(core.Aws.STACK_NAME))
            ]
        )
        vpc_public_subnet1.cfn_options.condition=vpc_not_given_condition
        vpc_public_subnet1_route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
            self,
            "VpcPublicSubnet1RouteTableAssociation",
            route_table_id=vpc_public_route_table.ref,
            subnet_id=vpc_public_subnet1.ref
        )
        vpc_public_subnet1_route_table_association.cfn_options.condition=vpc_not_given_condition
        vpc_public_subnet1_eip = aws_ec2.CfnEIP(
            self,
            "VpcPublicSubnet1EIP",
            domain="vpc"
        )
        vpc_public_subnet1_eip.cfn_options.condition=vpc_not_given_condition
        vpc_public_subnet1_nat_gateway = aws_ec2.CfnNatGateway(
            self,
            "VpcPublicSubnet1NATGateway",
            allocation_id=vpc_public_subnet1_eip.attr_allocation_id,
            subnet_id=vpc_public_subnet1.ref,
            tags=[core.CfnTag(key="Name", value="{}/Vpc/PublicSubnet1".format(core.Aws.STACK_NAME))]
        )
        vpc_public_subnet1_nat_gateway.cfn_options.condition=vpc_not_given_condition
        vpc_public_subnet2 = aws_ec2.CfnSubnet(
            self,
            "VpcPublicSubnet2",
            cidr_block="10.0.64.0/18",
            vpc_id=vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(1, core.Fn.get_azs()),
            map_public_ip_on_launch=True,
            tags=[
                core.CfnTag(key="Name", value="{}/Vpc/PublicSubnet2".format(core.Aws.STACK_NAME))
            ]
        )
        vpc_public_subnet2.cfn_options.condition=vpc_not_given_condition
        vpc_public_subnet2_route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
            self,
            "VpcPublicSubnet2RouteTableAssociation",
            route_table_id=vpc_public_route_table.ref,
            subnet_id=vpc_public_subnet2.ref
        )
        vpc_public_subnet2_route_table_association.cfn_options.condition=vpc_not_given_condition
        vpc_public_subnet2_eip = aws_ec2.CfnEIP(
            self,
            "VpcPublicSubnet2EIP",
            domain="vpc"
        )
        vpc_public_subnet2_eip.cfn_options.condition=vpc_not_given_condition
        vpc_public_subnet2_nat_gateway = aws_ec2.CfnNatGateway(
            self,
            "VpcPublicSubnet2NATGateway",
            allocation_id=vpc_public_subnet2_eip.attr_allocation_id,
            subnet_id=vpc_public_subnet1.ref,
            tags=[core.CfnTag(key="Name", value="{}/Vpc/PublicSubnet2".format(core.Aws.STACK_NAME))]
        )
        vpc_public_subnet2_nat_gateway.cfn_options.condition=vpc_not_given_condition

        vpc_private_subnet1 = aws_ec2.CfnSubnet(
            self,
            "VpcPrivateSubnet1",
            cidr_block="10.0.128.0/18",
            vpc_id=vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(0, core.Fn.get_azs()),
            map_public_ip_on_launch=False,
            tags=[
                core.CfnTag(key="Name", value="{}/Vpc/PrivateSubnet1".format(core.Aws.STACK_NAME))
            ]
        )
        vpc_private_subnet1.cfn_options.condition=vpc_not_given_condition
        vpc_private_subnet1_route_table = aws_ec2.CfnRouteTable(
            self,
            "VpcPrivateSubnet1RouteTable",
            vpc_id=vpc.ref,
            tags=[core.CfnTag(key="Name", value="{}/Vpc/PrivateSubnet1".format(core.Aws.STACK_NAME))]
        )
        vpc_private_subnet1_route_table.cfn_options.condition=vpc_not_given_condition
        vpc_private_subnet1_route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
            self,
            "VpcPrivateSubnet1RouteTableAssociation",
            route_table_id=vpc_private_subnet1_route_table.ref,
            subnet_id=vpc_private_subnet1.ref
        )
        vpc_private_subnet1_route_table_association.cfn_options.condition=vpc_not_given_condition
        vpc_private_subnet1_default_route = aws_ec2.CfnRoute(
            self,
            "VpcPrivateSubnet1DefaultRoute",
            route_table_id=vpc_private_subnet1_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            nat_gateway_id=vpc_public_subnet1_nat_gateway.ref
        )
        vpc_private_subnet1_default_route.cfn_options.condition=vpc_not_given_condition

        vpc_private_subnet2 = aws_ec2.CfnSubnet(
            self,
            "VpcPrivateSubnet2",
            cidr_block="10.0.192.0/18",
            vpc_id=vpc.ref,
            assign_ipv6_address_on_creation=None,
            availability_zone=core.Fn.select(1, core.Fn.get_azs()),
            map_public_ip_on_launch=False,
            tags=[
                core.CfnTag(key="Name", value="{}/Vpc/PrivateSubnet2".format(core.Aws.STACK_NAME))
            ]
        )
        vpc_private_subnet2.cfn_options.condition=vpc_not_given_condition
        vpc_private_subnet2_route_table = aws_ec2.CfnRouteTable(
            self,
            "VpcPrivateSubnet2RouteTable",
            vpc_id=vpc.ref,
            tags=[core.CfnTag(key="Name", value="{}/Vpc/PrivateSubnet2".format(core.Aws.STACK_NAME))]
        )
        vpc_private_subnet2_route_table.cfn_options.condition=vpc_not_given_condition
        vpc_private_subnet2_route_table_association = aws_ec2.CfnSubnetRouteTableAssociation(
            self,
            "VpcPrivateSubnet2RouteTableAssociation",
            route_table_id=vpc_private_subnet2_route_table.ref,
            subnet_id=vpc_private_subnet2.ref
        )
        vpc_private_subnet2_route_table_association.cfn_options.condition=vpc_not_given_condition
        vpc_private_subnet2_default_route = aws_ec2.CfnRoute(
            self,
            "VpcPrivateSubnet2DefaultRoute",
            route_table_id=vpc_private_subnet2_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            nat_gateway_id=vpc_public_subnet2_nat_gateway.ref
        )
        vpc_private_subnet2_default_route.cfn_options.condition=vpc_not_given_condition
