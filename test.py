import os
import custom_channel as channel
from client_server import Client, Server
import time
import sys

def main():
    """"
    token.py NP DATAFILE DELTA TOTCOUNT LOGFILE MAXTIME
    """ 
    if len(sys.argv) != 7:
        print('token.py NP DATAFILE DELTA TOTCOUNT LOGFILE MAXTIME')
        sys.exit(1)
    NP = int(sys.argv[1])
    DATAFILE = sys.argv[2]
    DELTA = int(sys.argv[3])
    TOTCOUNT = int(sys.argv[4])
    LOGFILE = sys.argv[5]
    MAXTIME = int(sys.argv[6])

    print(f'NP = {NP}')
    print(f'DATAFILE = {DATAFILE}')
    print(f'DELTA = {DELTA}')
    print(f'TOTCOUNT = {TOTCOUNT}')
    print(f'LOGFILE = {LOGFILE}')
    print(f'MAXTIME = {MAXTIME}')    
main()

chan = channel.Channel()
chan.channel.flushall()

processes = []
pid = os.fork()
if pid==0:
    server = Server()
    server.run()
    print('OS :: Server process is done!')
    os._exit(0)
else:
    processes.append(pid)

for i in range(10):
    pid = os.fork() 
    if pid == 0:
        client = Client()
        shutdown = i == 9
        if shutdown:
            time.sleep(1)
        client.run(shutdown=shutdown)
        print(f'OS :: Client process {i} is done!')
        os._exit(0)
    else:
        processes.append(pid)

while processes:
    pid, exit_code = os.wait()
    if pid > 0 :
        processes.remove(pid)

print('\n***************************************\n**** All child processes are done! ****\n***************************************')