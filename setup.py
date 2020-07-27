import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

# TODO: match version from calling code?
CDK_VERSION="1.42.1"

setuptools.setup(
    name="oe-patterns-cdk-common",
    version="0.0.1",
    author="Ordinary Experts",
    author_email="aaron@ordinaryexperts.com",
    description="Common CDK code for re-use in other AWS Marketplace patterns.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ordinaryexperts/aws-marketplace-oe-patterns-cdk-common",
    packages=setuptools.find_packages(),

    install_requires = [
        f"aws-cdk.core=={CDK_VERSION}"
    ],

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
