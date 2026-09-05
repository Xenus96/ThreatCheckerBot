FROM python:3.14-slim
LABEL authors="Xenus96 (CyberChief)"
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY vars.env .
COPY main.py .
CMD ["python", "main.py"]
