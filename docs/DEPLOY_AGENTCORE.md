# Deploying to Amazon Bedrock AgentCore Runtime

Travel Autopilot's agent can run as a hosted AgentCore Runtime. The web UI
stays local; the deployed runtime exposes the agent itself (monitoring
cycles and traveler requests) as an invocable AWS endpoint.

## Prerequisites

- Node.js 20+ and Python 3.10+
- AWS credentials configured (`~/.aws` or environment variables)
- Amazon Bedrock model access enabled (Claude)

## One-time setup

```bash
npm install -g @aws/agentcore
cd agentcore/cdk && npm install && cd ../..   # CDK app dependencies
```

## Deploy

From the repository root:

```bash
# 1. Sync project sources into the runtime bundle
python scripts/sync_agentcore.py

# 2. Deploy (creates the runtime via CDK; confirm the prompts)
agentcore deploy
```

## Invoke the deployed agent

```bash
# autonomous monitoring cycle
agentcore invoke "monitor"

# traveler request
agentcore invoke "Finished early - I'm at Gornergrat now, any suggestions?"
```

`agentcore status` shows the runtime ARN; see the AWS SDK snippet in the
AgentCore docs to call it from code.

## Notes

- `agentcore_runtime/app/` and `agentcore_runtime/data/` are generated
  copies (gitignored) — always re-run `scripts/sync_agentcore.py` after
  changing agent code.
- The runtime keeps mutable trip state in `/tmp` (per-instance,
  ephemeral) — fine for the hackathon demo.
- Model/region come from the runtime environment; set `BEDROCK_MODEL_ID`
  and `AWS_REGION` in the AgentCore environment settings if they differ
  from the defaults in `app/agent/travel_agent.py`.

## Teardown

```bash
agentcore remove all && agentcore deploy
```
