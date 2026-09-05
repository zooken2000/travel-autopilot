# builder.aws.com Post 2 Draft (bonus)

**Title:** Agents for Humans: Three bugs between my Strands agent and
Bedrock AgentCore — and how CloudWatch solved all of them

---

My Travel Autopilot agent ran perfectly on my laptop. Getting the same
agent onto Amazon Bedrock AgentCore Runtime took exactly three bugs.
Here's the honest deploy journey, because the error messages will save
you an afternoon.

## Bug 1: "CDK project not found"

`agentcore deploy` failed immediately. The new AgentCore CLI
(`npm install -g @aws/agentcore`) deploys through a CDK app that
`agentcore create` scaffolds under `agentcore/cdk/` — and I had written
my `agentcore.json` by hand without it. The scaffold's CDK app is fully
generic (it reads your `agentcore.json` and `aws-targets.json` at synth
time), so the fix was simply bringing the vended `cdk/` sources into the
repo and running `npm install` inside it. Lesson: the CLI's config files
travel together; scaffold first, then customize.

## Bug 2: a 500 caused by an argument's *name*

Deploy succeeded; `agentcore invoke` returned a bare 500. I reproduced
the runtime locally — same wheels, same entrypoint — and got the real
traceback in seconds:

```
TypeError: invoke() missing 1 required positional argument: '_context'
```

`bedrock_agentcore` inspects your entrypoint's signature and passes the
request context only if the parameter is *named* `context`. I had named
mine `_context` to mark it unused — so the framework decided my handler
didn't want a context and called it with one argument. Renaming the
parameter (or dropping it) fixed the 500. Lesson: in AgentCore
entrypoints, parameter names are API.

## Bug 3: AccessDenied — but not the IAM kind I expected

Next invoke, next 500. This time only CloudWatch could tell me why:

```
AccessDeniedException ... ConverseStream ... not authorized to perform
the required AWS Marketplace actions (aws-marketplace:Subscribe)
```

My runtime's execution role tried to invoke a Claude model my account
had never used. First use of a Bedrock model triggers a Marketplace
subscription — which an execution role can't approve. My laptop runs had
all used a model that was already enabled, so I'd never seen it. The fix
was declaring the known-good model explicitly in `agentcore.json`:

```json
"envVars": [{ "name": "BEDROCK_MODEL_ID",
              "value": "us.anthropic.claude-haiku-4-5-20251001-v1:0" }]
```

Lesson: pin your model ID in the runtime environment, and enable model
access in the Bedrock console before your role needs it.

## The payoff

```
$ agentcore invoke "monitor"
Monitoring cycle complete. One critical issue identified and escalated:
missing accommodation for August 19. The free time in Zermatt is not
urgent and does not require intervention at this time.
```

The deployed agent triaging on its own — one alert escalated, one
non-issue left alone. Worth all three bugs.

*Travel Autopilot: https://github.com/zooken2000/travel-autopilot. Built with Strands Agents SDK, Amazon
Bedrock, and Bedrock AgentCore for the Agents for Humans hackathon.*
