# ─────────────────────────────────────────────────────────────
# Terraform Variables
# ─────────────────────────────────────────────────────────────

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "ap-south-1"
}

variable "app_name" {
  description = "Application name used as prefix for all resources"
  type        = string
  default     = "flask-devops-app"
}

variable "environment" {
  description = "Deployment environment (dev/qa/prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "qa", "prod"], var.environment)
    error_message = "Environment must be one of: dev, qa, prod."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "key_name" {
  description = "AWS Key Pair name for SSH access"
  type        = string
}

variable "trusted_ip" {
  description = "Your IP address for SSH access (format: x.x.x.x/32)"
  type        = string
  sensitive   = true
}
