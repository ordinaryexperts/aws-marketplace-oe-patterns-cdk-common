FROM ordinaryexperts/aws-marketplace-patterns-devenv:2.8.0
# FROM devenv:latest

# install dependencies
RUN pip3 install --break-system-packages pytest
RUN mkdir -p /tmp/code
COPY ./requirements.txt /tmp/code/
COPY ./setup.py /tmp/code/
RUN touch /tmp/code/README.md
WORKDIR /tmp/code
RUN pip3 install --break-system-packages -r requirements.txt
RUN rm -rf /tmp/code
