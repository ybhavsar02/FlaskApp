#!/usr/bin/env python3
"""
cloudwatch_setup.py
Creates CloudWatch Log Group, metric filters, and alarms for the Flask app.
Run this once after infrastructure is provisioned.

Usage: python3 cloudwatch_setup.py --env prod --region ap-south-1
"""

import boto3
import argparse
import json
import sys

def create_log_group(logs_client, app_name, env):
    group_name = f"/{app_name}/{env}"
    try:
        logs_client.create_log_group(logGroupName=group_name)
        print(f"[+] Created log group: {group_name}")
    except logs_client.exceptions.ResourceAlreadyExistsException:
        print(f"[=] Log group already exists: {group_name}")

    # Set retention to 30 days
    logs_client.put_retention_policy(
        logGroupName=group_name,
        retentionInDays=30
    )
    return group_name


def create_metric_filter(logs_client, log_group):
    """Create a metric filter to count ERROR log lines"""
    logs_client.put_metric_filter(
        logGroupName=log_group,
        filterName="ErrorCount",
        filterPattern="ERROR",
        metricTransformations=[{
            "metricName": "ErrorCount",
            "metricNamespace": "FlaskDevOpsApp",
            "metricValue": "1",
            "defaultValue": 0
        }]
    )
    print(f"[+] Created metric filter 'ErrorCount' on {log_group}")


def create_alarms(cw_client, instance_id, app_name):
    alarms = [
        {
            "AlarmName": f"{app_name}-high-cpu",
            "MetricName": "CPUUtilization",
            "Namespace": "AWS/EC2",
            "Threshold": 80.0,
            "ComparisonOperator": "GreaterThanThreshold",
            "AlarmDescription": "CPU > 80% for 2 consecutive 2-minute periods",
            "Dimensions": [{"Name": "InstanceId", "Value": instance_id}]
        },
        {
            "AlarmName": f"{app_name}-low-disk",
            "MetricName": "disk_used_percent",
            "Namespace": "CWAgent",
            "Threshold": 85.0,
            "ComparisonOperator": "GreaterThanThreshold",
            "AlarmDescription": "Disk usage > 85%",
            "Dimensions": [
                {"Name": "InstanceId", "Value": instance_id},
                {"Name": "path", "Value": "/"},
                {"Name": "fstype", "Value": "ext4"}
            ]
        },
        {
            "AlarmName": f"{app_name}-app-errors",
            "MetricName": "ErrorCount",
            "Namespace": "FlaskDevOpsApp",
            "Threshold": 10.0,
            "ComparisonOperator": "GreaterThanThreshold",
            "AlarmDescription": "More than 10 application errors in 5 minutes",
            "Dimensions": []
        }
    ]

    for alarm in alarms:
        cw_client.put_metric_alarm(
            AlarmName=alarm["AlarmName"],
            ComparisonOperator=alarm["ComparisonOperator"],
            EvaluationPeriods=2,
            MetricName=alarm["MetricName"],
            Namespace=alarm["Namespace"],
            Period=300,
            Statistic="Average",
            Threshold=alarm["Threshold"],
            AlarmDescription=alarm["AlarmDescription"],
            Dimensions=alarm["Dimensions"],
            TreatMissingData="notBreaching"
        )
        print(f"[+] Created alarm: {alarm['AlarmName']}")


def create_dashboard(cw_client, app_name, instance_id):
    """Create a CloudWatch dashboard for quick visibility"""
    dashboard_body = {
        "widgets": [
            {
                "type": "metric",
                "properties": {
                    "title": "CPU Utilization",
                    "metrics": [["AWS/EC2", "CPUUtilization", "InstanceId", instance_id]],
                    "period": 300,
                    "stat": "Average",
                    "view": "timeSeries"
                }
            },
            {
                "type": "metric",
                "properties": {
                    "title": "Application Error Count",
                    "metrics": [["FlaskDevOpsApp", "ErrorCount"]],
                    "period": 300,
                    "stat": "Sum",
                    "view": "timeSeries"
                }
            }
        ]
    }

    cw_client.put_dashboard(
        DashboardName=f"{app_name}-dashboard",
        DashboardBody=json.dumps(dashboard_body)
    )
    print(f"[+] Created dashboard: {app_name}-dashboard")


def main():
    parser = argparse.ArgumentParser(description="Set up CloudWatch monitoring for Flask app")
    parser.add_argument("--env", required=True, choices=["dev", "qa", "prod"])
    parser.add_argument("--region", default="ap-south-1")
    parser.add_argument("--instance-id", help="EC2 instance ID (from Terraform output)", default="i-0123456789abcdef0")
    parser.add_argument("--app-name", default="flask-devops-app")
    args = parser.parse_args()

    print(f"\n=== Setting up CloudWatch monitoring for {args.app_name} ({args.env}) ===\n")

    logs_client = boto3.client("logs", region_name=args.region)
    cw_client   = boto3.client("cloudwatch", region_name=args.region)

    log_group = create_log_group(logs_client, args.app_name, args.env)
    create_metric_filter(logs_client, log_group)
    create_alarms(cw_client, args.instance_id, args.app_name)
    create_dashboard(cw_client, args.app_name, args.instance_id)

    print("\n=== CloudWatch setup complete! ===")
    print(f"View dashboard: https://{args.region}.console.aws.amazon.com/cloudwatch/home")


if __name__ == "__main__":
    main()
