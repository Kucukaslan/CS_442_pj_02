run:
	echo 0 > DATAFILE
	echo "" > DATAFILE

	python3 ./main.py 7 DATAFILE 10 20 LOGFILE 5000
tar:
	tar czf  ./21901779.tar.gz *akefile *.py *.md  *.pdf

rd:
	redis-cli flushall
	redis-cli shutdown
	redis-server &
	redis-cli flushall
	redis-cli ping
k:
	ps aux | awk '/main.py/ {print $$2}'  | xargs kill









