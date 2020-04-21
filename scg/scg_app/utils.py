""" Utils for internal use """

import datetime

def grouped(iterable, n=2):
    """  Agrupa los elementos de un iterable para obtener conjuntos de n elementos """
    aux = iter(iterable)
    return zip(*[aux] * n)

def get_min_offset(_time:datetime.time, _mins:int, _sub=False) -> datetime.time:
    """ return datetime.time object adding mins to hour received """
    fulldate = datetime.datetime(100, 1, 1, _time.hour, _time.minute, _time.second)
    if _sub:
        fulldate = fulldate - datetime.timedelta(minutes=_mins)
    else:
        fulldate = fulldate + datetime.timedelta(minutes=_mins)
    return fulldate.time()

# def handle_uploaded_file(f):
#     with open('some/file/name.txt', 'wb+') as destination:
#         for chunk in f.chunks():
#             destination.write(chunk)

# if __name__ == '__main__':
#   for x, y in grouped(range(11), 2):
#       print(x, y)