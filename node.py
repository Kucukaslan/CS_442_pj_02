import os
import sys
from  threading import Lock, Thread #.Lock as Lock
import custom_channel as channel
import random
from constants import Constants
import time

class Node:
    """
    A node in the token ring algorithm with requests.
    Variables in a node:
        hungry: True when the node wants to access the resource
        using: True when the node is accessing the resource
        holder = self: node has the token
        holder ≠ self: node does not have token
        asked: True or False
    We ask for token. Set asked to True
    We send a request for token.
    If request sent already (asked is True), we don’t send again.
    When token comes, we set to asked to False.
    pending_requests: True or False
        Indicates that there is a hungry node on left.
    After using the resource we need to pass the token, i.e., move the token. Otherwise, token can stay with us.
    """

    def __init__(
        self, pid, cwNeighbourPid, ccwNeighbourPid, constants, holder=False
    ):
        # log parameters
        print(f"pid={pid}, cwNeighbourPid={cwNeighbourPid}, ccwNeighbourPid={ccwNeighbourPid}, ospid={os.getpid()}, holder={holder}")

        random.seed(pid)
        self.lock = Lock()

        with self.lock:
            self.pid = pid
            self.ospid = os.getpid()
            self.hungry = False
            self.using = False
            self.holder = holder 
            self.asked = False
            self.pending_requests = False

            self.ci = channel.Channel()
            self.cwNeighbourPid = cwNeighbourPid
            self.ccwNeighbourPid = ccwNeighbourPid
            self.constants: Constants = constants
            self.write_count = 0
            self.start_time = time.time()


        self.Incoming = self.ci.join(f"{str(self.pid)}-inc")
#        print("joined incoming {" + str(self.Incoming) + "} pid {" + str(self.pid) + "}")

        self.OutgoingToken = []
        while len(self.OutgoingToken) == 0:
   #         print("will try to join outgoing token")
            self.OutgoingToken = self.ci.subgroup(f"{str(ccwNeighbourPid)}-inc")
  #          print(f"len of outgoing token is {len(self.OutgoingToken)}, type is {type(self.OutgoingToken)} {str(ccwNeighbourPid)}-inc")
            time.sleep(1)
 #       print("joined outgoing token")

        self.OutgoingRequest = []
        while len(self.OutgoingRequest) == 0:
            self.OutgoingRequest = self.ci.subgroup(f"{str(cwNeighbourPid)}-inc")
        
        
        msg =    " ".join(
                [
                    "\nA node is initialized with:\n",
                    "cwNeighbourPid",
                    str(self.cwNeighbourPid),
                    "\n",
                    "pid ",
                    str(self.pid),
                    "\n",
                    "ccwNeighbourPid",
                    str(self.ccwNeighbourPid),
                    "\n",
                    "Incoming",
                    str(self.Incoming),
                    "\n",
                    "OutgoingToken",
                    str(self.OutgoingToken),
                    "\n",
                    "OutgoingRequest",
                    str(self.OutgoingRequest),
                    "\n",
                ]
            )
        print(msg)

    
        # todo delete debug code
        """ 
        if True:
            channelId = f"{str(cwNeighbourPid)}-{str(pid)}"
            self.tokenIngress = self.ci.join(channelId)
            # assert len(self.tokenIngress) == 1
        if True:
            channelId = f"{str(ccwNeighbourPid)}-{str(pid)}"
            self.ReqIngress = self.ci.join(channelId)
            # assert len(self.tokenIngress) == 1
        if True:
            channelId = f"{str(pid)}-{str(ccwNeighbourPid)}"
            self.tokenEgress = []
            while len(self.tokenEgress) == 0:
                self.tokenEgress = self.ci.subgroup(channelId)
            assert len(self.tokenEgress) == 1
        if True:
            channelId = f"{str(pid)}-{str(cwNeighbourPid)}"
            self.ReqEgress = []
            while len(self.ReqEgress) == 0:
                self.ReqEgress = self.ci.subgroup(channelId)
            assert len(self.ReqEgress) == 1
        """

    def set_hungry(self):
        with self.lock:
            self.hungry = True
        
            if self.holder :  # // we have token
                self.using = True
                self.use_resource()
                self.release_resource()
                self.hungry = False
                self.send_token()
            else:  # we don’t have token
                if not self.asked:  # if not send req already
                    self.ci.sendTo(self.OutgoingRequest, "ResReq")
                    self.asked = True
                # todo wait until (using == True)

    # DO NOT LOCK THE CALLER SHOULD LOCK
    def send_token(self):
        with self.lock:     
            self.holder = False
            self.ci.sendTo(self.OutgoingToken, "Token")
            pass


    def request_token(self):
        """
        When a request is received
        """
        if (self.holder is True) and (not self.using):
            self.send_token()
        else:  # (self.holder != self) or (self.using)
            self.pending_requests = True
            if (not self.holder ) and (not self.asked):
                self.ci.sendTo(self.OutgoingRequest, "ResReq")
                self.asked = True

    # DO NOT LOCK, THE CALLER SHOULD LOCK
    def use_resource(self):
        file = open(self.constants.DATAFILE, "r+")
        lines = file.readlines()
        cur_num = int(lines[0]) + self.constants.DELTA
        n_updates = 1
        if len(lines) > 1:
            n_updates = int(lines[1]) + 1
        to_be_written = str(cur_num) + '\n' + str(n_updates)
        file.write(to_be_written)
        file.close()
        self.write_count += 1
        file = open(self.constants.LOGFILE, "a")
        elapsed_time = time.time() - self.start_time
        log_text = f"t={elapsed_time}, pid={self.pid}, ospid={self.ospid}, new={cur_num}, {n_updates}, count={self.write_count}\n"
        file.write(log_text)
        file.close()

    def receive_token(self):
        with self.lock:
            self.asked = False
            if self.hungry:  # if we asked
                self.using = True
                self.hungry = False
                self.use_resource()
                self.release_resource()
            else:  # pass token; left asked
                self.pending_requests = False
                self.send_token()


    def release_resource(self):
        self.using = False
        if self.pending_requests:
            self.send_token()
            self.holder=False
            self.pending_requests = False
        else:
            self.holder = True  # we have token

    def sleep(self):
        sleep_time = random.randint(0, self.constants.MAXTIME)
        print(f"pid {self.pid} will sleep for {sleep_time} seconds")
        time.sleep(sleep_time/1000)
        print(f"pid {self.pid} started requesting token")
        self.set_hungry()

    def run(self):
        thread = Thread(target = self.sleep)
        thread.start()
    
        while True:
            msg = self.ci.recvFromAny()
            sender_pid = msg[0]
            msg = msg[1:]
            # print(" ".join(["\n", str(sender_pid), "\n", str(msg), "\n"]))
            if msg[0] == "Token":
                # Token came in
                out = f"""Check Token? channelid(pid)
                      from {sender_pid}({self.cwNeighbourPid})
                      to [me]   {self.Incoming}({self.pid})
                      msg  {msg[0]}
                      """
                print(out)
            elif msg[0] == "ResReq":
                # ResReq came in
                out = f"""Check ResReq? channelid(pid)
                      from {sender_pid}({self.ccwNeighbourPid})
                      to [me]   {self.Incoming}({self.pid})
                      msg  {msg[0]}
                      """
                print(out)
            else:
                print("Error: Unknown message type")
                print(msg)
                
        thread.join()
        return
