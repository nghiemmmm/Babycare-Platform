---
name: production-ai-agent-testing
description: Best practices for testing production AI agents. Covers evaluation strategy, Golden Dataset, regression testing, CI/CD, prompt fuzzing, LLM-as-a-Judge, shadow deployment, canary releases, human-in-the-loop, observability, and production monitoring. Use this skill when designing, validating, or deploying AI agents.
license: MIT

metadata:
  version: 1.0.0
  category: AI Engineering
  framework:
    - LangGraph
    - LangChain
    - OpenAI Agents SDK
    - CrewAI
    - AutoGen
    - Generic AI Agent
---

# Production AI Agent Testing

## When to use this skill

Use this skill whenever you need to:

- Design an evaluation pipeline
- Test AI Agents before deployment
- Build regression testing
- Validate LangGraph workflows
- Evaluate Tool Calling
- Evaluate RAG
- Benchmark AI Agents
- Deploy production AI systems

---

# Philosophy

AI systems should **not** be tested like deterministic software.

Instead of checking exact outputs, evaluate behaviors.

Focus on

- Task completion
- Tool correctness
- Retrieval quality
- Planning quality
- Safety
- User satisfaction

---

# Production Evaluation Workflow

```text
Golden Dataset

↓

Unit Evaluation

↓

Workflow Evaluation

↓

Tool Evaluation

↓

RAG Evaluation

↓

Memory Evaluation

↓

Safety Evaluation

↓

Regression Testing

↓

Shadow Deployment

↓

Canary Release

↓

Production Monitoring
```

---

# Version Everything

Treat these as version-controlled artifacts.

- Prompt
- System Prompt
- Workflow
- Tool Definitions
- Model Version
- Golden Dataset
- Evaluation Config

Every deployment should reference exact versions.

---

# Continuous Evaluation

Never evaluate only once.

Automatically trigger evaluations whenever

- Prompt changes
- Workflow changes
- Model changes
- Tool changes

Small continuous evaluations detect regressions earlier than large benchmark suites.

---

# Golden Dataset

A Golden Dataset should represent real production traffic.

Each sample should include

- Prompt
- Conversation History
- User Context
- Expected Tool
- Expected Workflow
- Expected Documents
- Expected Outcome
- Safety Rules

Keep the dataset updated as production traffic evolves.

---

# Regression Testing

Every deployment should compare against the previous production version.

Evaluate

- Task Success Rate
- Tool Accuracy
- Hallucination Rate
- Retrieval Quality
- Latency

Reject deployment if metrics degrade beyond acceptable thresholds.

---

# Tool Testing

External tools are a common source of failures.

Always verify

- Tool selection
- Parameters
- Retry policy
- Timeout handling
- Error recovery

Use mocked services whenever possible during testing.

---

# Prompt Fuzzing

Test robustness using adversarial prompts.

Examples

- Prompt Injection
- Long Context
- Invalid JSON
- Mixed Languages
- Typographical Errors
- Contradictory Instructions

The goal is to expose fragile prompts before production.

---

# LLM-as-a-Judge

Use stronger LLMs to evaluate weaker ones.

Judge dimensions

- Correctness
- Relevance
- Faithfulness
- Safety
- Instruction Following

For critical domains, combine LLM evaluation with human review.

---

# Human-in-the-Loop

Automatically escalate responses when

- Confidence is low
- Safety risks are detected
- Tool execution fails repeatedly
- Multiple reasoning paths disagree

Human review improves reliability in high-risk scenarios.

---

# Shadow Deployment

Run the new agent alongside the production agent.

```text
Production Request

↓

Old Agent
        \
         \
          Compare
         /
New Agent
```

Only the production agent responds to users.

Use differences for evaluation.

---

# Canary Release

Gradually increase traffic.

```text
5%

↓

10%

↓

25%

↓

50%

↓

100%
```

Rollback immediately if evaluation metrics degrade.

---

# Observability

Every production AI system should capture

- Workflow traces
- Tool calls
- Retrieval steps
- Memory updates
- Token usage
- Latency
- Errors

Tracing should be enabled before deployment.

---

# Production Monitoring

Monitor continuously

- Task Success Rate
- Hallucination Rate
- Tool Failure Rate
- Latency
- API Cost
- User Feedback
- Retry Rate

Monitoring is part of evaluation.

---

# Best Practices

- Build Golden Datasets before prompt optimization.
- Version prompts like source code.
- Evaluate behavior instead of exact outputs.
- Run regression tests on every change.
- Use mocked tools for repeatable tests.
- Apply prompt fuzzing.
- Deploy using shadow mode first.
- Use canary releases for production rollout.
- Combine LLM-as-a-Judge with human review.
- Continuously monitor production metrics.

---

# Recommended Tools

Evaluation

- DeepEval
- OpenAI Evals

Tracing

- LangSmith
- Phoenix

Monitoring

- OpenTelemetry
- Prometheus
- Grafana

Deployment

- GitHub Actions
- ArgoCD
- Kubernetes

---

# References

- Anthropic – Demystifying Evals for AI Agents
- DeepEval Documentation
- LangSmith Documentation
- OpenAI Evals
- Microsoft AI Red Team Guidance