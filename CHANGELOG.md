# Unreleased

# 3.10.1

* Fixing typo in cache instance types

# 3.10.0

* Default to smallest instance type for asg
* Move to graviton for asg

# 3.9.0

* updating aurora version to 5.7.mysql_aurora.2.11.1

# 3.8.0

* fixing extra test output
* fixing ses secretvalue permissions issue
* allowing dbadmin username to be customized in DbSecret construct
* switch from launch configs to launch templates in Asg construct
* allow customization of asg health check type
* allowing default database to be customized in AuroraCluster construct
* allow customization of size of root volume
* [Apex DNS issue](https://github.com/ordinaryexperts/aws-marketplace-oe-patterns-cdk-common/issues/5)

# 3.7.0

* fixing AssetsBucket when a bucket name is provided
* Adding AuroraMysql construct

# 3.6.2

* updating asg allowed instance types

# 3.6.1

* Fixing KMS for OpenSearch Service

# 3.6.0

* Adding AssetsBucket construct

# 3.5.1

* Updating parameter labels

# 3.5.0

* OpenSearch Service construct

# 3.4.1

* Add option for additional policies on ses user

# 3.4.0

* Remove alb from dns
* SES construct
* Add option for additional policies on asg

# 3.3.0

* Remove unnecessary asg parameter from constructs

# 3.2.0

* Aurora Postgres construct
* allow customization of alb health_check_path
* ElastiCache Cluster construct

# 3.1.0

* ALB: Requiring CIDR range for AlbIngressCidr parameter
* ALB, ASG, EFS: Explicit SG egress rule

# 3.0.2

* Fixing bug with ASG parameters when singleton == True
* Fixing logical id for describe subnets lambda policy

# 3.0.1

* Fixing EFS parameter labels

# 3.0.0

* Upgrading to CDK 2.20.0
* EFS construct
* ALB construct
* DNS construct
* ASG Data Volume support
* ASG Singleton support
* ASG updates / improvements

# 2.1.0

* [PublicSubnet2NATGateway should be on subnet2](https://github.com/ordinaryexperts/aws-marketplace-oe-patterns-cdk-common/pull/4)
* ASG Construct

# 2.0.2

* Allow newer versions of CDK

# 2.0.1

* Fix consistency of labels

# 2.0.0

* Cleanup of output logical ids
* Add parameters for VPC CIDRs
* Upgrade CDK to 1.87.1
* Add NatGatewayPerSubnet parameter

# 1.4.0

* Adding Util class

# 1.3.0

* Removing unused conditions and parameters

# 1.2.0

* Adding VPC outputs
* Adding public_subnet_ids helper
* Adding CIDR Block param and cidr_ip helper

# 1.1.0

* Upgrade CDK to 1.57.0

# 1.0.0

* Initial development
