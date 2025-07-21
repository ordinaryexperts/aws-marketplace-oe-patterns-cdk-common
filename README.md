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
$ export TEMPLATE_VERSION=x.y.z
$ ave oe-patterns-prod make TEMPLATE_VERSION=$TEMPLATE_VERSION ami-ec2-build
$ export AMI_ID=[ami_id_from_above]
```

3. Update CDK with AMI ID, synth, and test:

```
$ vim cdk/[app]/[app]_stack.py # update AMI id and name
$ make synth-to-file
$ avl oe-patterns-prod-dylan
(take dist/template.yaml and test it manually in console of OE Patterns Prod account)
$ git add cdk
$ git ci -m "Updated AMI"
```

4. Scan AMI in AWS Marketplace Portal

```
$ xdg-open https://aws.amazon.com/marketplace/management/manage-products/#/share
(go to Assets -> Amazon Machine Image, then select the latest AMI and click 'Share')
Role: arn:aws:iam::879777583535:role/AWSMarketplaceAMIScanning
(monitor the result of the scan and make fixes, repeat as necessary)
```

5. Generate Product Load Form for AWS Marketplace

If this is the first version to be submitted:

```
$ wget https://s3.amazonaws.com/awsmp-loadforms/ProductDataLoad-Current.xlsx
```

If the product is already published, go to 'Products -> Server', then select the product, and click the `Download product load form` button. Copy the downloaded xlsx file to `plf.xlsx` in the root folder.

Then:

```
$ ave oe-patterns-prod-dylan make TEMPLATE_VERSION=$TEMPLATE_VERSION AMI_ID=$AMI_ID plf
(this may take a while to complete due to the AWS pricing calculations...)
```

The above will generate a `plf-[version]--[datetime].xlsx`, which we will upload in step 7.

6. Publish template to s3 bucket (in OE Patterns dev account)

```
$ ave oe-patterns-dev make TEMPLATE_VERSION=$TEMPLATE_VERSION publish
```

7. Upload Excel file to AWS Management Portal

```
$ xdg-open https://aws.amazon.com/marketplace/management/product-load
```


8. Wait for AWS to update product / make requested changes on release branch

9. Finish release branch

```
$ git ci -m "$TEMPLATE_VERSION updates"
$ git flow release finish $TEMPLATE_VERSION
$ git checkout main
$ git push
$ git push --tags
$ git checkout develop
```

10. Generate and copy dev AMI for taskcat tests

```
$ ave oe-patterns-dev make ami-ec2-build
$ ave oe-patterns-dev make AMI_ID=ami-xxxxxxxxxxxxxxxxx ami-ec2-copy
$ git add .
$ git commit -m "Updated AMI for taskcat testing post $TEMPLATE_VERSION release"
$ git push
```

*Create new product*

1. Create github repo

2. Clone locally

3. Create CDK project, and rename base folder to `cdk` for consistency among patterns.

```
$ mkdir [projectname]
$ cd [projectname]
$ cdk init app --language python
$ cd ..
$ mv [projectname] cdk
```

4. Copy in the `Dockerfile`, `docker-compose.yml`, `Makefile`, `.gitignore` and `packer` directories from another pattern

5. Tweak the `cdk/app.py` file to match other patterns

6. Create an empty CHANGELOG.md


## Areas we can reuse

* packer/setup.sh - the beginning and end of that script should be the some for all patterns using the same OS
* scripts/* - all these scripts could be shared
