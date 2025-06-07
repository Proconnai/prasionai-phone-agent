FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "5011"]
