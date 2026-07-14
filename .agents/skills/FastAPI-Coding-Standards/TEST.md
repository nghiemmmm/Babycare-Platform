# Testing Standards

> Version: 1.0
>
> Applies to:
>
> - Python 3.12+
> - FastAPI
> - Pytest
> - HTTPX
> - SQLAlchemy 2.x
> - Pydantic v2

---

# I. Purpose

Testing ensures application correctness, reliability, and maintainability.

A good test suite should:

- Detect regressions
- Validate business rules
- Protect against unexpected changes
- Support refactoring
- Improve confidence during deployment

Testing is part of the application architecture, not an afterthought.

---

# II. Testing Pyramid

Projects should follow the Testing Pyramid.

```
            End-to-End
                ▲
        Integration Tests
                ▲
            Unit Tests
```

Recommended ratio

- 70% Unit Tests
- 20% Integration Tests
- 10% End-to-End Tests

Most tests should be Unit Tests.

---

# III. Test Structure

```
tests/
│
├── conftest.py
│
├── unit/
│   ├── test_student_service.py
│   ├── test_auth_service.py
│   └── test_course_service.py
│
├── integration/
│   ├── test_student_router.py
│   ├── test_auth_router.py
│   └── test_attendance_router.py
│
└── e2e/
    └── test_login_flow.py
```

---

# IV. Unit Testing

Unit Tests verify one component in isolation.

Dependencies must be mocked.

Never use:

- Real database
- Real Redis
- Real HTTP APIs
- Real filesystem

Example

```
Service

↓

Mock Repository

↓

Assertion
```

---

# V. What Should Be Unit Tested

- Service
- Utility
- Validator
- Domain Logic
- Permission Logic
- Authentication Logic

Do NOT unit test

- SQLAlchemy
- FastAPI
- Pydantic internals

---

# VI. Mocking

Mock all external dependencies.

Examples

```
Repository

Database

Redis

S3

SMTP

HTTP Client

AI Service
```

Use

```
unittest.mock

AsyncMock

MagicMock
```

Avoid connecting to production resources.

---

# VII. Dependency Injection

FastAPI Dependency Injection makes testing easier.

Good

```
Service

↓

Repository Interface

↓

Mock Repository
```

Bad

```
Service

↓

Session()

↓

Real Database
```

Dependencies should always be injectable.

---

# VIII. Integration Testing

Integration Tests verify interaction between components.

Typical flow

```
HTTP Request

↓

Router

↓

Service

↓

Repository

↓

Test Database
```

Integration Tests should verify

- Routing
- Validation
- Serialization
- Dependency Injection
- Database Interaction

---

# IX. Test Client

Use FastAPI TestClient or HTTPX.

Example

```
client.get()

client.post()

client.put()

client.patch()

client.delete()
```

Verify

- Status Code
- Response Body
- Response Schema
- Headers

---

# X. Dependency Overrides

Use dependency_overrides.

Example

```
Production

↓

PostgreSQL

↓

Override

↓

SQLite Test DB
```

or

```
Override

↓

Mock Repository
```

Never connect integration tests to production databases.

---

# XI. Test Database

Integration Tests should use:

- SQLite
- Docker PostgreSQL
- Temporary Database

Never

Production Database

---

# XII. Fixtures

Common setup belongs in fixtures.

Examples

```
client

database

current_user

admin_user

student

teacher

course

attendance
```

Fixtures should be reusable.

---

# XIII. Naming Convention

Test file

```
test_student_service.py
```

Test function

```
test_create_student()

test_student_not_found()

test_register_course_success()

test_login_invalid_password()
```

Never

```
test1()

abc()

run()

```

---

# XIV. Assertion

Every test should contain meaningful assertions.

Good

```
assert response.status_code == 201

assert student.name == "Alice"

assert len(results) == 10
```

Bad

```
assert True
```

---

# XV. Error Testing

Every business error should have tests.

Examples

```
StudentNotFoundError

PermissionDeniedError

DuplicateRegistrationError

AttendanceClosedError

InvalidTokenError
```

Verify

- Exception
- HTTP Status
- Response Message

---

# XVI. Async Testing

Async functions should use

```
pytest.mark.asyncio
```

Never block async tests using

```
time.sleep()
```

Use

```
await

AsyncMock
```

---

# XVII. Coverage

Recommended minimum

Overall

```
80%
```

Critical modules

```
90%
```

Do not chase 100% blindly.

Quality matters more than coverage.

---

# XVIII. AI & External Services

AI models

Face Recognition

OCR

LLM

Cloud APIs

should always be mocked during Unit Tests.

Integration Tests may use lightweight fake implementations.

---

# XIX. Performance

Unit Test

Expected

```
< 100 ms
```

Integration Test

Expected

```
< 2 s
```

Avoid slow tests whenever possible.

---

# XX. Test Isolation

Tests must be independent.

Never rely on

- Execution order
- Shared global state
- Previous test data

Each test should prepare its own data.

---

# XXI. Logging

Tests should not depend on log output.

Logs may be verified only when logging behavior itself is under test.

---

# XXII. AI Coding Rules

## MUST

- Write Unit Tests for all Service methods.
- Mock external dependencies.
- Use dependency_overrides for FastAPI tests.
- Test success and failure scenarios.
- Test business exceptions.
- Use descriptive test names.

## SHOULD

- Reuse fixtures.
- Keep tests independent.
- Keep tests deterministic.
- Verify response_model output.

## NEVER

- Connect Unit Tests to a real database.
- Call external APIs.
- Depend on execution order.
- Hardcode production credentials.
- Use print() for debugging tests.

---

# XXIII. Anti-Patterns

Bad

```
Service

↓

Real Database

↓

Real Redis

↓

Real API
```

Good

```
Service

↓

Mock Repository

↓

Assertions
```

Bad

```
test1()

abc()
```

Good

```
test_create_student_success()

test_student_not_found()

test_duplicate_registration()
```

---

# XXIV. Checklist

Before committing

- [ ] Unit Tests added
- [ ] Integration Tests updated
- [ ] No production database
- [ ] Dependencies mocked
- [ ] Fixtures reused
- [ ] Error scenarios tested
- [ ] Async tests use pytest.mark.asyncio
- [ ] Response status verified
- [ ] Response schema verified
- [ ] Coverage acceptable

---

# XXV. Architecture Summary

```
Unit Test

Service

↓

Mock Repository

↓

Assertions
```

```
Integration Test

HTTP Request

↓

Router

↓

Service

↓

Repository

↓

Test Database

↓

Assertions
```

Unit Tests validate business logic.

Integration Tests validate component interaction.

The majority of tests should remain Unit Tests because they are faster, more reliable, and easier to maintain.