FROM ubuntu

RUN apt update
RUN apt install python3-pip -y

RUN pip3 install python-dotenv
RUN pip3 install Flask
RUN pip3 install requests


WORKDIR /app

COPY . .

CMD [ "python3", "app.py"]