Practice

Layer caching

Multi-stage builds

.dockerignore

Non-root user

1.5 Docker Best Practices for Al

Why It Matters
Copy requirements.txt and pip install BEFORE copying source code.
Dependencies change rarely; code changes often.

Use builder stage for compilation, copy only artifacts to slim final
image. Reduces image size 60-80%.

Exclude _pycache_ .git, *. ipynb, data/, models/ from build context.
Speeds up build, reduces image size.
Never run containers as root in production. Create a dedicated user
- reduces blast radius of vulnerabilities.
COPY vs ADD

Specific tags

Secret handling

Slim base images

Prefer COPY over ADD. ADD has hidden magic (URL fetching, tar
extraction) that causes unexpected behaviour.
Never use :latest in production. Pin exact versions: python:3.11.9-
slim, not python:latest.

Never bake API keys or passwords into images. Use -- secret flag in
BuildKit or env vars at runtime.

python:3.11-slim (55MB) vs python:3.11 (900MB). For GPU:
nvidia/cuda:12.1.0-runtime vs devel.