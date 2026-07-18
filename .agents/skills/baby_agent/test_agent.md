---
name: ai-agent-testing
description: Build reliable production AI agents through systematic testing. Covers Golden Dataset creation, unit testing, LangGraph workflow validation, RAG evaluation, memory testing, tool verification, safety testing, LLM-as-a-Judge, observability, CI/CD integration, performance benchmarking, and production monitoring. Use when building, debugging, evaluating, or deploying AI agents and agentic workflows.
license: MIT
metadata:
  version: 1.0.0
  framework: Generic AI Agent / LangGraph
  python: ">=3.10"
---

# AI Agent Testing Guide

Testing AI Agents is fundamentally different from traditional software testing.

Unlike deterministic software, AI Agents rely on reasoning, retrieval, memory, planning, tool usage, and probabilistic language models. Therefore, evaluation must cover both the final answer and the entire execution process.

---

# Contents

- Quick Start
- Common Testing Scenarios
- Core Principles
- Development Workflow
- Testing Pyramid
- Golden Dataset
- Unit Testing
- Workflow Testing
- Tool Testing
- RAG Testing
- Memory Testing
- Multi-turn Testing
- Voice & Vision Testing
- Safety Testing
- End-to-End Testing
- Metrics
- LLM-as-a-Judge
- Observability
- Performance Testing
- CI/CD Integration
- Common Pitfalls
- Troubleshooting
- Recommended Tools
- Next Steps

---

# Quick Start

Install common evaluation libraries.

```bash
pip install deepeval
pip install langsmith
pip install pytest
pip install openai
```

Minimal example using DeepEval.

```python
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric

test_case = LLMTestCase(
    input="What causes baby crying?",
    actual_output="Babies may cry because they are hungry."
)

metric = AnswerRelevancyMetric()

metric.measure(test_case)

print(metric.score)
```

---

# Common Testing Scenarios

## Chatbot Evaluation

Evaluate

- Answer quality
- Hallucination
- Context retention

---

## RAG Evaluation

Evaluate

- Retrieval
- Citation
- Context Precision
- Context Recall

---

## Tool Calling

Evaluate

- Tool selection
- Parameters
- Retry
- Timeout

---

## LangGraph Workflow

Evaluate

- Routing
- Branches
- Interrupt
- Retry
- State transitions

---

## Multi-Agent Systems

Evaluate

- Agent coordination
- Handoff
- Shared memory
- Deadlock
- Infinite loops

---

## Voice AI

Evaluate

- ASR
- TTS
- Speaker Similarity
- Naturalness

---

## Vision AI

Evaluate

- Detection
- Tracking
- Classification

---

# Core Principles

## 1. Test Components Independently

Always validate every module before testing the entire workflow.

Example

```text
Retriever

↓

Retriever Test

Planner

↓

Planner Test

Memory

↓

Memory Test
```

---

## 2. Build Golden Dataset First

Never optimize prompts before creating evaluation data.

Golden Dataset should represent production traffic.

---

## 3. Trace Everything

Never evaluate only the final response.

Capture

- workflow
- reasoning
- tool calls
- memory
- latency

---

## 4. Automate Everything

Evaluation should be repeatable.

Avoid manual testing whenever possible.

---

# Development Workflow

Recommended evaluation process

```text
Golden Dataset

↓

Unit Tests

↓

Workflow Tests

↓

Tool Tests

↓

RAG Tests

↓

Memory Tests

↓

Safety Tests

↓

Performance Tests

↓

End-to-End Tests

↓

Deploy

↓

Production Monitoring
```

---

# Testing Pyramid

```text
                End-to-End
                     ▲
                Performance
                     ▲
                 Safety
                     ▲
            Voice / Vision
                     ▲
                Multi-turn
                     ▲
                 Memory
                     ▲
                    RAG
                     ▲
                  Tools
                     ▲
                Workflow
                     ▲
                  Unit
```

Always build from the bottom upward.

---

# Golden Dataset

Every AI project should maintain a Golden Dataset.

Each evaluation example should include

```python
{
    "prompt": "...",
    "conversation_history": "...",
    "user_profile": "...",
    "memory": "...",
    "expected_tools": [...],
    "expected_documents": [...],
    "expected_workflow": [...],
    "expected_response": "...",
    "safety_rules": [...]
}
```

A Golden Dataset should evolve alongside production usage.

---

# Unit Testing

Validate each module independently.

Examples

- Planner
- Intent Classifier
- OCR
- Parser
- Cry Classifier
- Reasoner
- Response Generator

Metrics

- Accuracy
- Precision
- Recall
- F1
- Latency

---

# Workflow Testing

Validate the orchestration graph.

Typical execution

```text
User

↓

Planner

↓

Reasoner

↓

Retriever

↓

Tool

↓

LLM

↓

Response
```

Verify

- routing
- retry
- branch
- interrupt
- state update
- fallback

---

# Tool Testing

Each external dependency should be tested independently.

Examples

- REST API
- Database
- Calendar
- Search
- Camera
- Notification
- Email

Validate

- Tool Selection
- Parameters
- Timeout
- Retry
- Exception Handling
- Fallback

Example

Bad

```python
calendar.create(date=None)
```

