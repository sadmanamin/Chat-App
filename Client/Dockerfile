FROM python:3.8.3-slim-buster
WORKDIR /dir
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "socketio-client.py"]