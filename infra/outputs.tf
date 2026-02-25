# ─────────────────────────────────────────────────────────────
# Terraform Outputs
# ─────────────────────────────────────────────────────────────

output "ec2_public_ip" {
  description = "Public IP of the EC2 app server"
  value       = aws_instance.app_server.public_ip
}

output "ec2_instance_id" {
  description = "Instance ID of the EC2 app server"
  value       = aws_instance.app_server.id
}

output "ecr_repository_url" {
  description = "ECR repository URL for pushing Docker images"
  value       = aws_ecr_repository.app.repository_url
}

output "s3_artifact_bucket" {
  description = "S3 bucket name for build artifacts"
  value       = aws_s3_bucket.artifacts.bucket
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "app_url" {
  description = "Application URL"
  value       = "http://${aws_instance.app_server.public_ip}"
}