Expected

Ask user for the missing date.

---

# RAG Testing

Retrieval quality determines response quality.

Evaluate

- Retrieval Precision
- Retrieval Recall
- Context Precision
- Context Recall
- Citation Accuracy
- Hallucination Rate

Pipeline

```text
Question

↓

Retriever

↓

Vector Search

↓

Re-ranking

↓

LLM
```

---

# Memory Testing

Memory should persist correctly.

Evaluate

- Short-term Memory
- Long-term Memory
- Semantic Memory
- Conversation History

Example

Turn 1

"My baby is 2 months old."

Turn 2

"Can she eat bananas?"

Expected

The model remembers the baby's age.

---

# Multi-turn Testing

Single-turn testing is insufficient.

Evaluate

- Context retention
- Goal completion
- State transition
- Memory updates
- Compound reasoning

---

# Voice & Vision Testing

Voice

Evaluate

- ASR Accuracy
- Speaker Similarity
- MOS
- Naturalness
- Latency

Vision

Evaluate

- Detection Accuracy
- Classification Accuracy
- Tracking Accuracy
- FPS

---

# Safety Testing

Every production AI system requires safety validation.

Test

- Prompt Injection
- Jailbreak
- Hallucination
- PII Leakage
- Policy Compliance
- Toxicity
- Medical Advice
- Harmful Output

Expected

Unsafe responses should be rejected or redirected safely.

---

# End-to-End Testing

Run the complete production workflow.

```text
Speech

↓

ASR

↓

Planner

↓

Reasoner

↓

Memory

↓

Retriever

↓

Tool

↓

LLM

↓

TTS

↓

Response
```

Measure

- Success Rate
- Latency
- API Cost
- Token Usage
- Memory
- CPU
- GPU

---

# Metrics

## Task

- Task Completion
- Goal Success

## Workflow

- Workflow Accuracy
- Branch Accuracy
- Retry Rate

## Tool

- Tool Accuracy
- Parameter Accuracy

## Retrieval

- Context Precision
- Context Recall
- Citation Accuracy

## Memory

- Recall Accuracy
- Context Retention

## Response

- Faithfulness
- Answer Relevancy
- Hallucination
- Toxicity

## Performance

- Latency
- Throughput
- Cost
- Token Usage

---

# LLM-as-a-Judge

Modern AI systems commonly use stronger LLMs for evaluation.

Judge Criteria

- Correctness
- Faithfulness
- Relevance
- Helpfulness
- Safety
- Instruction Following

Human reviewers should validate

- Medical
- Legal
- Safety-critical
- Edge cases

---

# Observability

Every production AI Agent should provide tracing.

Collect

- Workflow Trace
- Tool Calls
- State Changes
- Memory Updates
- Token Usage
- Errors
- Latency
- Cost

Recommended

- LangSmith
- Phoenix
- OpenTelemetry
- Jaeger
- Grafana

---

# Performance Testing

Stress test production workloads.

Examples

- 100 users
- 1000 users
- 10000 users

Measure

- Throughput
- Queue Time
- Response Time
- Token/sec
- CPU
- GPU
- Memory

---

# CI/CD Integration

Every deployment should automatically execute

```text
Golden Dataset

↓

Unit Tests

↓

Workflow Tests

↓

Safety Tests

↓

Regression Tests

↓

Performance Tests

↓

Deploy
```

Never deploy prompt changes without regression testing.

---

# Common Pitfalls

Typical failures

- Hallucination
- Wrong Tool
- Wrong Parameters
- Missing Context
- Missing Memory
- Infinite Loop
- Prompt Injection
- Bad Routing
- Broken Retrieval
- Overfitting to Evaluation Set

---

# Troubleshooting

When failures occur

```text
Wrong Answer

↓

Retriever?

↓

Memory?

↓

Planner?

↓

Tool?

↓

Prompt?

↓

LLM?

↓

Parser?

↓

Root Cause
```

Always inspect execution traces before changing prompts.

---

# Recommended Tools

| Purpose | Tool |
|----------|------|
| Evaluation | DeepEval |
| Tracing | LangSmith |
| Monitoring | Phoenix |
| Metrics | Prometheus |
| Dashboard | Grafana |
| Benchmark | OpenAI Evals |
| Workflow | LangGraph |
| Experiment Tracking | Weights & Biases |

---

# Best Practices

- Build a Golden Dataset before prompt engineering.
- Test every component independently.
- Validate workflow execution.
- Verify tool usage.
- Evaluate retrieval quality.
- Test memory across conversations.
- Perform safety testing.
- Trace every execution.
- Automate evaluation in CI/CD.
- Use LLM-as-a-Judge together with human review.

---

# Next Steps

- Learn DeepEval metrics.
- Integrate LangSmith tracing.
- Build regression datasets.
- Automate evaluation in GitHub Actions.
- Monitor production AI continuously.
- Expand benchmark coverage with AgentBench and GAIA.

---

# References

- DeepEval Documentation
- LangSmith Documentation
- LangGraph Documentation
- OpenAI Evals
- Microsoft AI Red Team Guidance
- Anthropic Evaluation Framework
- AgentBench
- GAIA Benchmark