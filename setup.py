import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

CDK_VERSION="2.20.0"

setuptools.setup(
    name="oe-patterns-cdk-common",
    version="1.1.0",
    author="Ordinary Experts",
    author_email="aaron@ordinaryexperts.com",
    description="Common CDK code for re-use in other AWS Marketplace patterns.",
    include_package_data=True,
    package_data={
        'oe_patterns_cdk_common': ['*.sh', 'app_deploy_pipeline/*']
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    url="https://github.com/ordinaryexperts/aws-marketplace-oe-patterns-cdk-common",

    install_requires=[
        f"typeguard==2.13.3",
        f"aws-cdk-lib>={CDK_VERSION}"
    ],

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
