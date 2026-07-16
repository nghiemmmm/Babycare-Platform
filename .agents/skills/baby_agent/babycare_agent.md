┌─────────────────────────────────────────────────────────────────────────────┐
│                             BabyCare AI Web                                │
└─────────────────────────────────────────────────────────────────────────────┘

                                 Parent
                                    │
        ┌───────────────────────────┼────────────────────────────┐
        │                           │                            │
        ▼                           ▼                            ▼
   Chat Message                Voice Input                 Upload Audio
 (Text từ Chat UI)          (Microphone)                (Baby Cry Audio)
        │                           │                            │
        │                     Whisper STT                        │
        │                           │                            │
        └───────────────┬───────────┴────────────────────────────┘
                        │
                        ▼
               AI Assistant Core
                        │
                        ▼
             Intent & Planning Agent
                        │
        ┌───────────────┼───────────────────────────────────────────────┐
        │               │               │               │               │
        ▼               ▼               ▼               ▼               ▼
   Chat Agent     Voice Logging     Cry Analysis    Health Agent   Nutrition Agent
                     Agent              Agent
        │               │               │               │               │
        │               │               │               │               │
        └───────────────┴───────────────┴───────────────┴───────────────┘
                                │
                                ▼
                     Shared AI Components
                ┌─────────────────────────────────┐
                │ Reasoner                        │
                │ Synthesis                       │
                │ Conversation Memory             │
                │ GraphRAG Retrieval              │
                │ Prompt Builder                  │
                │ Tool Executor                   │
                └─────────────────────────────────┘
                                │
                                ▼
                     Executive Report Generator
                                │
          ┌─────────────────────┼──────────────────────────┐
          ▼                     ▼                          ▼
      Chat Response       Dashboard Summary          PDF / Word Report
                                │
                                ▼
                         Tool & Integration Layer
                ┌─────────────────────────────────────────────┐
                │ Firestore                                   │
                │ GraphRAG Knowledge Base                     │
                │ Whisper                                     │
                │ XTTS Voice Mom                              │
                │ Music Player                                │
                │ Notification                                │
                │ Scheduler                                   │
                └─────────────────────────────────────────────┘
                                │
                                ▼
                        Response to User
Các Agent
1. Intent & Planning Agent

Modules

Intent Detection
Task Classification
Workflow Planning
Agent Router
Context Loader
2. Chat Agent

Modules

Conversation Manager
Memory Manager
GraphRAG Retriever
Context Builder
Prompt Builder
LLM Generator
Citation Manager
Response Formatter
3. Voice Logging Agent

Modules

Intent Detection
Entity Extraction
Data Validation
Record Mapper
Firestore Writer
Confirmation Generator
4. Cry Analysis Agent

Modules

Cry Classifier
Confidence Evaluation
Baby Context Loader
Reasoner
Decision Engine
Voice Mom Controller
Music Controller
Cry Log Manager
Feedback Collector
5. Health Agent

Modules

Symptom Analyzer
Medication Checker
Health History Loader
Risk Assessment
Medical Guideline Retriever
Recommendation Generator
Health Record Manager
6. Nutrition Agent

Modules

Growth Analyzer
Age Calculator
Food History Loader
Allergy Checker
Nutrition Recommender
WHO Growth Checker
Nutrition Logger
Shared AI Components

Các Agent không tự cài Reasoner riêng, mà dùng chung.

Reasoner
Synthesis
Conversation Memory
GraphRAG
Prompt Builder
Tool Executor
Executive Report Generator

Được gọi khi người dùng yêu cầu:

"Tạo báo cáo"

"Tổng hợp tuần"

"Xuất PDF"

"Xuất Word"

Modules

Data Aggregator
Summary Generator
Insight Generator
Dashboard Builder
PDF Generator
Word Generator
Tool Layer
Firestore
GraphRAG
Whisper
XTTS
Music Player
Notification
Scheduler
Có một điểm mình muốn góp ý để kiến trúc "đúng chất LangGraph" hơn

Hiện tại bạn đang đặt Chat Agent, Health Agent, Nutrition Agent... ngang hàng như các agent độc lập. Với quy mô dự án BabyCare AI hiện tại, mình sẽ không dùng multi-agent theo nghĩa mỗi domain là một agent LLM.

Thay vào đó:

Chỉ có Intent & Planning Agent là agent điều phối.
Mỗi "Agent" còn lại thực chất là một LangGraph Workflow (Graph) hoặc một Subgraph.

Ví dụ:

AI Assistant Core
        │
Intent & Planning Agent
        │
 ├── Chat Graph
 ├── Voice Logging Graph
 ├── Cry Analysis Graph
 ├── Health Graph
 ├── Nutrition Graph
 └── Report Graph

Cách này phù hợp hơn với LangGraph vì mỗi nghiệp vụ là một graph có nhiều node (Reasoner, Tool, GraphRAG, Database...), dễ bảo trì và mở rộng hơn so với việc mọi thành phần đều là một "Agent". Đây cũng là kiến trúc mình khuyến nghị cho BabyCare AI.