""" Utils for internal use """
import datetime
from zeep import Client
from django.conf import settings
from scg_app import models
from string import digits as str_digits, ascii_lowercase as str_letters
from random import choice as r_choice

from django.utils.text import slugify
from typing import Any

def grouped(iterable, n=2):
    """ Agrupa los elementos de un iterable para obtener conjuntos
        de n elementos """

    aux = iter(iterable)
    return zip(*[aux] * n)

def get_min_offset(_time: datetime.time, _mins: int, _sub=False) -> datetime.time:
    """ return datetime.time object adding mins to hour received """
    fulldate = datetime.datetime(100, 1, 1, _time.hour, _time.minute, _time.second)
    if _sub:
        fulldate = fulldate - datetime.timedelta(minutes=_mins)
    else:
        fulldate = fulldate + datetime.timedelta(minutes=_mins)
    return fulldate.time()

def get_dia_display(*args):
    to_dict = dict(settings.DIA_SEMANA_CHOICES)
    return [to_dict.get(str(char)) for char in args]

def pull_netTime(container, _fields=[], _filter=''):
    """ Pull from nettime with listfields method,
        Use args how fields and can use filter parameter for specific cases.
    """

    results = list()
    try:
        client = Client(settings.SERVER_URL)
        ns4 = client.type_factory('ns4')
        aos = ns4.ArrayOfstring(_fields)

        nt_response = client.service.ListFields(container, aos, _filter)

        for db_records in nt_response["KeyValueOfstringanyType"]:
            result = dict()
            for data in db_records["Value"]["Data"]["KeyValueOfstringanyType"]:
                result[data['Key']] = data['Value']
            results.append(result)

    except Exception as error:
        raise error
    
    return {container: results}


def pull_nt_clockings(_employee, _start, _end, _type):
    """ Pull clockings from nettime with Clockings method,
        Use parameters for get data. """

    response = []
    try:
        client = Client(settings.SERVER_URL)
        response = client.service.Clockings(_employee, _start, _end, _type)

    except Exception as error:
        raise error

    return response

### permissions ###

def check_admin(user):
    """ returns if a user is a superuser """

    return user.is_superuser

def sedes_available(user):
    """ returns the Sedes on which the user has permission """

    if user.is_superuser:
        return models.Sede.objects.all()

    return user.sedes.all()

def has_sede_permission(user, *sedes, operator: str = "AND"):
    """ Inform if a user has permission in a sede/s.
        Can use AND (default) or OR operator for compare if all or any sede \
        match/es. """

    if user.is_superuser:
        return True

    if operator == "AND":
        return all(sede in user.sedes.all() for sede in sedes)

    if operator == "OR":
        return any(sede in user.sedes.all() for sede in sedes)

    return False


def random_str(size=10, chars=str_digits + str_letters):
    """ Return a str of 'size' len with numbers and ascii lower letters. """

    return ''.join(r_choice(chars) for _ in range(size))

def unique_slug_generator(instance: Any, to_slug: str, field: str='slug', \
        append_random: bool=False):
    """ Return a slug text checking what the property exists and duplicate \
        does not exits. """
    
    if getattr(instance, field, '__ne__') == '__ne__':
        raise AttributeError('La clase {} no posee el atributo {}'.format(
            instance.__class__.__name__, field))

    if getattr(instance, field):
        return getattr(instance, field)

    if not append_random:
        slug = slugify(to_slug)
    else:
        slug = f'{slugify(to_slug)}-{random_str()}'

    if instance.__class__.objects.filter(**{field: slug}).exists():
        #recursion activate
        slug = unique_slug_generator(instance, to_slug, append_random=True)

    return slug
        
def datetime_to_array(date: datetime.date, time: datetime.datetime=None):
    return [
        date.year,
        date.month - 1, #FIX because first month is 0 in frontend
        date.day,
        time.hour if time else None,
        time.minute if time else None,
    ]


def overlap(start1, end1, start2, end2):
    TIME_FORMAT = '%H:%M'
    #transform time
    # start1_time = datetime.strptime(start1, TIME_FORMAT)
    # end1_time = datetime.strptime(end1, TIME_FORMAT)
    # start2_time = datetime.strptime(start2, TIME_FORMAT)
    # end2_time = datetime.strptime(end2, TIME_FORMAT)

    match_one = min(start1_time, end1_time) <= max(start2_time, end2_time)
    match_two = max(start1_time, end1_time) >= min(start2_time, end2_time)

    #checking conditions
    if match_one and match_two:
        return True
    else:
        return False

# def handle_uploaded_file(f):
#     with open('some/file/name.txt', 'wb+') as destination:
#         for chunk in f.chunks():
#             destination.write(chunk)

# if __name__ == '__main__':
#   for x, y in grouped(range(11), 2):
#       print(x, y)
