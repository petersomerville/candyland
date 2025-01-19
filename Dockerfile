FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
RUN pip install --upgrade pip
RUN pip install poetry

# Copy project files
COPY candyland-website/pyproject.toml candyland-website/poetry.lock /app/

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy the rest of the code
COPY . /app

# Expose port
EXPOSE 5000

# Run the application
CMD ["poetry", "run", "flask", "run", "--host=0.0.0.0"]
