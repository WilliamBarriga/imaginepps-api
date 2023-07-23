FROM python:3.11

ENV PYTHONUNBUFFERED 1

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

COPY /.env /.env
RUN sed -i 's/\r$//g' /.env
RUN chmod +x /.env

RUN python db_creation.py

EXPOSE 8000
CMD gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --max-requests 100 --access-logfile - --error-logfile - --log-level info