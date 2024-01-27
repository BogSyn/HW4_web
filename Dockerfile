FROM python:3.12

MAINTAINER Bohdan Synytskyi

WORKDIR /app

COPY . .

#RUN pip install -r requirements.txt

EXPOSE 3000

CMD ["python", "main.py"]


