run:
	echo 0 > DATAFILE
	echo "" > DATAFILE

	python3 ./main.py 5 DATAFILE 10 10 LOGFILE 10000
tar:
	tar czf  ./21901779.tar.gz *akefile *.py *.md  *.pdf

rd:
	redis-server &
	redis-cli ping








