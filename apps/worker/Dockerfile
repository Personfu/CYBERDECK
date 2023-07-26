FROM python:3.11-slim
WORKDIR /app
COPY reqs.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt || true
COPY . /app
CMD ["python", "worker.py"]
