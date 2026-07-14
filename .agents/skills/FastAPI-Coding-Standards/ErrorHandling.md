# Exception Handling Standards

> Version: 1.0
>
> Applies to:
>
> - Python 3.12+
> - FastAPI
> - Pydantic v2
> - SQLAlchemy 2.x

---

# I. Purpose

The Exception Handling layer defines how errors should be represented and propagated throughout the application.

The goal is to:

- Separate business errors from HTTP errors.
- Keep business logic framework-independent.
- Centralize HTTP error handling.
- Improve testability.
- Improve maintainability.
- Produce consistent API responses.

---

# II. Exception Flow

```
HTTP Request
      │
      ▼
Router
      │
      ▼
Service
      │
      ▼
Repository
      │
      ▼
Raise Domain Exception
      │
      ▼
FastAPI Exception Handler
      │
      ▼
JSON Response
```

Business logic should never generate HTTP responses directly.

---

# III. Responsibilities

## Router

Responsible for:

- Calling services
- Returning responses

Must NOT:

- Catch business exceptions
- Convert business exceptions to HTTPException
- Hide domain errors

---

## Service

Responsible for:

- Business validation
- Business rules
- Raising domain exceptions

Must NOT:

- Import FastAPI
- Raise HTTPException
- Return JSONResponse

---

## Repository

Responsible for:

- Database access
- CRUD operations

Must NOT:

- Raise HTTPException
- Handle HTTP responses
- Catch business exceptions

---

# IV. Exception Hierarchy

Every project should define a base exception.

Example

```python
class AppException(Exception):
    """Base application exception."""
```

Domain exceptions inherit from it.

```python
class StudentNotFoundError(AppException):
    """Student does not exist."""


class StudentAlreadyExistsError(AppException):
    """Student already exists."""


class PermissionDeniedError(AppException):
    """User does not have permission."""


class AttendanceAlreadyExistsError(AppException):
    """Attendance already exists."""
```

---

# V. Domain Exceptions

Domain exceptions describe business failures.

Examples

```
StudentNotFoundError

TeacherNotFoundError

CourseNotFoundError

AttendanceNotFoundError

AttendanceAlreadyExistsError

FaceImageNotFoundError

FaceVerificationFailedError

PermissionDeniedError

InvalidExamStateError

DuplicateRegistrationError
```

These exceptions must not depend on FastAPI.

---

# VI. HTTP Exceptions

Only the FastAPI layer should know HTTP.

Allowed

```python
raise HTTPException(
    status_code=404,
    detail="Not found"
)
```

Only in

- Router
- Authentication middleware
- Dependency

Never inside

```
service/

repository/

crud/

domain/

model/
```

---

# VII. Exception Handlers

Register handlers globally.

Example

```python
@app.exception_handler(StudentNotFoundError)
async def student_not_found_handler(
    request: Request,
    exc: StudentNotFoundError,
):
    return JSONResponse(
        status_code=404,
        content={
            "message": "Student not found"
        },
    )
```

Keep handlers small.

They only translate exceptions into HTTP responses.

---

# VIII. Error Response Format

Use one consistent response format.

Recommended

```json
{
    "message": "Student not found"
}
```

or

```json
{
    "success": false,
    "message": "Student not found",
    "code": "STUDENT_NOT_FOUND"
}
```

Do not mix response structures.

---

# IX. OpenAPI Documentation

FastAPI does not automatically document custom exception handlers.

Document common errors manually.

Example

```python
@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    responses={
        404: {
            "description": "Student not found",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Student not found"
                    }
                }
            },
        },
    },
)
```

Document

- 400
- 401
- 403
- 404
- 409
- 422
- 500

when applicable.

---

# X. Logging

Unexpected exceptions should be logged.

Example

```python
logger.exception(exc)
```

Never expose stack traces to clients.

---

# XI. Transaction Handling

Service controls transactions.

Repository should not decide business rollback.

Example

```
Service

↓

Repository

↓

Raise Exception

↓

Rollback

↓

Raise Domain Exception
```

---

# XII. Naming Convention

Exception names must clearly describe the error.

Good

```
StudentNotFoundError

PermissionDeniedError

InvalidTokenError

CourseAlreadyExistsError

AttendanceClosedError
```

Bad

```
Error

Exception

DatabaseError

UnknownError
```

---

# XIII. Mapping Table

| Domain Exception | HTTP Status |
|------------------|------------|
| ValidationError | 400 |
| AuthenticationError | 401 |
| PermissionDeniedError | 403 |
| StudentNotFoundError | 404 |
| CourseNotFoundError | 404 |
| AttendanceNotFoundError | 404 |
| StudentAlreadyExistsError | 409 |
| DuplicateRegistrationError | 409 |
| AttendanceAlreadyExistsError | 409 |
| InvalidExamStateError | 422 |
| FaceVerificationFailedError | 422 |
| AppException | 500 |

---

# XIV. AI Coding Rules

## MUST

- Define a base AppException.
- Raise domain exceptions from Service.
- Register exception handlers globally.
- Return consistent JSON responses.
- Document common responses in OpenAPI.

## SHOULD

- Keep exception handlers under 20 lines.
- Log unexpected exceptions.
- Use descriptive exception names.
- Map one domain exception to one HTTP status.

## NEVER

- Raise HTTPException inside Service.
- Raise HTTPException inside Repository.
- Return JSONResponse inside Service.
- Catch every exception with bare except.
- Swallow exceptions silently.

---

# XV. Anti-Patterns

Bad

```python
def get_student(student_id: int):

    student = repository.get(student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return student
```

Correct

```python
def get_student(student_id: int):

    student = repository.get(student_id)

    if student is None:
        raise StudentNotFoundError()

    return student
```

FastAPI

```python
@app.exception_handler(StudentNotFoundError)
async def student_not_found_handler(...):

    return JSONResponse(
        status_code=404,
        content={
            "message": "Student not found"
        },
    )
```

---

# XVI. Checklist

Before committing

- [ ] Base AppException exists.
- [ ] Domain exceptions are defined.
- [ ] Services do not import HTTPException.
- [ ] Repositories do not raise HTTPException.
- [ ] Global exception handlers are registered.
- [ ] OpenAPI documents common error responses.
- [ ] Error responses use one consistent schema.
- [ ] Unexpected exceptions are logged.
- [ ] No bare except blocks.
- [ ] No business logic inside exception handlers.

---

# XVII. Architecture Summary

```
Request

↓

Router

↓

Service

↓

Repository

↓

Database

↓

Raise Domain Exception

↓

FastAPI Exception Handler

↓

HTTP Response
```

The Service layer describes **what went wrong**.

The FastAPI layer decides **how that error is represented over HTTP**.

This separation keeps the application framework-independent, easier to test, and easier to maintain.