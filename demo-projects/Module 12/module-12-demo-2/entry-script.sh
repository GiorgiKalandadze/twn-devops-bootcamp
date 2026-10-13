#!/bin/bash
sudo yum update -y
sudo amazon-linux-extras install docker -y || sudo yum install -y docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user
docker run -d -p 8080:80 nginx