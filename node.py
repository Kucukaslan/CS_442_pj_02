import os
import sys,multiprocessing
from  threading import Lock,RLock, Thread #.Lock as Lock
import custom_channel as channel
import random
from constants import Constants
import time

class Node:
    """
    Receive a token from the predecessor
    Send a token to the successor
    
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
        self, pid, predecessor, successor, constants, holder=False
    ):
        # log parameters
        print(f"pid={pid}, predecessor={predecessor}, successor={successor}, ospid={os.getpid()}, holder={holder}")

        random.seed(pid)
        self.lock = RLock()

        with self.lock:
            self.pid = pid
            self.ospid = os.getpid()
            self.hungry = False
            self.using = False
            self.holder = holder 
            self.asked = False
            self.pending_requests = False

            self.predecessor = predecessor
            self.successor = successor
            self.constants: Constants = constants
            self.write_count = 0
            self.start_time = time.time()

            self.ci = channel.Channel()
            self.ci.join(f"{str(self.pid)}-inc")
            # It seems to me that directions are fkced up
            self.Incoming = self.ci.subgroup(f"{str(self.pid)}-inc")

            self.OutgoingToken = []
            while len(self.OutgoingToken) == 0:
                self.OutgoingToken = self.ci.subgroup(f"{str(successor)}-inc")
                time.sleep(1)

            self.OutgoingRequest = []
            while len(self.OutgoingRequest) == 0:
                self.OutgoingRequest = self.ci.subgroup(f"{str(predecessor)}-inc")
        
        
        msg =    " ".join(
                [
                    "\nA node is initialized with: ",
                    "predecessor",
                    str(self.predecessor),
                    "pid ",
                    str(self.pid),
                    "successor",
                    str(self.successor),
                    "Incoming",
                    str(self.Incoming),
                    "OutgoingToken",
                    str(self.OutgoingToken),
                    "OutgoingRequest",
                    str(self.OutgoingRequest),
                ]
            )
        print(msg)

    def run(self):
        """
        The Node will start ordinary execution.
        It will create two threads:
            1. A thread to listen for incoming messages
            2. A thread for waiting/sleeping for a random time before sending a request
        """
        print(f"Node {self.pid} is starting")
        self.start_time = time.time()
        listen_thread = self.start_listening()
        sleep_thread = self.start_sleeping()
        #self.listen()
# todo    listen_thread.join()
#       todo wait sleep and kill listen thread
        sleep_thread.join()
        sys.exit(0)

    def start_listening(self):
        """
        Start a thread to listen for incoming messages
        """
        t = Thread(target=self.listen)
        t.start()
        return t

    def start_sleeping(self):
        """
        Start a thread to sleep for a random time before accessing the resource
        """
        t = Thread(target=self.sleep)
        t.start()
        return t

    def listen(self):
        """
        Listen for incoming messages
        """
        while True:
            print(f"{self.pid} is listening for messages to {self.Incoming}")
            # todo delete this
            msg = self.ci.recvFrom(self.Incoming, timeout=1)
            if msg is not None:
                print("The message: ",msg) 
                if msg[1] == "TOKEN":
                    self.handle_token()
                elif msg[1] == "REQUEST":
                    self.handle_request()
                else:
                    print("Unknown message: ", msg)
            
    
    def sleep(self):
        """
        Sleep for a random time up to self.MAXTIME ms before accessing the resource
        """
        while True:
            time.sleep(random.randint(0, self.constants.MAXTIME)/1000)
            self.set_hungry()
    
    def set_hungry(self):
        """
        Set the node to hungry
        """
        with self.lock:
            self.hungry = True

            if self.holder:
                self.using=True
                self.use_resource()
                self.hungry=False
                self.using=False
                print(f"{self.pid} used token, pending: {self.pending_requests}")
                if self.pending_requests:
                    self.pending_requests = False
                    print(f"{self.pid} will send token to: ",self.OutgoingToken, self.successor)
                    self.ci.sendTo(self.OutgoingToken, "TOKEN")
                    print("Token sent to: ",self.OutgoingToken, self.successor)
            elif not self.asked:
                self.asked=True
                self.ci.sendTo(self.OutgoingRequest, "REQUEST")
                print(f"{self.pid} Sent request to: ",self.OutgoingRequest, self.predecessor)
            # todo wait until using?
    
    def handle_token(self):
        """
        Handle the token
        """
        print(f"{self.pid} received token from: ",self.predecessor)
        with self.lock:
            self.holder = True
            self.asked = False
            if self.hungry:
                self.using=True
                self.use_resource()
                self.hungry=False
                self.using=False
            
            if self.pending_requests:
                self.pending_requests = False
                self.ci.sendTo(self.OutgoingToken, "TOKEN")
                print(f"{self.pid} Sent request to: ",self.OutgoingToken, self.OutgoingToken)


    def handle_request(self):
        """
        Handle the request
        """
        print(f"{self.pid} received request from: ",self.successor)
        with self.lock:
            print(f"{self.pid} is handling request from: holder:{self.holder}",self.successor)
            if self.holder:
                self.holder = False
                self.ci.sendTo(self.OutgoingToken, "TOKEN")
                print(f"{self.pid} Sent token to: ",self.OutgoingToken, self.successor)
            else:
                self.pending_requests = True
                if not self.asked:
                    print(f"{self.pid} Will send request to: ",self.OutgoingRequest, self.predecessor)
                    self.ci.sendTo(self.OutgoingRequest, "REQUEST")
                    self.asked = True
                    print(f"{self.pid} Sent request to: ",self.OutgoingRequest, self.predecessor)
                else:
                    print(f"{self.pid} already asked for token")




    # def set_hungry(self):
    #     with self.lock:
    #         self.hungry = True
        
    #         if self.holder :  # // we have token
    #             self.using = True
    #             self.use_resource()
    #             self.release_resource()
    #             self.hungry = False
    #             self.send_token()
    #         else:  # we don’t have token
    #             if not self.asked:  # if not send req already
    #                 self.ci.sendTo(self.OutgoingRequest, "ResReq")
    #                 self.asked = True
    #             # todo wait until (using == True)

    # # DO NOT LOCK THE CALLER SHOULD LOCK
    # def send_token(self):
    #     with self.lock:     
    #         self.holder = False
    #         self.ci.sendTo(self.OutgoingToken, "TOKEN")
    #         pass


    # def request_token(self):
    #     """
    #     When a request is received
    #     """
    #     if (self.holder is True) and (not self.using):
    #         self.send_token()
    #     else:  # (self.holder != self) or (self.using)
    #         self.pending_requests = True
    #         if (not self.holder ) and (not self.asked):
    #             self.ci.sendTo(self.OutgoingRequest, "ResReq")
    #             self.asked = True

    # DO NOT LOCK, THE CALLER SHOULD LOCK
    def use_resource(self):
        file = open(self.constants.DATAFILE, "r")
        lines = file.readlines()
        file.close()
        if len(lines) == 0 or not lines[0].isnumeric():
            lines = [str(self.constants.DELTA*self.write_count)]
            print("No data was found in file, writing: ", lines[0])
        cur_num = int(lines[0]) + self.constants.DELTA
        n_updates = self.write_count
        if len(lines) > 1:
            print("defaulting n_updates: ", n_updates)
            n_updates = int(lines[1]) + 1
        to_be_written = str(cur_num) + '\n' + str(n_updates)
        if n_updates < self.constants.TOTCOUNT:
            file = open(self.constants.DATAFILE, "w")
            file.write(to_be_written)
            file.close()
        else:
            # graceful exit
            print("Node ", self.pid, " is exiting")
            print("Max number reached, sending token to", self.OutgoingToken, self.successor)
            # send token to ccw neighbour
            self.ci.sendTo(self.OutgoingToken, "TOKEN")
            print("Node ", self.pid, " is exiting, sent token to", self.OutgoingToken, self.successor)
            #sys.exit(0)
            multiprocessing.current_process().terminate()

        self.write_count += 1
        file = open(self.constants.LOGFILE, "a")
        elapsed_time = (time.monotonic_ns() / 1000000) - self.constants.START_TIME 
        log_text = f"t={elapsed_time}, pid={self.pid}, ospid={self.ospid}, new={cur_num}, {n_updates}, count={self.write_count}\n"
        file.write(log_text)
        file.close()
        print(f"-- {self.pid} ---\n", to_be_written, "\n", log_text, "\n")

    # def receive_token(self):
    #     with self.lock:
    #         self.asked = False
    #         if self.hungry:  # if we asked
    #             self.using = True
    #             self.hungry = False
    #             self.use_resource()
    #             self.release_resource()
    #         else:  # pass token; left asked
    #             self.pending_requests = False
    #             self.send_token()


    # def release_resource(self):
    #     self.using = False
    #     if self.pending_requests:
    #         self.send_token()
    #         self.holder=False
    #         self.pending_requests = False
    #     else:
    #         self.holder = True  # we have token

    # def sleep(self):
    #     sleep_time = random.randint(0, self.constants.MAXTIME)
    #     print(f"pid {self.pid} will sleep for {sleep_time} seconds")
    #     time.sleep(sleep_time/1000)
    #     print(f"pid {self.pid} started requesting token")
    #     self.set_hungry()

    # def run(self):
    #     thread = Thread(target = self.sleep)
    #     thread.start()
    
    #     while True:
    #         msg = self.ci.recvFromAny()
    #         sender_pid = msg[0]
    #         msg = msg[1:]
    #         # print(" ".join(["\n", str(sender_pid), "\n", str(msg), "\n"]))
    #         if msg[0] == "Token":
    #             # Token came in
    #             out = f"""Check Token? channelid(pid)
    #                   from {sender_pid}({self.predecessor})
    #                   to [me]   {self.Incoming}({self.pid})
    #                   msg  {msg[0]}
    #                   """
    #             print(out)
    #         elif msg[0] == "ResReq":
    #             # ResReq came in
    #             out = f"""Check ResReq? channelid(pid)
    #                   from {sender_pid}({self.successor})
    #                   to [me]   {self.Incoming}({self.pid})
    #                   msg  {msg[0]}
    #                   """
    #             print(out)
    #         else:
    #             print("Error: Unknown message type")
    #             print(msg)
                
    #     thread.join()
    #     return
