FROM alpine:latest
RUN apk add --no-cache python3 && \
    python3 -m ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi  
    
COPY . /app
WORKDIR /app

# install psycopg2 dependencies
RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev postgresql-libs zlib-dev jpeg-dev

RUN apk update
RUN apk add postgresql zlib jpeg
RUN pip install psycopg2 Pillow
RUN pip3 install -r requirements.txt
RUN python manage.py makemigrations
RUN python manage.py migrate
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
