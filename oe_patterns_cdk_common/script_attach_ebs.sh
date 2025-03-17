#!/bin/bash
function error_exit
{
  cfn-signal --exit-code 1 --stack ${AWS::StackName} --resource ${AsgId} --region ${AWS::Region}
  exit 1
}
token=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
instance_id=$(curl -H "X-aws-ec2-metadata-token: $token" -s http://169.254.169.254/latest/meta-data/instance-id)
max_attach_tries=30
attach_tries=0
success=1
while [[ $success != 0 ]]; do
  if [ $attach_tries -gt $max_attach_tries ]; then
    error_exit
  fi
  sleep 10
  aws ec2 attach-volume --region ${AWS::Region} --volume-id ${EbsId} --instance-id $instance_id --device /dev/sdf
  success=$?
  ((attach_tries++))
done
max_waits=12
current_waits=0
while [ ! -e /dev/xvdf ] && [ ! -e /dev/nvme1n1 ]; do
  echo waiting for /dev/xvdf or /dev/nvme1n1 to attach
  if [ $current_waits -gt $max_waits ]; then
    error_exit
  fi
  sleep 10
  ((current_waits++))
done
if [ -e /dev/xvdf ]; then
  DEVICE=/dev/xvdf
fi
if [ -e /dev/nvme1n1 ]; then
  DEVICE=/dev/nvme1n1
fi
echo $DEVICE
file -s $DEVICE | grep -iv xfs &> /dev/null
if [ $? == 0 ]; then
  mkfs -t xfs $DEVICE
fi
mkdir -p /data
mount $DEVICE /data
echo "$DEVICE /data xfs defaults,nofail 0 2" >> /etc/fstab
xfs_growfs -d /data
