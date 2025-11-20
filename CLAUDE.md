# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains reusable AWS CDK constructs for building AWS Marketplace patterns. It's a Python library that provides common infrastructure components (VPC, ASG, ALB, RDS Aurora, ElastiCache, OpenSearch, etc.) used across multiple AWS Marketplace pattern repositories.

## Development Environment

All development happens inside Docker containers to ensure consistency:

```bash
# Build the development environment
make build

# Rebuild from scratch (no cache)
make rebuild

# Start interactive bash shell
make bash

# Start Python REPL
make python

# Run all tests
make test
```

The Docker environment is based on `ordinaryexperts/aws-marketplace-patterns-devenv:2.5.5` and includes AWS CDK 2.20.0 and pytest.

## Testing

Tests are in `oe_patterns_cdk_common/tests/` directory. Each construct has a corresponding test file (e.g., `test_vpc.py`, `test_asg.py`).

Run tests with:
```bash
make test
```

## Architecture

### Core Constructs

The library provides CDK constructs that follow a consistent pattern:

1. **VPC (`vpc.py`)**: Creates or uses existing VPC with public/private subnets, NAT gateways, and Internet gateways. Supports both "bring your own VPC" and "create new VPC" patterns via CloudFormation parameters.

2. **ASG (`asg.py`)**: Auto Scaling Group with:
   - Support for both Graviton (ARM) and x86 instance types
   - Optional singleton mode (single instance)
   - Data volume attachment
   - Backup plan integration
   - CloudWatch alarms
   - User data customization
   - Instance profile with configurable IAM policies

3. **AppDeployPipeline (`app_deploy_pipeline.py`)**: CodePipeline-based deployment pipeline with:
   - S3 source stage
   - CodeBuild for building
   - CodeDeploy for deployment to ASG
   - Optional demo initialization
   - SNS notifications

4. **ALB (`alb.py`)**: Application Load Balancer with target groups and listeners

5. **Database Constructs**:
   - `aurora_cluster.py`: RDS Aurora clusters with multi-AZ support
   - `elasticache_cluster.py`: Redis/Memcached clusters
   - `db_secret.py`: Secrets Manager for database credentials

6. **Storage**:
   - `efs.py`: Elastic File System with mount targets
   - `assets_bucket.py`: S3 buckets for static assets

7. **Other Services**:
   - `amazonmq.py`: Amazon MQ broker
   - `open_search_service.py`: OpenSearch Service domain
   - `ses.py`: Simple Email Service configuration
   - `dns.py`: Route53 DNS records
   - `secret.py`: Secrets Manager secrets
   - `notification_topic.py`: SNS topics for notifications

### Design Patterns

**CloudFormation Parameter Pattern**: All constructs expose CloudFormation parameters (using `CfnParameter`) to allow runtime configuration. Parameters use the construct ID as a prefix (e.g., `VpcId`, `VpcCidr`).

**Conditional Resource Creation**: Constructs use `CfnCondition` extensively to conditionally create resources based on parameter values. For example, VPC creates resources only if no VPC ID is provided.

**Logical ID Override**: All resources use `override_logical_id()` to ensure stable CloudFormation logical IDs that don't change when CDK app is modified.

**Resource Tagging**: Resources are tagged with `Name` tags that include the stack name using `Aws.STACK_NAME`.

**cfn_lint Suppressions**: Constructs may include a `cfn_lint_suppressions()` method that returns a list of CloudFormation linting rule IDs to suppress (e.g., `W1019` for unused variables that may be used by downstream patterns).

### Utility Functions

`util.py` provides helper functions:
- `append_stack_uuid(name)`: Appends a unique ID from the stack ID to resource names
- `local_path(relative_path)`: Resolves paths relative to the package directory
- `add_sg_ingress(resource, sg)`: Adds security group ingress rules

## Key Implementation Details

### Instance Type Selection (ASG)

The ASG construct maintains two lists of allowed instance types:
- `GRAVITON_INSTANCE_TYPES`: ARM-based instances (t4g, c7g, m7g, r7g, etc.)
- `STANDARD_INSTANCE_TYPES`: x86 instances (t2, t3, c5, m5, r5, etc.)

You can filter these using `excluded_instance_families` and `excluded_instance_sizes` parameters.

### VPC Parameter Pattern

VPC uses a "bring your own" pattern where users can optionally provide:
- VPC ID and subnet IDs (to use existing resources)
- OR CIDR blocks (to create new resources)

The construct uses conditions to create resources only when not provided.

### User Data Handling (ASG)

User data can be customized via `user_data_contents` parameter. The construct replaces variables in the user data using a dictionary passed via `user_data_variables`.

## Common Workflows

When adding new features to constructs:
1. Add CloudFormation parameters for any configurable values
2. Use conditions for optional resource creation
3. Override logical IDs for stable CloudFormation resource names
4. Add tests to the corresponding test file
5. If adding variables that may not be used by all patterns, add cfn-lint suppressions

When creating new constructs:
1. Follow the existing patterns for parameter naming (use construct ID as prefix)
2. Support both "bring your own" and "create new" patterns where applicable
3. Use `CfnCondition` for conditional resource creation
4. Create a corresponding test file in `oe_patterns_cdk_common/tests/`
