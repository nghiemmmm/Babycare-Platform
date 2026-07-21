AI Agent Design Skills
Skill 1. Business-First Design
Mục tiêu

Thiết kế Agent bắt đầu từ bài toán nghiệp vụ, không bắt đầu từ LLM.

Nguyên tắc
Xác định Business Problem.
Xác định User Persona.
Xác định Use Case.
Xác định Success Criteria.
Chỉ sau đó mới chọn AI.
Checklist
Business problem là gì?
Agent giải quyết pain point nào?
Người dùng là ai?
Giá trị tạo ra là gì?
Khi nào không nên dùng Agent?
Skill 2. Scope Definition
Mục tiêu

Xác định chính xác phạm vi của Agent.

Nguyên tắc

Một Agent tốt không phải làm được mọi thứ.

Một Agent tốt là làm rất tốt một phạm vi nhỏ.

Checklist
Input
Output
Supported Tasks
Unsupported Tasks
Failure Cases
Human Handoff
Skill 3. LLM Decision Framework
Mục tiêu

Chỉ sử dụng LLM khi thật sự cần.

Decision Tree
Business Rule?

↓

YES
↓

Code

↓

NO

↓

Need reasoning?

↓

YES

↓

LLM

↓

NO

↓

Traditional Logic
Ví dụ

Không dùng LLM

Email validation
Permission check
Regex parsing
CRUD
Authentication

Nên dùng LLM

Summarization
Classification
Reasoning
Recommendation
Natural Language
Skill 4. Trade-off Analysis
Mục tiêu

Cân bằng giữa:

Accuracy
Flexibility
Cost
Design Matrix
Accuracy	Flexibility	Cost	Recommendation
High	Low	Low	Rule Workflow
Medium	Medium	Medium	Hybrid
High	High	High	Full Agent
Skill 5. Agent Capability Design

Định nghĩa rõ Agent được phép làm gì.

Allowed
Tool A
Tool B
Database C
Forbidden
Delete Database
Access Salary
Call Internet
Human Approval
Payment
Delete Record
Sensitive Data
Skill 6. Data-driven Agent
Mục tiêu

Agent phải grounded trên dữ liệu thật.

Components
User

↓

Agent

↓

Retriever

↓

Memory

↓

Database

↓

Response
Checklist
Source of Truth
Freshness
Ownership
Permission
Metadata
Skill 7. Tool Design

Không để Agent thao tác trực tiếp Database.

Agent

↓

Tool

↓

Service

↓

Repository

↓

Database

Checklist

Idempotent
Permission Check
Validation
Audit Log
Skill 8. Memory Design

Phân loại Memory.

Short-term

Conversation

Long-term

User Preference

Semantic

Knowledge

Episodic

Past Events

Working Memory

Current Task

Skill 9. RAG Architecture
RAG không phải phép màu.

RAG chỉ là Context Provider.

User

↓

Retriever

↓

Ranking

↓

Context

↓

LLM

Checklist

Chunking
Embedding
Metadata
Permission
Citation
Skill 10. Security Design
Security Layers
Authentication

↓

Authorization

↓

Permission

↓

Data Boundary

↓

Session Boundary

↓

Output Filter

Checklist

IAM
RBAC
Encryption
Audit
Session Isolation
Skill 11. Guardrails
Input Guardrail
Prompt Injection
Toxic Prompt
Unsupported Language
Oversized Input
Tool Guardrail
Allowed Tool
Allowed Arguments
Rate Limit
Output Guardrail
Schema Validation
PII Detection
Business Rule Validation
Human Approval
Skill 12. Multi-Agent Design
Khi nào dùng
Domain khác nhau
Context quá lớn
Permission khác nhau
Workflow nhiều bước
Không dùng khi
Chỉ có một use case
Workflow đơn giản
Không có collaboration
Skill 13. Planner Design

Planner chịu trách nhiệm:

Intent Detection
Task Decomposition
Agent Selection
Dependency Planning

Không thực hiện nghiệp vụ.

Skill 14. Reasoner Design

Reasoner chịu trách nhiệm:

Reasoning
Reflection
Self-check
Decision Making
Skill 15. Evaluation Design

Đo chất lượng Agent.

Offline
Golden Dataset
Unit Test
Prompt Test
Online
Success Rate
Hallucination Rate
Tool Success
Latency
Cost
Skill 16. Observability

Theo dõi Agent.

Logging
Prompt
Response
Tool Call
Latency
Token
Cost
Tracing
LangSmith
OpenTelemetry
Phoenix
Skill 17. AI Governance

Quản lý toàn bộ hệ thống Agent.

Versioning
Prompt
Model
Tool
Workflow
Change Management
Prompt Review
Evaluation
Rollback
Skill 18. Enterprise AI Architecture

Một kiến trúc Agentic AI hoàn chỉnh nên bao gồm:

User
        │
        ▼
Authentication
        │
        ▼
Input Guardrails
        │
        ▼
Planner
        │
        ▼
Reasoner
        │
        ▼
Router
        │
        ▼
Specialized Agents
        │
        ▼
Tool Layer
        │
        ▼
Business Services
        │
        ▼
Repository
        │
        ▼
Database / RAG / Memory
        │
        ▼
Output Guardrails
        │
        ▼
Evaluation & Observability
        │
        ▼
Response