# Skill: LangGraph Workflow Design Pattern

## Purpose

Thiết kế LangGraph theo hướng **Workflow-Oriented Architecture** thay vì xây dựng một Agent duy nhất có hàng chục Tool.

Mỗi nghiệp vụ (Use Case) được triển khai thành một **Subgraph** độc lập và được điều phối bởi một **Router Graph**.

---

# Design Principles

## ❌ Không nên

Một Agent duy nhất tự quyết định toàn bộ Tool.

```
User
    │
    ▼
LLM
    │
    ▼
50+ Tools
```

Nhược điểm

- Tool Selection khó chính xác
- Prompt rất dài
- Chi phí cao
- Hallucination
- Khó debug
- Khó mở rộng

---

## ✅ Nên

Thiết kế nhiều Workflow.

```
User
    │
    ▼
Router Graph
    │
    ├── Chat Graph
    ├── Voice Logging Graph
    ├── Cry Analysis Graph
    ├── Report Graph
    └── ...
```

Mỗi Workflow chỉ sử dụng các Tool liên quan.

---

# Overall Architecture

```
                Entry Point
                     │
                     ▼
               Router Graph
                     │
             Intent Detection
                     │
     ┌───────────────┼────────────────┐
     ▼               ▼                ▼
Chat Graph   Voice Logging      Cry Graph
                     │
                     ▼
             Shared Components
                     │
                     ▼
            Response Generator
```

---

# OverallState

Router Graph luôn sử dụng một State chung.

Ví dụ

```python
class OverallState(TypedDict):

    messages: list

    user_id: str

    baby_id: str

    session_id: str

    current_graph: str

    intent: str

    memory: dict

    response: str
```

OverallState được chia sẻ giữa tất cả Workflow.

---

# Intermediate State

Mỗi Workflow sử dụng State riêng.

Ví dụ

## VoiceLoggingState

```python
class VoiceLoggingState(TypedDict):

    transcript: str

    entities: dict

    database_action: str

    tool_result: dict
```

---

## CryAnalysisState

```python
class CryAnalysisState(TypedDict):

    cry_type: str

    confidence: float

    feeding_context: dict

    health_context: dict

    decision: str
```

---

## ReportState

```python
class ReportState(TypedDict):

    date_range: str

    statistics: dict

    summary: str

    report_file: str
```

Workflow kết thúc sẽ merge dữ liệu trở lại OverallState.

---

# Workflow Pattern

```
START

↓

Load State

↓

Business Logic

↓

Tool Call

↓

Reasoning

↓

Save Result

↓

Merge OverallState

↓

END
```

---

# Router Pattern

Router chỉ có nhiệm vụ phân loại Intent.

Ví dụ

```
Chat Question

↓

chat_graph
```

```
Voice Logging

↓

voice_logging_graph
```

```
Baby Cry

↓

cry_analysis_graph
```

```
Generate Report

↓

report_graph
```

Router không xử lý nghiệp vụ.

---

# Tool Design

Mỗi Workflow chỉ được phép sử dụng Tool liên quan.

Ví dụ

## Chat Graph

- GraphRAG
- Memory
- LLM

---

## Voice Logging Graph

- Whisper
- Firestore
- Growth Tool
- Health Tool

---

## Cry Analysis Graph

- Cry Classifier
- Context Loader
- XTTS
- Music Player
- Notification

---

## Report Graph

- Firestore
- Statistics
- PDF Generator

---

# Shared Components

Tất cả Workflow dùng chung.

```
Reasoner

Prompt Manager

Memory

Tool Executor

Output Formatter

GraphRAG

LLM Factory

Model Router
```

Không duplicate giữa các Workflow.

---

# Response Pattern

Workflow chỉ sinh Decision.

Response được tạo ở bước cuối.

Ví dụ

```
Workflow

↓

Decision

↓

Response Generator

↓

Chat

Voice

Notification

Dashboard

PDF
```

---

# Recommended BabyCare AI Graphs

```
Router Graph

├── Chat Graph

├── Voice Logging Graph

├── Cry Analysis Graph

├── Report Graph

└── Future Graphs
```

---

# Best Practices

✅ Một Workflow cho một Use Case.

✅ OverallState dùng chung.

✅ IntermediateState cho từng Workflow.

✅ Tool chỉ dùng trong Workflow liên quan.

✅ Router chỉ phân loại Intent.

✅ Workflow chỉ giải quyết một nghiệp vụ.

✅ Shared Components không được duplicate.

✅ Không xây dựng một Graph khổng lồ.

---

# Anti Pattern

Không nên

```
User

↓

One Giant Graph

↓

LLM

↓

50 Tools

↓

LLM

↓

50 Tools

↓

LLM

↓

...
```

Nên

```
User

↓

Router Graph

↓

Specific Workflow

↓

Specific Tools

↓

Merge OverallState

↓

Response
```

---

# Benefits

- Dễ mở rộng
- Dễ kiểm thử
- Tool Selection chính xác
- Prompt ngắn hơn
- Giảm hallucination
- Giảm chi phí token
- Workflow rõ ràng
- Phù hợp với LangGraph Production