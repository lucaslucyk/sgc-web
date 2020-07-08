# SGC-WEB (Class Management System)

![python3.8](https://img.shields.io/badge/python-v3.8-blue)
![django2.2](https://img.shields.io/badge/django-v2.2-blue)
![winx86/64](https://img.shields.io/badge/OS-win%20x86%2Fx64-lightgrey)
![winx86/64](https://img.shields.io/badge/license-GPL%20v3-brightgreen)

## Project install

- Install python 3.8 (or high) x64 adding to PATH

- Install git (if don't have it)

- Clone this repository:
```bash
> git clone https://github.com/lucaslucyk/sgc-web.git
> cd scg-web
> cd scg
```

- Install dependencies:
```bash
> python -m pip install requirements.txt -r
```

- Generate and run migrations:
```bash
> python manage.py makemigrations
> python manage.py migrate
```

- (ERROR ONLY) Repare conection between poroject and database:
```bash
> python manage.py migrate --run-syncdb
```

- Create superuser completing specific data:
```bash
> python manage.py createsuperuser
...
```

- Run server:
```bash
> python manage.py runserver
```

- For stop server, use CTRL+C.

*\* To use a third party database or web-server, use the corresponding settings* 

**\* Scheduled tasks don't work on UNIX OS's**

## Deploy on Microsoft IIS

- Watch on YouTube: [Deploy Django on Windows using Microsoft IIS](https://youtu.be/APCQ15YqqQ0)

### Steps
1. Install IIS on your VM or machine, and enable CGI

    - [How to Install IIS on Windows 8 or Windows 10](https://www.howtogeek.com/112455/how-to-install-iis-8-on-windows-8/)

    - [CGI](https://docs.microsoft.com/en-us/iis/configuration/system.webserver/cgi)

2. Clone repository in `C:/inetpub/wwwroot/`

3. Install Python 3.8 in `C:/Python38`, and install dependences with `requirements.txt`.

4. Navigate to `C:/`, right-click on `Python38`, and edit `Properties`.
Under Security, add `IIS AppPool\DefaultAppPool`. `DefaultAppPool` is the default app pool.
** Ensure the location is local and replicate this for `C:/inetpub/wwwroot/sgc-web/` directory.

5. Enable wfastcgi

    - Open a CMD terminal as Administrator, change directory with `cd C:\` and run the command `wfastcgi-enable`. 
    
    - Copy the Python path, and replace the `scriptProcessor="<to be filled in>"` in config/iis/web-config-template with the Python path returned by `wfastcgi-enable`.

6. Edit the remaining settings in `web-config-template` then save it as `web.config` in the `C:/inetpub/wwwroot/` directory. It should NOT sit inside `sgc-web/`. Other settings can be modified if `sgc-web` does NOT sit at `C:/inetpub/wwwroot/`

    - Edit project `PYTHONPATH` (path to your project what includes `manage.py`)

    - Edit `WSGI_HANDLER` (located in your `wsgi.py`)

    - Edit `DJANGO_SETTINGS_MODULE` (your `settings.py` module)

7. Open Internet Information Services (IIS) Manager. Under connections select the server, then in the center pane under Management select Configuration Editor. Under Section select system.webServer/handlers. Under Section select Unlock Section. This is required because the `C:/inetpub/wwwroot/web.config` creates a [route handler](https://pypi.org/project/wfastcgi/#route-handlers) for our project.

8. Run `manage.py collectstatic` for load all staticfiles in `publish/static/` folder.

9. Create folder `publish/media/` and copy `web.config` file from `publish/static/`.

10. Add Virtual Directory. In order to enable serving static files map a static alias to the static directory, `C:/inetpub/wwwroot/sgc-web/publish/static/`

11. Add Virtual Directory. In order to enable serving media files map a media alias to the media directory, `C:/inetpub/wwwroot/sgc-web/publish/media/`

9. Refresh the server and navigate to `localhost`

## Application Guide
...

