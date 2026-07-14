# Python Naming Convention & Coding Standards with PEP 8

## I. Introduction

Naming Convention is a set of rules for naming variables, functions, classes, modules, packages, and other program components.

Goals:

* Improve readability
* Improve maintainability
* Improve collaboration
* Reduce bugs
* Standardize coding style across the project

---

## II. General Principles

### 1. Descriptive

Names should clearly describe their purpose.

```python
customer_age = 20

def calculate_total_price():
    pass
```

---

### 2. Consistency

Use one naming style throughout the project.

Good:

```python
get_user_name()
get_user_email()
```

Bad:

```python
getUserName()
get_user_email()
```

---

### 3. Clarity

Prefer meaningful names.

Good:

```python
calculate_average_score()
```

Bad:

```python
calc_avg_scr()
```

---

### 4. Balance

Names should be concise but meaningful.

Good:

```python
user_login_count
```

Bad:

```python
number_of_times_a_user_has_logged_into_the_system
```

---

## III. Naming Convention by Component Type

### 1. Variables

Use snake_case.

```python
user_name = "Nghiem"
total_price = 1000
is_active = True
```

---

### 2. Functions

Use snake_case.

```python
def get_user():
    pass

def calculate_total():
    pass
```

---

### 3. Boolean Functions

Start with:

* is_
* has_
* can_
* should_

```python
def is_valid():
    pass

def has_permission():
    pass

def can_edit():
    pass

def should_retry():
    pass
```

---

### 4. Classes

Use PascalCase.

```python
class User:
    pass

class UserAccount:
    pass

class StudentService:
    pass
```

---

### 5. Methods

```python
class User:

    def get_name(self):
        pass

    def update_email(self):
        pass
```

---

### 6. Constants

Use UPPER_CASE.

```python
MAX_LOGIN_ATTEMPTS = 5

JWT_SECRET_KEY = "secret"

ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

---

### 7. Modules

Use snake_case.

```text
user_service.py
database.py
auth_utils.py
attendance_repository.py
```

---

### 8. Packages

Use lowercase.

```text
app/
services/
repositories/
schemas/
models/
```

---

## IV. OOP Naming Convention

### Public Members

```python
name

get_name()
```

---

### Protected Members

Convention only.

```python
_name

_update_cache()
```

---

### Private Members

Uses name mangling.

```python
__password

__encrypt()
```

---

### Dunder Methods

```python
__init__
__str__
__repr__
__len__
__eq__
```

Example:

```python
class User:

    def __init__(self, name: str):
        self.name = name
```

---

## V. Understanding self

```python
class User:

    def get_name(self):
        return self.name
```

When calling:

```python
user.get_name()
```

Python internally executes:

```python
User.get_name(user)
```

`self` represents the current object instance.

---

## VI. Context-Based Naming

### Loop Variables

Good:

```python
for student in students:
    pass
```

Avoid:

```python
for s in students:
    pass
```

---

### Exceptions

```python
ValidationError

DatabaseConnectionError

AuthenticationError
```

---

### Context Managers

```python
with open(file_path) as file:
    pass
```

---

### Boolean Variables

```python
is_active

has_permission

can_edit

should_retry
```

---

## VII. Type Hints

Always use type hints.

Variables:

```python
user_name: str

age: int

scores: list[int]
```

Functions:

```python
def get_user(user_id: int) -> str:
    pass
```

---

### Optional

```python
from typing import Optional

email: Optional[str]
```

---

### Lists

```python
list[User]
```

---

### Dictionaries

```python
dict[str, str]
```

---

## VIII. Common Naming Mistakes

### Excessive Abbreviations

Bad:

```python
usr_nm

calc_avg_scr
```

Good:

```python
user_name

calculate_average_score
```

---

### Overly Long Names

Bad:

```python
number_of_times_a_user_has_logged_into_the_system
```

Good:

```python
user_login_count
```

---

### Inconsistent Naming

Bad:

```python
getUserName()

get_user_email()
```

---

## IX. FastAPI Naming Convention

### Routers

```python
user_router

auth_router

attendance_router
```

---

### Services

```python
UserService

AuthService

AttendanceService
```

---

### Repositories

```python
UserRepository

AttendanceRepository
```

---

### Schemas

```python
UserCreate

UserUpdate

UserResponse
```

---

### Models

```python
User

AttendanceLog

FaceEmbedding
```

---

## X. AI / Machine Learning Naming Convention

### Dataset

```python
train_dataset

test_dataset

