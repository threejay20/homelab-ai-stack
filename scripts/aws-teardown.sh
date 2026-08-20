#!/bin/bash
# Tears down all AWS resources to stop charges
source ~/homelab/scripts/aws-deploy.env

echo "Stopping ECS tasks..."
aws ecs list-tasks --cluster homelab-ai-stack --query 'taskArns[]' --output text | \
  xargs -I {} aws ecs stop-task --cluster homelab-ai-stack --task {}

echo "Deleting ECS cluster..."
aws ecs delete-cluster --cluster homelab-ai-stack

echo "Emptying S3 bucket..."
aws s3 rm s3://homelab-ai-stack-ui-415902281293 --recursive
aws s3 rb s3://homelab-ai-stack-ui-415902281293

echo "Deleting ECR repositories..."
aws ecr delete-repository --repository-name homelab-chichi --force
aws ecr delete-repository --repository-name homelab-rag --force
aws ecr delete-repository --repository-name homelab-agent --force

echo "Deleting networking..."
aws ec2 delete-security-group --group-id $SG_ID
aws ec2 disassociate-route-table --association-id $(aws ec2 describe-route-tables --route-table-ids $RTB_ID --query 'RouteTables[0].Associations[0].RouteTableAssociationId' --output text)
aws ec2 delete-route-table --route-table-id $RTB_ID
aws ec2 detach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID
aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID
aws ec2 delete-subnet --subnet-id $SUBNET_ID
aws ec2 delete-vpc --vpc-id $VPC_ID

echo "All resources deleted."
