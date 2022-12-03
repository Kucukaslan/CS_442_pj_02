import os
import custom_channel as channel
from node import Node
import time
import sys
from constants import Constants


def main():
    """ "
    token.py NP DATAFILE DELTA TOTCOUNT LOGFILE MAXTIME
    """
    if len(sys.argv) != 7:
        print("token.py NP DATAFILE DELTA TOTCOUNT LOGFILE MAXTIME")
        sys.exit(1)

    constants = Constants(
        NP=int(sys.argv[1]),
        DATAFILE=sys.argv[2],
        DELTA=int(sys.argv[3]),
        TOTCOUNT=int(sys.argv[4]),
        LOGFILE=sys.argv[5],
        MAXTIME=int(sys.argv[6]),
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

    chan = channel.Channel()
    chan.channel.flushall()

    processes = []
    NP = constants.NP
    for i in range(NP):
        pid = os.fork()
        if pid == 0:
            node = Node(
                pid=i,
                cwNeighbourPid=((i + 1) % NP),
                ccwNeighbourPid=((i - 1) % NP),
                constants=constants,
            )
            node.run()
            print(f"OS :: Client process {i} is started!")
        else:
            processes.append(pid)


main()


def oldmain():
    chan = channel.Channel()
    chan.channel.flushall()

    processes = []
    pid = os.fork()
    if pid == 0:
        server = Server()
        server.run()
        print("OS :: Server process is done!")
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
            print(f"OS :: Client process {i} is done!")
            os._exit(0)
        else:
            processes.append(pid)

    while processes:
        pid, exit_code = os.wait()
        if pid > 0:
            processes.remove(pid)

    print(
        "\n***************************************\n**** All child processes are done! ****\n***************************************"
    )


# oldmain()
