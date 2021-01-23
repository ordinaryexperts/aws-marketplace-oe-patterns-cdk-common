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
$ vim cdk/wordpress/wordpress_stack.py # update as directed by the output of ami-ec2-build
$ make synth-to-file
$ avl oe-patterns-prod-dylan
(take dist/template.yaml and test it manually in console of OE Patterns Prod account)
```

4. Scan AMI in AWS Marketplace Portal

```
$ xdg-open https://aws.amazon.com/marketplace/management/manage-products/#/manage-amis.unshared
(go to Assets -> Amazon Machine Image, then select the latest AMI and click 'Share')
(monitor the result of the scan and make fixes, repeat as necessary)
```

5. Generate Product Load Form for AWS Marketplace

```
$ wget https://s3.amazonaws.com/awsmp-loadforms/ProductDataLoad-Current.xlsx
(open in Excel, copy header line, paste into scripts/gen-plf-column-headers.txt)
$ ave oe-patterns-prod-dylan make TEMPLATE_VERSION=1.0.0 AMI_ID=ami-xxxxxxxxxxxxxxxxx gen-plf
(this may take more than an hour to complete due to the AWS pricing calculations...)
(sometimes you have to run it more than once...)
(it also helps to quit anything else running on your laptop while it is running...)
```

The above will generate a `plf.csv`. Open the default Product Load Form downloaded above, remove the default content, and paste in the row from `plf.csv`.

6. Publish template to s3 bucket (in OE Patterns dev account)

```
$ ave oe-patterns-dev make TEMPLATE_VERSION=1.0.0 publish
```

7. Upload Excel file to AWS Management Portal

```
$ wget https://aws.amazon.com/marketplace/management/product-load
```


8. Finish release branch

```
$ git flow release finish 1.0.0
$ git checkout main
$ git push
$ git push --tags
$ git checkout develop
```

9. Generate and copy dev AMI for taskcat tests

```
$ ave oe-patterns-dev make ami-ec2-build
$ ave oe-patterns-dev make AMI_ID=ami-xxxxxxxxxxxxxxxxx ami-ec2-copy
$ git add .
$ git commit -m "Updated AMI for taskcat testing post 1.0.0 release"
$ git push
```
