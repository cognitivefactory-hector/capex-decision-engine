FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY . .
RUN pip install --upgrade pip && pip install .

# Collect static assets (whitenoise serves them in production).
RUN DJANGO_SECRET_KEY=build-time python manage.py collectstatic --noinput

EXPOSE 8000

# DJANGO_SECRET_KEY and ANTHROPIC_API_KEY are provided at runtime via env/secrets.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
