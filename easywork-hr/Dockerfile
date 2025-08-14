FROM python:3.11-slim

WORKDIR /app
COPY ./requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt


ADD . .

COPY deploy/entrypoint.sh /entrypoint.sh

ENTRYPOINT ["sh", "/entrypoint.sh"]