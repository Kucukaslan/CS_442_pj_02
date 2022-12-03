import os
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
        self, pid, cwNeighbourPid, ccwNeighbourPid, constants, ospid=os.getpid(), holder=None
    ):
        random.seed(ospid)
        self.pid = pid
        self.ospid = ospid
        self.hungry = False
        self.using = False
        self.holder = holder  # self?
        self.asked = False
        self.pending_requests = False
        self.ci = channel.Channel()
        self.cwNeighbourPid = cwNeighbourPid
        self.ccwNeighbourPid = ccwNeighbourPid
        self.constants: Constants = constants
        self.write_count = 0
        self.start_time = time.time()

        self.Incoming = self.ci.join(f"{str(pid)}-inc")

        self.OutgoingToken = []
        while len(self.OutgoingToken) == 0:
            self.OutgoingToken = self.ci.subgroup(f"{str(ccwNeighbourPid)}-inc")

        self.OutgoingRequest = []
        while len(self.OutgoingRequest) == 0:
            self.OutgoingRequest = self.ci.subgroup(f"{str(cwNeighbourPid)}-inc")
        print(
            " ".join(
                [
                    "\n",
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
        )

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
        self.hungry = True
        if self.holder is not self:  # we don’t have token
            if not self.asked:  # if not send req already
                # todo send request to right(CCW dir)
                self.ci.sendTo(self.OutgoingRequest, "ResReq")
                self.asked = True
            # todo wait until (using == True)
        else:  # // we have token
            self.using = True
            # todo update the DATAFILE and log it
            self.hungry = False

    def send_token(self):
        pass

    def request_token(self):
        if (self.holder is self) and (not self.using):
            0  # todo  send token (CW) // we send token
        else:  # (self.holder != self) or (self.using)
            self.pending_requests = True
            if (self.holder != self) and (not self.asked):
                # todo send request (CCW dir)
                self.asked = True

    def use_resource(self):
        file = open(self.constants.DATAFILE, "r+")
        lines = file.readlines[0]
        cur_num = int(lines[0]) + self.constants.DELTA
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
        self.asked = False
        if self.hungry:  # if we asked
            self.using = True
            self.hungry = False
            self.use_resource()
        else:  # pass token; left asked
            self.send_token()
            self.pending_requests = False

    def release_resource(self):
        self.using = False
        if self.pending_requests:
            # todo send token (CW)
            self.pending_requests = False
        else:
            self.holder = self  # we have token
        self.sleep()

    def sleep(self):
        sleep_time = random.randint(0, self.constants.MAXTIME)
        time.sleep(sleep_time)

    def run(self):
        self.ci.sendTo(
            self.OutgoingRequest,
            f"from {self.Incoming}({self.pid}) to {self.OutgoingRequest[0]}({self.cwNeighbourPid}) ResReq",
        )
        self.ci.sendTo(
            self.OutgoingToken,
            f"from {self.Incoming}({self.pid}) to {self.OutgoingToken[0]}({self.ccwNeighbourPid}) Token",
        )

        while True:
            msg = self.ci.recvFromAny()
            sender_pid = msg[0]
            msg = msg[1:]
            # print(" ".join(["\n", str(sender_pid), "\n", str(msg), "\n"]))
            if sender_pid == self.OutgoingRequest[0]:
                # Token came in
                out = f"""Check Token? channelid(pid)
                      from {sender_pid}({self.cwNeighbourPid})
                      to   {self.Incoming}({self.pid})
                      msg  {msg[0]}
                      """
                print(out)

                # print(" ".join(["\nToken?", str(sender_pid), "\n", str(msg), "\n"]))
            elif sender_pid == self.OutgoingToken[0]:
                # Resource request came in
                out = f"""Check ResReq? channelid(pid)
                      from {sender_pid}({self.ccwNeighbourPid})
                      to   {self.Incoming}({self.pid})
                      msg  {msg[0]}
                      """
                print(out)
