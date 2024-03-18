FROM python:3.10-bookworm

ENV PYTHONUNBUFFERED True
ENV APP_HOME /app

WORKDIR $APP_HOME
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["--host", "0.0.0.0", "--port", "8080"]
ENTRYPOINT ["uvicorn", "main:app"]