validation_dataset
```

---

### Models

```python
face_recognition_model

light_estimation_model
```

---

### Training Functions

```python
train_model()

evaluate_model()

predict_image()
```

---

### Hyperparameters

```python
learning_rate

batch_size

num_epochs

weight_decay
```

---

## XI. Documentation Convention

### Module Docstring

Every Python file should start with a module docstring.

```python
"""
User Service Module

Handles user-related business logic.

Responsibilities:
- Create user
- Update profile
- Change password
"""
```

---

### Class Docstring

```python
class UserService:
    """
    Service responsible for user business logic.
    """
```

---

### Function Docstring

```python
def calculate_total_price(
    price: float,
    quantity: int
) -> float:
    """
    Calculate total price.

    Args:
        price: Product unit price.
        quantity: Number of products.

    Returns:
        Total price.
    """
```

---

### Async Function Docstring

```python
async def get_user_by_id(
    user_id: int
) -> User:
    """
    Retrieve user by identifier.

    Args:
        user_id: User identifier.

    Returns:
        User entity.

    Raises:
        NotFoundException:
            If user does not exist.
    """
```

---

## XII. Import Convention

### Standard Import Order

```python
# Standard Library
from datetime import datetime

# Third Party
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

# Local Application
from app.schemas.user_schema import UserCreate
from app.services.user_service import UserService
```

---

### Avoid Wildcard Imports

Bad:

```python
from user_service import *
```

Good:

```python
from user_service import UserService
```

---

## XIII. FastAPI Project Structure

```text
app/
├── api/
├── routers/
├── services/
├── repositories/
├── models/
├── schemas/
├── core/
├── utils/
├── database/
```

---

### Router Naming

```python
user_router

attendance_router

report_router
```

---

### Service Naming

```python
UserService

AttendanceService

ReportService
```

---

### Repository Naming

```python
UserRepository

AttendanceRepository

ReportRepository
```

---

### Schema Naming

Request Schemas:

```python
UserCreate

UserUpdate

UserLogin
```

Response Schemas:

```python
UserResponse

UserDetailResponse
```

---

### Model Naming

```python
User

Attendance

ClassSection
```

---

## XIV. Clean Code Guidelines

### Function Length

Prefer:

```python
< 50 lines
```

---

### Class Responsibility

Each class should have a single responsibility.

Good:

```python
UserService
```

Bad:

```python
UserAndAttendanceAndReportService
```

---

### Avoid Code Duplication

Extract repeated logic into reusable functions.

---

### Clear Function Names

Good:

```python
calculate_average_score()
```

Bad:

```python
process()
```

---

## XV. FastAPI Architecture Rules

### Router Layer

Responsibilities:

* Receive requests
* Validate input
* Call services
* Return responses

Do NOT place business logic here.

---

### Service Layer

Responsibilities:

* Business logic
* Validation rules
* Application workflows

---

### Repository Layer

Responsibilities:

* Database operations
* Query execution

---

### Schema Layer

Responsibilities:

* Request validation
* Response serialization

---

### Model Layer

Responsibilities:

* Database entity definitions

---

## XVI. PEP 8 Checklist

### Naming

* [ ] Descriptive names
* [ ] No unnecessary abbreviations
* [ ] snake_case for variables
* [ ] snake_case for functions
* [ ] PascalCase for classes
* [ ] UPPER_CASE for constants

---

### Documentation

* [ ] Module docstring
* [ ] Class docstring
* [ ] Public method docstring

---

### Type Hints

* [ ] Parameter type hints
* [ ] Return type hints

---

### FastAPI

* [ ] Router contains no business logic
* [ ] Service contains business logic
* [ ] Repository handles database access
* [ ] Schema used for request/response validation

---

### Readability

* [ ] Functions are concise
* [ ] Classes have a clear responsibility
* [ ] No duplicated code
* [ ] Imports follow standard order

---

## XVII. Example of Good FastAPI Code

```python
"""
User Service Module

Handles user-related business logic.
"""

class UserService:
    """
    User business service.
    """

    async def get_user_by_id(
        self,
        user_id: int
    ) -> User:
        """
        Retrieve user by identifier.

        Args:
            user_id: User identifier.

        Returns:
            User entity.
        """
```

---

## XVIII. Final Principle

Write code for humans first, computers second.

Good code should be:

* Readable
* Maintainable
* Consistent
* Documented
* Predictable
* Easy to extend

A developer should be able to understand your code months later without needing additional explanation.
