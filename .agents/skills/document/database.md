# BabyCare AI Database Documentation

## Overview

This document describes the production PostgreSQL database schema for
BabyCare AI.

## Modules

### 1. User Management

#### users

Stores user accounts, authentication and profile information.

Fields: - id (UUID, PK) - username - email - password_hash - phone -
is_admin - active - first_login - created_at - updated_at - last_login

#### login_logs

Stores login history.

Relationship: - login_logs.user_id → users.id

------------------------------------------------------------------------

### 2. Baby Management

#### babies

Stores baby profile information.

#### baby_guardians

Many-to-many relationship between users and babies.

#### growth_logs

Stores growth history: - Height - Weight - Head circumference

------------------------------------------------------------------------

### 3. Vaccination

#### vaccines

Master vaccine list.

#### baby_vaccinations

Vaccination schedule and history.

Relationship: - baby_vaccinations.baby_id → babies.id -
baby_vaccinations.vaccine_id → vaccines.id

------------------------------------------------------------------------

### 4. Healthcare

#### healthcare_tips

Health education articles.

#### alert_rules

Rules used for automatic health alerts.

#### notifications

Stores notification history.

Relationship: - notifications.user_id → users.id - notifications.baby_id
→ babies.id

------------------------------------------------------------------------

### 5. AI Chatbot (GraphRAG)

#### chat_threads

Conversation sessions.

#### chat_messages

Messages inside conversations.

#### chat_message_sources

GraphRAG citations linking answers to indexed knowledge.

#### knowledge_documents

Indexed medical documents.

Relationships: - chat_threads.user_id → users.id - chat_threads.baby_id
→ babies.id - chat_messages.thread_id → chat_threads.id -
chat_message_sources.message_id → chat_messages.id -
chat_message_sources.document_id → knowledge_documents.id

------------------------------------------------------------------------

### 6. Computer Vision

#### skin_analysis_results

Stores AI skin analysis results.

Relationship: - baby_id → babies.id

------------------------------------------------------------------------

### 7. Nutrition Recommendation

#### nutrition_recommendations

AI-generated nutrition recommendations.

Relationship: - baby_id → babies.id

------------------------------------------------------------------------

### 8. Health Records

#### health_records

Medical history and symptoms.

Relationship: - baby_id → babies.id

------------------------------------------------------------------------

### 9. OCR Medical Documents

#### medical_documents

Uploaded medical documents.

#### medical_document_extractions

Structured information extracted by OCR.

Relationship: - medical_documents.baby_id → babies.id -
medical_document_extractions.document_id → medical_documents.id

------------------------------------------------------------------------

### 10. Calendar

#### calendar_events

Google Calendar synchronization.

Relationship: - baby_id → babies.id

------------------------------------------------------------------------

# Entity Relationship Summary

Users ├── Login Logs ├── Notifications └── Baby Guardians │ ▼ Babies ├──
Growth Logs ├── Vaccinations ├── Health Records ├── Nutrition
Recommendations ├── Calendar Events ├── Skin Analysis Results └──
Medical Documents │ ▼ Medical Document Extractions

Knowledge Documents │ ▼ Chat Message Sources │ ▼ Chat Messages │ ▼ Chat
Threads

## Technologies

-   PostgreSQL
-   UUID Primary Keys
-   FastAPI
-   GraphRAG
-   JSON Fields
-   Google Calendar API
-   Computer Vision
-   OCR
