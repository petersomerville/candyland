### Logging Configuration

**Import the logging module and configure a module-level logger:**

```python
import logging
logger = logging.getLogger(__name__)
```

**If the script is a CLI or entry point, use basicConfig:**

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
```

### Logging Use

- Use `logger.info()` at the start of each function to confirm execution.
- Use `logger.debug()` to log intermediate variables and flow.
- Use `logger.warning()` when falling back to default logic or encountering unexpected but non-critical conditions.
- Use `logger.error()` inside `except` blocks to capture and log exceptions clearly.

### Context

- Always log meaningful context: URLs, file names, input parameters, or config settings.
- Never log secrets, credentials, or full payloads.
- For large values (e.g., API responses), log only a trimmed version (first 100–200 characters).

### Performance and Behavior

- Time expensive or long-running operations and log their durations.
- Avoid logging in tight loops to reduce noise and prevent performance issues.
- Be mindful of log volume; keep logs informative but concise.

### Versioning and Metadata

- On startup, log the script or Agent version explicitly.
- Also log key configuration paths, environment details, or runtime context.

This format ensures your AI Agent has structured, clear, and production-grade logging practices that enhance observability, debuggability, and operational readiness.
