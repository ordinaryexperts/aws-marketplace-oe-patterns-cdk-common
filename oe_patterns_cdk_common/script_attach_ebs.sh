#!/bin/bash

function log {
  echo "$(date '+%Y-%m-%d %H:%M:%S') $1"
}

function error_exit {
  log "Error: Exiting with failure"
  cfn-signal --exit-code 1 --stack "${AWS::StackName}" --resource "${AsgId}" --region "${AWS::Region}"
  exit 1
}

log "Fetching instance metadata"
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" -s)
INSTANCE_ID=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/instance-id)

MAX_ATTACH_TRIES=180  # 180 tries * 10s = 30 minutes
ATTACH_TRIES=0

log "Attaching EBS volume (timeout: 30 minutes)"
while ! aws ec2 attach-volume --region "${AWS::Region}" --volume-id "${EbsId}" --instance-id "$INSTANCE_ID" --device /dev/sdf; do
  ((ATTACH_TRIES++))
  if [[ $ATTACH_TRIES -ge $MAX_ATTACH_TRIES ]]; then
    log "EBS volume attachment failed after $ATTACH_TRIES attempts"
    error_exit
  fi
  sleep 10
done

MAX_WAITS=12  # 12 tries * 10s = 2 minutes
CURRENT_WAITS=0

log "Waiting for EBS volume to be detected"
while [[ -z "$(lsblk -n -o NAME,SERIAL | grep $(aws ec2 describe-volumes --region ${AWS::Region} --volume-ids ${EbsId} --query 'Volumes[0].Attachments[0].VolumeId' --output text))" ]]; do
  if [[ $CURRENT_WAITS -ge $MAX_WAITS ]]; then
    log "Device detection timed out"
    error_exit
  fi
  log "Waiting for EBS volume to appear..."
  sleep 10
  ((CURRENT_WAITS++))
done

# Detect the correct device name dynamically
DEVICE=$(lsblk -n -o NAME,SERIAL | grep "$(aws ec2 describe-volumes --region ${AWS::Region} --volume-ids ${EbsId} --query 'Volumes[0].Attachments[0].VolumeId' --output text)" | awk '{print "/dev/" $1}')

if [[ -z "$DEVICE" ]]; then
  log "Error: Unable to determine device name"
  error_exit
fi

log "Device detected: $DEVICE"

file -s $DEVICE
log "Sleeping for 10 seconds..."
sleep 10
file -s $DEVICE
file -s $DEVICE | grep -iv xfs &> /dev/null
if [ $? == 0 ]; then
  log "No filesystem detected, formatting as XFS"
  mkfs -t xfs $DEVICE
else
  log "Filesystem already exists on $DEVICE"
fi

log "Mounting $DEVICE to /data"
mkdir -p /data
mount $DEVICE /data
echo "$DEVICE /data xfs defaults,nofail 0 2" >> /etc/fstab
xfs_growfs -d /data

log "EBS Volume setup completed successfully!"
