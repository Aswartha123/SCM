FROM python:3.11.4


WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

CMD [ "uvicorn","mani:app","--reload","--port=8000","--host=0.0.0.0"]