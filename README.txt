USAGE

	make
	./userns ./main.c


	userns: user:[4026531837]
	process  euid     1001
	process  egid     1002
	file     uid      1001
	file     gid      1002
	userns: user:[4026532714]
	process  euid     0
	process  egid     65534
	file     uid      0
	file     gid      65534

