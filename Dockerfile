FROM continuumio/anaconda3

RUN mkdir -p /home/app

WORKDIR /home/app

COPY ./core ./core
COPY ./manage.py ./manage.py
COPY ./requirements.txt ./requirements.txt

RUN pip install gunicorn
RUN pip install psycopg2-binary
RUN pip install -r requirements.txt

CMD ["gunicorn", "--bind", ":80", "core.wsgi:application", "--log-level", "debug"]