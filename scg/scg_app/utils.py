from typing import Iterable, Tuple, TypeVar

T = TypeVar("T")

def grouped(iterable: Iterable[T], n=2) -> Iterable[Tuple[T, ...]]:
    """  Agrupa los elementos de un iterable para obtener conjuntos de n elementos """
    aux = iter(iterable)
    return zip(*[aux] * n)

# if __name__ == '__main__':
# 	for x, y in grouped(range(11), 2):
# 		print(x, y)