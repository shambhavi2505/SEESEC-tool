# SEESEC backend Dockerfile
# Uses Playwright's official Python image, which already includes
# Chromium and all its system-level dependencies pre-installed —
# this avoids the "Executable doesn't exist" / apt dependency hell
# that plain python:3.x images run into with Playwright.

FROM mcr.microsoft.com/playwright/python:v1.60.0-jammy

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Browsers are already included in this base image, but this is a
# harmless no-op safety net in case the base image version drifts.
RUN playwright install chromium --with-deps

COPY . .

# Render provides the PORT env var at runtime; default to 8000 for
# local `docker run` testing.
ENV PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]