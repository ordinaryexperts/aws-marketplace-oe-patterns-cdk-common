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

log "Waiting for device to be attached"
while [[ ! -e /dev/xvdf && ! -e /dev/nvme1n1 ]]; do
  if [[ $CURRENT_WAITS -ge $MAX_WAITS ]]; then
    log "Device attachment timed out"
    error_exit
  fi
  log "Waiting for /dev/xvdf or /dev/nvme1n1 to appear..."
  sleep 10
  ((CURRENT_WAITS++))
done

DEVICE=""
if [[ -e /dev/xvdf ]]; then
  DEVICE="/dev/xvdf"
elif [[ -e /dev/nvme1n1 ]]; then
  DEVICE="/dev/nvme1n1"
fi

log "Device detected: $DEVICE"

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
