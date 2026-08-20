#!/bin/bash
# Redeploys the cloud stack for demos
echo "Logging into ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 415902281293.dkr.ecr.us-east-1.amazonaws.com

echo "Starting ECS task..."
source ~/homelab/scripts/aws-deploy.env
CHICHI_ARN=$(aws ecs run-task \
  --cluster homelab-ai-stack \
  --task-definition homelab-chichi:2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
  --query 'tasks[0].taskArn' \
  --output text)
echo "Task started: $CHICHI_ARN"
aws ecs wait tasks-running --cluster homelab-ai-stack --tasks $CHICHI_ARN

ENI_ID=$(aws ecs describe-tasks \
  --cluster homelab-ai-stack \
  --tasks $CHICHI_ARN \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
  --output text)
PUBLIC_IP=$(aws ec2 describe-network-interfaces \
  --network-interface-ids $ENI_ID \
  --query 'NetworkInterfaces[0].Association.PublicIp' \
  --output text)
echo "Backend IP: $PUBLIC_IP"
echo "Update VITE_WS_URL=ws://$PUBLIC_IP:8002/ws in .env.production and rebuild UI"
