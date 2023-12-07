# Unreleased

# 3.17.5

* Fix race condition between public routes and IGW attachment when provisioning VPC
* Fix deprecation warnings on escape characters

# 3.17.4

* Fix issue with ALB when creating new VPC introduced in 3.17.0

# 3.17.3

* adding excluded_instance_families and excluded_instance_sizes to asg
* adding parameter for create_and_update_timeout_minutes for ASG
* Fixing metadata for amazonmq stack

# 3.17.2

* Adding CORS permissions to asset bucket IAM policy

# 3.17.1

* Adding password_length argument to secret class

# 3.17.0

* Adding dependency on VPC internet gateway attachment on ALB when VPC is not given. Fixes #6

# 3.16.0

* add SesInstanceUserAccessKeySerial to allow rotation of InstanceUserAccessKey

# 3.15.0

* make asg instance types available via python

# 3.14.1

* Update descriptions of various CFN parameters
* Upgrade to v2.2.0 of OE devenv

# 3.14.0

* Update graviton instance types in asg

# 3.13.0

* Fix IAM issue with root folders with AssetsBucket
* Add `allow_open_cors` option in assets AssetsBucket
* Add `object_ownership_value` option in AssetsBucket
* Add `remove_public_access_block` option in AssetsBucket

# 3.12.0

* Move from data_volume_size to use_data_volume
* Add AsgDataVolumeSizeParam

# 3.11.0

* Adding AmazonMQ for RabbitMQ

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
