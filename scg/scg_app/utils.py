""" Utils for internal use """
from zeep import Client
import datetime
from django.conf import settings

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

# def handle_uploaded_file(f):
#     with open('some/file/name.txt', 'wb+') as destination:
#         for chunk in f.chunks():
#             destination.write(chunk)

# if __name__ == '__main__':
#   for x, y in grouped(range(11), 2):
#       print(x, y)
