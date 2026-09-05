"""Verify AWS/Bedrock setup using FREE control-plane calls only.

Checks credentials, lists usable Claude inference profiles, and warns if
BEDROCK_MODEL_ID is not among them. No inference cost is incurred.

Usage:  python scripts/check_bedrock.py
"""

import os
import sys

import boto3


def main() -> int:
    region = os.environ.get("AWS_REGION", "us-east-1")
    sts = boto3.client("sts", region_name=region)
    account = sts.get_caller_identity()["Account"]
    print(f"✓ credentials OK (account ...{account[-4:]}, region {region})")

    bedrock = boto3.client("bedrock", region_name=region)
    profiles = bedrock.list_inference_profiles()["inferenceProfileSummaries"]
    claude_ids = sorted(
        p["inferenceProfileId"]
        for p in profiles
        if "claude" in p["inferenceProfileId"]
    )
    print("Usable Claude inference profiles:")
    for profile_id in claude_ids:
        print(f"  - {profile_id}")

    model_id = os.environ.get("BEDROCK_MODEL_ID", "")
    if not model_id:
        print("✗ BEDROCK_MODEL_ID is not set")
        return 1
    if model_id in claude_ids:
        print(f"✓ BEDROCK_MODEL_ID is valid: {model_id}")
        return 0
    print(f"⚠ BEDROCK_MODEL_ID '{model_id}' is not in the list above — "
          "pick one of the listed profile ids.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
