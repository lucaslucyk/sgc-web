FROM python:3.8

ENV PYTHONUNBUFFERED 1
RUN mkdir /code

WORKDIR /code
COPY . /code/

RUN python -m pip install -r scg/requirements.txt

CMD ["gunicorn", "-c", "config/gunicorn/conf.py", "--bind", "0.0.0.0:8000", "--chdir", "scg", "scg.wsgi:application"]