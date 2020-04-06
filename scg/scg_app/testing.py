def accion():
	def get_id(ids:str):
		ids.split()
		return ids[0] if ids else None

	_id = get_id("4 56 78 1")
	return(_id)


if __name__ == '__main__':
	print(accion())
