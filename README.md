# sgc-web
## Megatlon web app


### Installation of project

- Install python v>=3.8 x64 adding to PATH

- Install git (if don't have it)

- Clone this repository:
```bash
git clone https://github.com/lucaslucyk/sgc-web.git
cd scg-web
cd scg
```

- Install dependencies:
```bash
python -m pip install requirements.txt -r
```

- Generate and run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

- (ERROR ONLY) Repare conection between poroject and database:
```bash
python manage.py migrate --run-syncdb
```

- Create superuser completing specific data:
```bash
python manage.py createsuperuser
...
```

- Run server:
```bash
python manage.py runserver
```

- For stop server, use CTRL+C.

*To use a third party database or web-server, use the corresponding settings* 

### Application Guide
...

