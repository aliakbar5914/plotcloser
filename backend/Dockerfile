# Recipe to build the PlotCloser API container for Hugging Face Spaces.

# 1. Start from a small official Linux image that already has Python.
FROM python:3.12-slim

# 2. Python settings: don't write .pyc files, print logs immediately.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. Hugging Face runs containers as user 1000, so create that user (not root = safer).
RUN useradd -m -u 1000 appuser
WORKDIR /home/appuser/app

# 4. Install packages FIRST (this layer is cached, so rebuilds are fast
#    when only our code changes, not requirements.txt).
COPY --chown=appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy our application code.
COPY --chown=appuser app ./app

USER appuser

# 6. The hosting platform tells us the port in $PORT (Render does this).
#    If PORT is not set (e.g. Hugging Face), use 7860.
ENV PORT=7860
EXPOSE 7860

# 7. Start the server. 0.0.0.0 = accept connections from outside the container.
#    "sh -c" is needed so ${PORT} is replaced with its value.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
