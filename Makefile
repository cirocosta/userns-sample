userns: ./userns.c
	gcc -O2 -static -o $@ $<

samples: sample-0 sample-1000 sample-1001
.PHONY: samples


sample-%:
	mkdir -p ./samples
	touch ./samples/$*.txt
	sudo chown $* ./samples/$*.txt
	sudo chmod 0400 ./samples/$*.txt
