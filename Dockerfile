FROM alpine:edge
RUN apk add --no-cache python3 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache
COPY . /app
WORKDIR /app
RUN apk add --virtual build-deps --no-cache gcc python3-dev musl-dev zlib-dev postgresql-dev jpeg-dev
RUN apk add postgresql zlib jpeg
RUN pip install psycopg2 Pillow==8.0.1
RUN pip3 install -r requirements.txt
RUN python manage.py makemigrations
RUN python manage.py migrate
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
