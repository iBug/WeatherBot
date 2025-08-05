FROM python:3.12-alpine

WORKDIR /app
ADD requirements.txt ./
RUN pip3 --no-cache-dir install -Ur requirements.txt

ADD . ./
