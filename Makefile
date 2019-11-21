userns: ./main.c
	gcc -O2 -static -o $@ $<
