FROM python:3.8

ENV PYTHONUNBUFFERED 1
RUN mkdir /code

WORKDIR /code
COPY . /code/

RUN python -m pip install -r scg/requirements.txt
RUN python scg/manage.py makemigrations
RUN python scg/manage.py migrate
RUN python scg/manage.py collectstatic --noinput

CMD ["gunicorn", "-c", "config/gunicorn/conf.py", "--bind", "0.0.0.0:8000", "--chdir", "scg", "scg.wsgi:application"]