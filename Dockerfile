FROM continuumio/anaconda3

RUN apt-get update
RUN apt-get install docker.io -y

RUN mkdir -p /usr/share/man/man1 /usr/share/man/man2
RUN apt-get install -y --no-install-recommends openjdk-11-jre
RUN curl -s https://get.nextflow.io | bash
RUN chmod +x nextflow
RUN mv nextflow /usr/local/bin

RUN mkdir -p /home/app

WORKDIR /home/app

COPY ./core ./core
COPY ./peka ./peka
COPY ./manage.py ./manage.py
COPY ./requirements.txt ./requirements.txt

RUN pip install gunicorn
RUN pip install psycopg2-binary
RUN pip install -r requirements.txt

CMD ["gunicorn", "--bind", ":80", "core.wsgi:application", "--log-level", "debug"]