output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.ragtune_vpc.id
}

output "eks_cluster_name" {
  description = "EKS Cluster Name"
  value       = aws_eks_cluster.ragtune_eks.name
}

output "eks_cluster_endpoint" {
  description = "EKS API Control Plane Endpoint"
  value       = aws_eks_cluster.ragtune_eks.endpoint
}

output "rds_postgresql_endpoint" {
  description = "Managed RDS PostgreSQL Endpoint"
  value       = aws_db_instance.ragtune_postgres.endpoint
}

output "elasticache_redis_endpoint" {
  description = "ElastiCache Redis Endpoint"
  value       = aws_elasticache_replication_group.ragtune_redis.primary_endpoint_address
}

output "s3_storage_bucket_name" {
  description = "S3 Object Storage Bucket Name"
  value       = aws_s3_bucket.ragtune_storage.id
}
