# Production Infrastructure-as-Code (IaC) - Terraform Module for RAGTUNE

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket         = "ragtune-tfstate-prod"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "ragtune-tflocks"
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

# 1. Production VPC Networking
resource "aws_vpc" "ragtune_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "ragtune-production-vpc"
    Environment = "production"
  }
}

# 2. AWS EKS Kubernetes Cluster
resource "aws_eks_cluster" "ragtune_eks" {
  name     = "ragtune-prod-cluster"
  role_arn = aws_iam_role.eks_cluster_role.arn

  vpc_config {
    subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  }
}

resource "aws_iam_role" "eks_cluster_role" {
  name = "ragtune-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })
}

# Dummy Subnet resources
resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.ragtune_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
}

resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.ragtune_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
}
