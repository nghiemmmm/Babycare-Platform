---
name: langgraph-persistence
description: |
  Use this skill when building production LangGraph applications that require
  persistent workflow execution, conversation memory, checkpointing,
  thread management, human-in-the-loop workflows, state recovery,
  or long-term memory.

  This skill explains how to configure Checkpointers, Stores,
  Thread IDs, State History, Time Travel, update_state(),
  PostgreSQL persistence, and production memory architecture.

  Use whenever implementing:
    - Conversation memory
    - Workflow persistence
    - Human approval (HITL)
    - Interrupt / Resume
    - Multi-turn agents
    - Long-term user memory
    - Durable execution
---

# LangGraph Persistence

## Purpose

LangGraph Persistence provides durable execution by saving graph state
after every execution step. It allows workflows to resume after failures,
remember conversations, support human approval, and maintain user memory.

---

# Architecture

```
                 User
                   │
                   ▼
            LangGraph Workflow
                   │
      ┌────────────┴─────────────┐
      ▼                          ▼
 Checkpointer                Store
(Thread Memory)        (Long-term Memory)
```

---

# Memory Types

LangGraph provides two completely different memory systems.

## 1. Checkpointer (Short-term Memory)

Scope:

- Per thread
- Per conversation
- Workflow execution

Stores:

- Messages
- Current node
- Planner output
- Tool results
- Execution state

Production:

- PostgresSaver

Development:

- InMemorySaver
- SqliteSaver

---

## 2. Store (Long-term Memory)

Scope:

- Cross threads
- Cross conversations

Stores:

- User profile
- Preferences
- Facts
- Settings
- Long-term memory

Examples

```
User Name

Preferred Language

Baby Profile

Notification Preference

Mother Voice
```

---

# Thread ID

Every graph invocation MUST include a thread_id.

```
config = {
    "configurable": {
        "thread_id": "user-123"
    }
}
```

Without thread_id:

- Conversation is NOT persisted.

---

# Checkpointer

Development

```
InMemorySaver()
```

Local

```
SqliteSaver()
```

Production

```
PostgresSaver()
```

Recommended architecture:

```
Workflow

↓

Checkpoint

↓

Planner

↓

Checkpoint

↓

Tool

↓

Checkpoint

↓

Finish
```

---

# Store

Store provides long-term memory.

Example

```
User

↓

Preferences

↓

Store

↓

Future Conversations
```

Store is shared across all thread IDs.

---

# State History

LangGraph stores every checkpoint.

Capabilities

- Replay execution
- Browse history
- Fork execution
- Debug workflows

Example

```
Checkpoint1

↓

Checkpoint2

↓

Checkpoint3
```

Resume

Replay

Fork

---

# update_state()

State can be modified before resuming execution.

Useful for

- Human corrections
- Manual approvals
- External updates
- Workflow recovery

---

# Human-in-the-loop

Persistence is required for

- interrupt()
- resume()
- approval workflows
- manual validation

Architecture

```
Workflow

↓

Interrupt

↓

Human Review

↓

Resume
```

---

# Subgraph Persistence

Options

checkpointer=False

Stateless subgraph

checkpointer=None

Supports interrupts only

checkpointer=True

Persistent multi-turn subgraph

---

# Production Architecture

```
                API
                 │
                 ▼
          LangGraph Workflow
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
 Checkpointer           Store
(PostgresSaver)     (Long-term Memory)
      │                     │
      └──────────┬──────────┘
                 ▼
            PostgreSQL
```

---

# Best Practices

Always

- Use PostgresSaver in production.
- Always provide thread_id.
- Separate Checkpointer from Store.
- Use Store for user memory.
- Use Checkpointer for workflow state.
- Keep Vector Database separate from Store.

Never

- Use InMemorySaver in production.
- Forget thread_id.
- Store business data inside Checkpointer.
- Use Store as a Vector Database.

---

# Typical Enterprise Architecture

```
User
   │
   ▼
API Gateway
   │
   ▼
LangGraph Workflow
   │
   ├── Planner
   ├── Skills
   ├── Tools
   └── Synthesizer
        │
        ▼
Persistence Layer
   │
   ├── Checkpointer
   ├── Store
   ├── PostgreSQL
   └── Vector Database
```

---

# Related Skills

- langgraph-human-in-the-loop
- deep-agents-memory
- langgraph-state-management
- langgraph-workflows
- postgres-checkpointing