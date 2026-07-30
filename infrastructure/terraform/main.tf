# Enterprise Cloud-Native Production Infrastructure-as-Code (IaC) - Terraform for RAGTUNE

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
  default_tags {
    tags = {
      Project     = "RAGTUNE"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# -----------------------------------------------------------------------------
# 1. Multi-AZ VPC & Networking Infrastructure
# -----------------------------------------------------------------------------
resource "aws_vpc" "ragtune_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name = "ragtune-${var.environment}-vpc"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.ragtune_vpc.id
  tags = {
    Name = "ragtune-igw"
  }
}

resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.ragtune_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = var.availability_zones[0]
  map_public_ip_on_launch = true
  tags = { Name = "ragtune-public-1" }
}

resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.ragtune_vpc.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = var.availability_zones[1]
  map_public_ip_on_launch = true
  tags = { Name = "ragtune-public-2" }
}

resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.ragtune_vpc.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = var.availability_zones[0]
  tags = { Name = "ragtune-private-1" }
}

resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.ragtune_vpc.id
  cidr_block        = "10.0.20.0/24"
  availability_zone = var.availability_zones[1]
  tags = { Name = "ragtune-private-2" }
}

resource "aws_eip" "nat_eip" {
  domain = "vpc"
}

resource "aws_nat_gateway" "nat_gw" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.public_1.id
  tags = { Name = "ragtune-nat-gw" }
}

# -----------------------------------------------------------------------------
# 2. AWS EKS Kubernetes Control Plane & Worker Node Groups
# -----------------------------------------------------------------------------
resource "aws_eks_cluster" "ragtune_eks" {
  name     = "ragtune-${var.environment}-cluster"
  role_arn = aws_iam_role.eks_cluster_role.arn

  vpc_config {
    endpoint_private_access = true
    endpoint_public_access  = true
    subnet_ids              = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  }

  depends_on = [aws_iam_role_policy_attachment.eks_cluster_policy]
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

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster_role.name
}

# Node Group IAM Role
resource "aws_iam_role" "eks_node_role" {
  name = "ragtune-eks-node-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_node_role.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_node_role.name
}

resource "aws_iam_role_policy_attachment" "eks_container_registry" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_node_role.name
}

resource "aws_eks_node_group" "ragtune_nodes" {
  cluster_name    = aws_eks_cluster.ragtune_eks.name
  node_group_name = "ragtune-prod-nodes"
  node_role_arn   = aws_iam_role.eks_node_role.arn
  subnet_ids      = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  instance_types  = ["t3.xlarge"]

  scaling_config {
    desired_size = var.eks_node_desired_size
    max_size     = var.eks_node_max_size
    min_size     = 2
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry
  ]
}

# -----------------------------------------------------------------------------
# 3. RDS PostgreSQL Multi-AZ Managed Database
# -----------------------------------------------------------------------------
resource "aws_db_subnet_group" "db_subnets" {
  name       = "ragtune-db-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]
}

resource "aws_db_instance" "ragtune_postgres" {
  identifier             = "ragtune-postgres-prod"
  engine                 = "postgres"
  engine_version         = "16.1"
  instance_class         = var.db_instance_class
  allocated_storage      = 100
  max_allocated_storage  = 500
  storage_type           = "gp3"
  multi_az               = true
  db_name                = "ragtune_db"
  username               = "ragtune_user"
  password               = "ragtune_prod_db_secure_password_9988"
  db_subnet_group_name   = aws_db_subnet_group.db_subnets.name
  skip_final_snapshot    = false
  final_snapshot_identifier = "ragtune-postgres-final-snapshot"
  storage_encrypted      = true
  deletion_protection    = true
}

# -----------------------------------------------------------------------------
# 4. ElastiCache Redis Cluster
# -----------------------------------------------------------------------------
resource "aws_elasticache_subnet_group" "redis_subnets" {
  name       = "ragtune-redis-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]
}

resource "aws_elasticache_replication_group" "ragtune_redis" {
  replication_group_id          = "ragtune-redis-cluster"
  replication_group_description = "RAGTUNE Production Multi-Layer Cache"
  node_type                     = var.redis_node_type
  num_cache_clusters            = 2
  port                          = 6379
  automatic_failover_enabled   = true
  subnet_group_name             = aws_elasticache_subnet_group.redis_subnets.name
  at_rest_encryption_enabled    = true
  transit_encryption_enabled    = true
}

# -----------------------------------------------------------------------------
# 5. S3 Object Storage with KMS Encryption & Lifecycle Rules
# -----------------------------------------------------------------------------
resource "aws_kms_key" "s3_key" {
  description             = "KMS Key for RAGTUNE S3 Storage"
  deletion_window_in_days = 30
}

resource "aws_s3_bucket" "ragtune_storage" {
  bucket = "ragtune-enterprise-storage-prod"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "s3_encrypt" {
  bucket = aws_s3_bucket.ragtune_storage.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.s3_key.arn
      sse_algorithm     = "aws:kms"
    }
  }
}
