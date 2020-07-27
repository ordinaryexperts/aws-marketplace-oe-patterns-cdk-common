import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="oe-cdk-common",
    version="0.0.1",
    author="Aaron Richard Carlucci",
    author_email="aaron@ordinaryexperts.com",
    description="Common CDK code for re-use in other AWS Marketplace patterns.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ordinaryexperts/aws-marketplace-oe-patterns-cdk-common",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
