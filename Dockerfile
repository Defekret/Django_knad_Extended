FROM python:3.11-slim

LABEL maintainer="Defekret"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app_knad

COPY project/requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY project/ .

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
