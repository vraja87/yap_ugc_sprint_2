FROM --platform=linux/amd64 python:3.10-slim-buster
WORKDIR /code
RUN apt-get update && apt-get -y install gcc 

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
COPY app/requirements.txt requirements.txt
RUN pip install -r requirements.txt
EXPOSE 5000
COPY . .
COPY app/uwsgi.ini /usr/local/etc/uwsgi.ini

CMD uwsgi --ini /usr/local/etc/uwsgi.ini