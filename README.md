# sgc-web
Megatlon web app


Instalacion y uso del proyecto, paso a paso


- Instalar python x64 (tildar la opcion de escribir en el PATH, eso es mucho muy importante!)

- Instalar git/bitbucket

- Abrir un CMD para usar el resto de los comandos

- (opcional) Checkear que el path este bien seteado corriendo

	> python -V  
	o  
	> py -V

deberia devolver, en mi caso,

	Python 3.8.0

- Correr luego el comando

	> pip install virtualenv

para instalar el modulo de creacion de entornos virtuales (aislados).

- Correr luego (en el directorio a utilizar)

	> python -m virtualenv "."  
	o  
	> python -m virtualenv "path/al/proy/"

- Ir a /Scripts y correr activate.bat

	> cd Scripts  
	> activate.bat  
	(proy) > cd ..

(en este ultimo para volver al top-level del venv, ademas que ya puede verse el tag que aclara que el el venv esta activado efectivamente)

- Una vez dentro del entorno virtual, corremos

	(proy) > pip install django zeep

- Creamos una nueva carpeta (cualquier nombre va a servir) y clonamos el proyecto dentro de dicha carpeta

	(proy) > mkdir proy  
	(proy) > cd proy  
	(proy) > git clone https://baalbla@bitbucket.org/aradoteam/sgc.git

- Una vez instalado y desempaquetado, entramos para ver el proyecto

	(proy) > cd scg

- Brevemente, el proyecto es "scg" y dentro va a haber una carpeta "scg" donde estan los settings principales (pre-seteados). Luego esta una app, "scg_app", que es la que controla el funcionamiento del proyecto, dentro hay varios archivos entre los que destacan "admin.py" (configuraciones para la vista del panel del administrador), "models.py" (donde van a estar los modelos de tablas de la base de datos y su logica interna), "urls.py" (donde se van a ver los patrones de matcheo de las urls) y "views.py" (donde se encuentra el funcionamiento interno de cada sub-url del proyecto, ademas de funciones utiles al mismo y los valores que manejan las vistas). Las vistas se guardan en la carpeta "templates" que engloba las plantillas de html + las apis de django para renderear cada pagina que se requestea.

- Dentro de esta carpeta, para empezar a trabajar hay que crear la base de datos (se crean en base a views.py y generan unos archivos en la carpeta "migrations"), esto se hace con los siguientes comandos

	(proy) > python manage.py makemigrations  
	(proy) > python manage.py migrate

- (opcional) SI por algun motivo en los pasos siguientes tenemos un error que alguna tabla NO existe, hay que correr el siguiente comando para reparar la conexion entre el proyecto y la db

	(proy) > python manage.py migrate --run-syncdb

- Seguidamente, hay que crear un superusuario para manejar la parte de administracion del proyecto

	(proy) > python manage.py createsuperuser

elegir un usuario (no es necesario el mail, puede ir vacio) y contraseña, y repetirla.

- (opcional) Un comando bastante util para interactuar con el server de forma de interprete, desde donde se puede tanto usar la base de datos (crear, borrar y actualizar entradas), crear usuarios, ver los objetos y metodos, etc; es

	(proy) > python manage.py shell

- Por ultimo, para poder usar el servidor interno de django propiamente dicho, se usa el comando

	(proy) > python manage.py runserver

la ventana va a empezar a dar todos los requests y sus estados al momento de hacer la request (200, 404, 303, etc) y se puede salir con CTRL + C. Una vez este el servidor andando, se puede acceder desde un browser a la url http://127.0.0.1:8000 o http://localhost:8000 y desde ahi, ir entrando en las distintas paginas e interactuando con la base de datos (algo limitada por el momento, solo se puede hacer por ahora desde el panel de admin o algunas paginas especificas).
