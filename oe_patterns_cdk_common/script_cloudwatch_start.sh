#!/bin/bash

echo "$(date): Starting CloudWatch agent for early logging visibility"

# Replace placeholders with actual log group names
sed -i 's/ASG_APP_LOG_GROUP_PLACEHOLDER/${AsgAppLogGroup}/g' /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
sed -i 's/ASG_SYSTEM_LOG_GROUP_PLACEHOLDER/${AsgSystemLogGroup}/g' /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# Start CloudWatch agent
systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent

echo "$(date): CloudWatch agent started successfully"
