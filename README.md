# aws-marketplace-oe-patterns-cdk-common

## Common Processes

*Release a new version*

1. Create release branch

```
$ git flow release start 1.0.0
$ vim CHANGELOG.md
$ git add CHANGELOG.md
```

2. Build AMI in oe-patterns-prod AWS account:

```
$ ave oe-patterns-prod make TEMPLATE_VERSION=1.0.0 ami-ec2-build
```

3. Update CDK with AMI ID, synth, and test:

```
$ vim cdk/wordpress/wordpress_stack.py # update the AMI info as directed by the output of ami-ec2-build
$ make synth-to-file
(now take file in dist/template.yaml and test it manually in console of the OE Patterns Prod account)
```

4. Scan AMI in AWS Marketplace Portal

```
$ avl oe-patterns-prod-dylan
$ xdg-open https://aws.amazon.com/marketplace/management/manage-products/#/manage-amis.unshared
(go to Assets -> Amazon Machine Image, then select the latest AMI and click 'Share')
(monitor the result of the scan and make fixes, repeat as necessary)
```

5. Submit Product Load Form to AWS Marketplace

```
$ wget https://s3.amazonaws.com/awsmp-loadforms/ProductDataLoad-Current.xlsx
```
