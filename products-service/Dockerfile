FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV FLASK_ENV=production
EXPOSE 8081

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8081", "app:app"]
