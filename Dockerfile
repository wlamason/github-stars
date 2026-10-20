FROM python:3.15.0-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.3 /uv /uvx /bin/
# Use the interpreter in this image (Python 3.15.0) rather than downloading another.
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_PYTHON_PREFERENCE=only-system
COPY . /src
WORKDIR /src
RUN uv sync --locked --no-dev
CMD ["uv", "run", "--locked", "--no-dev", "python", "github_stars.py", "--help"]
