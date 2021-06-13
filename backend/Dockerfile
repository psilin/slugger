# https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker

#FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim
FROM python:3.8.1-slim

# set environment variables
ENV PYTHONBUFFERED 1

# set working directory
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY ./requirements-app.txt /app

# install dependencies
RUN pip3 install -r requirements-app.txt

# copy project
COPY . /app/

ENV PYTHONPATH=/

EXPOSE 8000

CMD uvicorn --host=0.0.0.0 --port 8000 app.main:app
