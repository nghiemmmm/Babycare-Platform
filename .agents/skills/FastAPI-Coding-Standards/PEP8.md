# PEP 8 - Python Style Guide

> **Version:** 1.0  
> **Python:** 3.12+  
> **Applies to:** FastAPI, SQLAlchemy, Pydantic, AsyncIO Projects

---

# I. Introduction

## Purpose

PEP 8 is the official Python Style Guide published by the Python Software Foundation.

Its purpose is to establish a consistent coding style that improves:

- Readability
- Maintainability
- Collaboration
- Code Review
- Scalability

The most important principle is:

> **Code is read far more often than it is written.**

---

# II. Philosophy

## Write Code for Humans

Good code should be:

- Easy to read
- Easy to modify
- Easy to test
- Easy to debug
- Easy to review

Never optimize readability away for cleverness.

Bad

```python
a=[i for i in x if i%2==0]
```

Better

```python
even_numbers = [
    number
    for number in numbers
    if number % 2 == 0
]
```

---

# III. The Zen of Python

Run:

```python
import this
```

Python philosophy:

```
Beautiful is better than ugly.

Explicit is better than implicit.

Simple is better than complex.

Complex is better than complicated.

Flat is better than nested.

Sparse is better than dense.

Readability counts.

Errors should never pass silently.

There should be one—and preferably only one—obvious way to do it.
```

Every line of code should follow these ideas.

---

# IV. Indentation

## MUST

Use **4 spaces**.

Never use tabs.

Good

```python
if is_admin:
    create_user()
```

Bad

```python
if is_admin:
\tcreate_user()
```

Configure your editor to automatically replace tabs with spaces.

---

# V. Maximum Line Length

Recommended

```
88 characters
```

(Black formatter standard)

Acceptable

```
79 characters
```

for standard PEP 8.

If a line is too long, break it naturally.

Good

```python
student = student_repository.get_student_by_email(
    email=email
)
```

Bad

```python
student = student_repository.get_student_by_email(email=email)
```

when exceeding the maximum length.

---

# VI. Blank Lines

Use blank lines to separate logical sections.

Between top-level functions

```python
def create_user():
    ...


def delete_user():
    ...
```

Between class methods

```python
class UserService:

    def create(self):
        ...


    def delete(self):
        ...
```

Avoid excessive blank lines.

---

# VII. Imports

Always group imports into three sections.

```python
# Standard Library
from datetime import datetime
from pathlib import Path

# Third-party
from fastapi import APIRouter
from sqlalchemy.orm import Session

# Local Application
from app.models.user_model import User
from app.schemas.user_schema import UserCreate
```

Separate each group with one blank line.

---

# VIII. Wildcard Imports

Never use

```python
from user import *
```

Always import explicitly.

Good

```python
from user import User
```

Benefits

- Better readability
- IDE autocomplete
- Easier refactoring
- Prevent namespace collisions

---

# IX. Naming

Variables

```
snake_case
```

Functions

```
snake_case
```

Classes

```
PascalCase
```

Constants

```
UPPER_SNAKE_CASE
```

Modules

```
snake_case.py
```

Packages

```
lowercase
```

---

# X. Comments

Comments should explain

WHY

not

WHAT

Bad

```python
# Increment x
x += 1
```

Good

```python
# Skip inactive users to reduce unnecessary database queries.
```

---

# XI. Docstrings

Every public module

Every public class

Every public function

must have docstrings.

Good

```python
def create_user():
    """
    Create a new user.
    """
```

---

# XII. Whitespace

Correct

```python
total = price + tax
```

Incorrect

```python
total=price+tax
```

Correct

```python
if age > 18:
```

Incorrect

```python
if age>18 :
```

---

# XIII. Trailing Whitespace

Never leave spaces at the end of lines.

Configure your IDE to automatically trim whitespace.

---

# XIV. Trailing Commas

Preferred for multiline collections.

Good

```python
students = [
    "Alice",
    "Bob",
    "Charlie",
]
```

Benefits

- Cleaner Git diff
- Easier editing

---

# XV. String Quotes

Choose one style consistently.

Recommended

```python
"double quotes"
```

or

```python
'single quotes'
```

Do not mix styles without reason.

---

# XVI. Boolean Comparisons

Bad

```python
if is_active == True:
```

Good

```python
if is_active:
```

Bad

```python
if is_active == False:
```

Good

```python
if not is_active:
```

---

# XVII. None Comparison

Always use

```python
is None
```

Good

```python
if user is None:
```

Bad

```python
if user == None:
```

Likewise

```python
is not None
```

---

# XVIII. Exception Handling

Avoid bare except.

Bad

```python
try:
    ...
except:
    ...
```

Good

```python
try:
    ...
except ValueError:
    ...
```

or

```python
except Exception as exc:
    logger.exception(exc)
```

---

# XIX. Functions

Each function should do

ONE thing.

Good

```python
create_student()

send_email()

calculate_average()
```

Bad

```python
create_student_and_send_email_and_log()
```

---

# XX. Classes

Each class should have

ONE responsibility.

Good

```
UserService
```

Bad

```
UserAttendanceNotificationService
```

---

# XXI. Mutable Default Arguments

Never do this

```python
def create(items=[]):
    ...
```

Correct

```python
def create(items=None):
    if items is None:
        items = []
```

---

# XXII. Context Manager

Always prefer

```python
with
```

Good

```python
with open(file_path) as file:
    content = file.read()
```

---

# XXIII. Return Early

Prefer

```python
if user is None:
    return None

return user.email
```

instead of

```python
if user:
    return user.email
else:
    return None
```

---

# XXIV. Type Hints

Always use type hints.

Good

```python
def get_user(
    user_id: int
) -> User:
    ...
```

---

# XXV. Magic Numbers

Avoid

```python
timeout = 3600
```

Prefer

```python
DEFAULT_TIMEOUT = 3600

timeout = DEFAULT_TIMEOUT
```

---

# XXVI. Logging

Prefer logging over print.

Bad

```python
print(user)
```

Good

```python
logger.info("User created: %s", user.id)
```

---

# XXVII. Formatting Tools

Recommended tools

Black

```
black .
```

Ruff

```
ruff check .
```

isort

```
isort .
```

mypy

```
mypy .
```

---

# XXVIII. IDE Configuration

Enable

- Format on Save
- Organize Imports
- Remove Trailing Spaces
- Type Checking
- Auto Docstrings

---

# XXIX. Code Review Checklist

Before committing

- [ ] PEP 8 compliant
- [ ] Descriptive names
- [ ] No wildcard imports
- [ ] Type hints
- [ ] Docstrings
- [ ] No duplicated code
- [ ] Functions have a single responsibility
- [ ] Classes have a single responsibility
- [ ] Proper exception handling
- [ ] Logging instead of print
- [ ] Black formatting
- [ ] Ruff passes
- [ ] isort passes

---

# XXX. Summary

Always remember:

- Readability counts.
- Explicit is better than implicit.
- Keep code simple.
- One responsibility per function.
- One responsibility per class.
- Use descriptive names.
- Follow PEP 8 consistently.
- Write code for humans first, computers second.

Following these principles ensures a clean, maintainable, and professional Python codebase suitable for long-term development.