FROM python:3.11-slim

WORKDIR /app

# Install build deps, then runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

EXPOSE 8000

# Use the PORT environment variable (provided by Vercel) if set.
# Use sh -lc so ${PORT:-8000} is expanded.
CMD ["sh", "-lc", "gunicorn app:app --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 4 --timeout 120"]
