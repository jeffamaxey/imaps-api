FROM --platform=linux/amd64 python:3.8.1-slim-buster

RUN apt-get update
RUN apt-get install docker.io -y

RUN mkdir -p /home/app
RUN useradd -ms /bin/bash -u 1007 goodwright
RUN usermod -aG sudo goodwright
WORKDIR /home/app

RUN apt-get install --reinstall ca-certificates
RUN mkdir -p /usr/share/man/man1 /usr/share/man/man2
RUN apt-get install -y --no-install-recommends openjdk-11-jre
RUN apt-get install curl -y
RUN curl -s https://get.nextflow.io | bash
RUN chmod +x nextflow
RUN mv nextflow /usr/local/bin
RUN chown goodwright /usr/local/bin/nextflow

COPY ./core ./core
COPY ./analysis ./analysis
COPY ./peka ./peka
COPY ./manage.py ./manage.py
COPY ./requirements.txt ./requirements.txt

RUN chown goodwright core
RUN chown goodwright analysis
RUN chown goodwright peka
RUN chown goodwright manage.py

RUN pip install gunicorn
RUN pip install psycopg2-binary
RUN pip install -r requirements.txt

CMD ["gunicorn", "--bind", ":80", "core.wsgi:application", "--log-level", "debug"]