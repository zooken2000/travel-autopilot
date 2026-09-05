"""Fetch recent CloudWatch logs for the AgentCore runtime (free API calls).

Usage:  set -a; source .env; set +a; python scripts/fetch_agentcore_logs.py
"""

import os
from datetime import datetime, timedelta, timezone

import boto3

region = os.environ.get("AWS_REGION", "us-east-1")
logs = boto3.client("logs", region_name=region)

groups = []
paginator = logs.get_paginator("describe_log_groups")
for prefix in ("/aws/bedrock-agentcore", "/aws/vendedlogs/bedrock-agentcore"):
    for page in paginator.paginate(logGroupNamePrefix=prefix):
        groups.extend(g["logGroupName"] for g in page["logGroups"])

if not groups:
    print("No AgentCore log groups found in", region)
    raise SystemExit(1)

start = int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp() * 1000)
for name in groups:
    print(f"\n########## {name}")
    streams = logs.describe_log_streams(
        logGroupName=name, orderBy="LastEventTime", descending=True, limit=3
    )["logStreams"]
    for stream in streams:
        print(f"\n== stream: {stream['logStreamName']}")
        events = logs.get_log_events(
            logGroupName=name,
            logStreamName=stream["logStreamName"],
            startTime=start,
            limit=80,
        )["events"]
        for event in events:
            print(event["message"].rstrip()[:600])
