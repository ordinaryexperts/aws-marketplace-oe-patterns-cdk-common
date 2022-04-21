FROM ordinaryexperts/aws-marketplace-patterns-devenv:feature-cdk2
# FROM devenv:latest

# install dependencies
RUN pip3 install pytest
RUN mkdir -p /tmp/code
COPY ./requirements.txt /tmp/code/
COPY ./setup.py /tmp/code/
RUN touch /tmp/code/README.md
WORKDIR /tmp/code
RUN pip3 install -r requirements.txt
RUN rm -rf /tmp/code
