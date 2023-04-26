FROM python:3.8-slim-buster

COPY . .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /app

WORKDIR /app

CMD ["python3", "main.py"]

# build image with name and tag 
# docker build -t mqtt_client:v1.0 .