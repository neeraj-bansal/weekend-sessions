FROM registry.redhat.io/ubi9/python-311-minimal:latest

# Create non-root application user
RUN useradd -m -u 1001 appuser

WORKDIR /app

# Copy dependency definitions
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn

# Copy application code
COPY --chown=appuser:appuser . .

USER 1001

EXPOSE 8000

CMD ["uvicorn", "finance.app:app", "--host", "127.0.0.1", "--port", "8000"]
