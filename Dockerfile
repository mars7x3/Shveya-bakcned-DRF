FROM python:3.11

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip

COPY ./app/requirements.txt /usr/src/requirements.txt
RUN pip install -r /usr/src/requirements.txt

COPY ./app /usr/src/app

