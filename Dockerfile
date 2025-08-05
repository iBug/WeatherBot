FROM python:3.12-alpine

WORKDIR /app
ADD requirements.txt ./
RUN pip3 install -Ur requirements.txt

ADD . ./
