FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY forwarder_ia.py .
CMD ["python", "-u", "forwarder_ia.py"]