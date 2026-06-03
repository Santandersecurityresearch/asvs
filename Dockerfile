FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=asvs.settings \
    PORT=8000 \
    GUNICORN_WORKERS=3

WORKDIR /app

RUN addgroup --system asvs \
    && adduser --system --ingroup asvs --home /app asvs

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY --chown=asvs:asvs . .
RUN mkdir -p /app/db /app/storage /app/staticfiles \
    && chown -R asvs:asvs /app

USER asvs

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os, urllib.request; port=os.environ.get('PORT','8000'); host=os.environ.get('DJANGO_HEALTHCHECK_HOST') or os.environ.get('DJANGO_ALLOWED_HOSTS','127.0.0.1').split(',')[0]; req=urllib.request.Request('http://127.0.0.1:%s/' % port, headers={'Host': host}); urllib.request.urlopen(req, timeout=4).read()" || exit 1

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput --clear && python -m gunicorn asvs.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${GUNICORN_WORKERS:-3} --access-logfile - --error-logfile -"]
