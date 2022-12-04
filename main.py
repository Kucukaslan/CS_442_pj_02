import os
import custom_channel as channel
from node import Node
import time
import sys
from constants import Constants

def main():
    """ 
    main.py NP DATAFILE DELTA TOTCOUNT LOGFILE MAXTIME
    """
    if len(sys.argv) != 7:
        print(f"Usage: python3 {os.path.basename(sys.argv[0])} <np> <datafile> <delta> <totcount> <logfile> <maxtime>")
        print(f"Example:\n python3 {os.path.basename(sys.argv[0])} 5 DATAFILE 100 25 LOGFILE 1000")

        sys.exit(1)

    constants = Constants(
        NP=int(sys.argv[1]),
        DATAFILE = sys.argv[2],
        DELTA = int(sys.argv[3]),
        TOTCOUNT = int(sys.argv[4]),
        LOGFILE = sys.argv[5],
        MAXTIME = int(sys.argv[6]),
        START_TIME = time.monotonic_ns() / 1000000
    )

    print(f"NP = {constants.NP}")
    print(f"DATAFILE = {constants.DATAFILE}")
    print(f"DELTA = {constants.DELTA}")
    print(f"TOTCOUNT = {constants.TOTCOUNT}")
    print(f"LOGFILE = {constants.LOGFILE}")
    print(f"MAXTIME = {constants.MAXTIME}")
    assert constants.NP <= 20
    assert 2 <= constants.NP
    assert 1 <= constants.DELTA
    assert constants.MAXTIME > 0


    chan = channel.Channel()
    chan.channel.flushall()

    processes = []
    NP = constants.NP
    for i in range(NP):
        pid = os.fork()
        if pid == 0:
           # print(f"OS :: Child process {i} is started!")
            holder = False
            if i == 0:
                holder=True
            node = Node(
                pid=i, predecessor=((i - 1) % NP), successor=((i+1) % NP), constants=constants, holder=holder
            )
            print(f"OS :: Calling node.run() for {i}")
            node.run()
            print(f"OS :: Child process {i} is finished!")
        else:
            processes.append(pid)

    while processes:
        print(f"OS :: Waiting for child process {processes[0]}")
        pid, exit_code = os.wait()
        if pid > 0:
            processes.remove(pid)
            print(f"OS :: Child process {pid} is terminated with exit code {exit_code}")

    print(
        "\n***************************************\n**** All child processes are done! ****\n***************************************"
    )

main()

