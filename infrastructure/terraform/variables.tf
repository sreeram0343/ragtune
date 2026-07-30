variable "environment" {
  description = "Target deployment environment"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS Region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for multi-AZ topology"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "eks_node_desired_size" {
  description = "Desired count of Kubernetes worker nodes"
  type        = number
  default     = 3
}

variable "eks_node_max_size" {
  description = "Maximum count of Kubernetes worker nodes"
  type        = number
  default     = 10
}

variable "db_instance_class" {
  description = "RDS PostgreSQL instance class"
  type        = string
  default     = "db.r6g.xlarge"
}

variable "redis_node_type" {
  description = "ElastiCache Redis node instance type"
  type        = string
  default     = "cache.r6g.large"
}
