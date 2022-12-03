import os
import custom_channel as channel


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
        self, pid, cwNeighbourPid, ccwNeighbourPid, ospid=os.getpid(), holder=None
    ):
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

        self.Incoming = self.ci.join(f"{str(pid)}-inc")

        self.OutgoingToken = []
        while len(self.OutgoingToken) == 0:
            self.OutgoingToken = self.ci.subgroup(f"{str(ccwNeighbourPid)}-inc")

        self.OutgoingRequest = []
        while len(self.OutgoingRequest) == 0:
            self.OutgoingRequest = self.ci.subgroup(f"{str(cwNeighbourPid)}-inc")
        print(
            "cwNeighbourPid ",
            self.cwNeighbourPid,
            "\n",
            "pid ",
            self.pid,
            "\n",
            "ccwNeighbourPid ",
            self.ccwNeighbourPid,
            "\n",
            "Incoming",
            self.Incoming,
            "\n",
            "OutgoingToken ",
            self.OutgoingToken,
            "\n",
            "OutgoingRequest",
            self.OutgoingRequest,
            "\n",
        )

        os._exit(0)
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

    def request_token(self):
        if (self.holder is self) and (not self.using):
            0  # todo  send token (CW) // we send token
        else:  # (self.holder != self) or (self.using)
            self.pending_requests = True
            if (self.holder != self) and (not self.asked):
                # todo send request (CCW dir)
                self.asked = True

    def receive_token(self):
        self.asked = False
        if self.hungry:  # if we asked
            self.using = True
            self.hungry = False
            # todo will use resource
        else:  # pass token; left asked
            # todo send token (CW)
            self.pending_requests = False

    def release_resource(self):
        self.using = False
        if self.pending_requests:
            # todo send token (CW)
            self.pending_requests = False
        else:
            self.holder = self  # we have token

    def run(self):
        while True:
            msg = self.ci.recvFromAny()
            sender_pid = msg[0]
            msg = msg[1:]
            if sender_pid == self.OutgoingRequest[0]:
                # Token came in
                pass
            elif sender_pid == self.OutgoingToken[0]:
                # Resource request came in
                pass
