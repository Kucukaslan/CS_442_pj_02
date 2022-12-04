import os
import sys, signal
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
        # print(f"pid={pid}, predecessor={predecessor}, successor={successor}, ospid={os.getpid()}, holder={holder}")

        random.seed(pid)
        self.lock = RLock()

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

        self.ch = channel.Channel()
        self.ch.join(pid=self.pid, ospid=self.ospid)

        print(f"A node is initialized with: predecessor {self.predecessor}, pid {self.pid}, successor {self.successor}")

    def run(self):
        """
        The Node will start ordinary execution.
        It will create three threads:
            1 & 2. Two  thread to listen for requests and tokens
            3. A thread for waiting/sleeping for a random time before sending a request
        """
        # print(f"Node {self.pid} is starting")
        self.start_time = time.time()
        request_thread = Thread(target=self.start_listening_requests, daemon=True)
        token_thread = Thread(target=self.start_listening_tokens, daemon=True)
        sleep_thread = Thread(target=self.start_sleeping, daemon=True)
        
        request_thread.start()
        token_thread.start()
        sleep_thread.start()

        sleep_thread.join()
        sys.exit(0)

    def start_listening_requests(self):
        """
        listen for incoming requests 
        """
    
        while True:
            msg = self.ch.recvFrom(sender_pid=self.successor)
            #if msg is not None:
                # print(f"{self.successor}-{self.pid} The message:",msg)

            self.handle_request() 

    def start_listening_tokens(self):
        """
        listen for incoming tokens 
        """
        while True:
            msg = self.ch.recvFrom(sender_pid=self.predecessor)
            if msg is not None:
                # print(f"{self.predecessor}-{self.pid} The message:",msg)
                if msg[1] == "TERMINATE":
                    # print(f"{self.pid} ({self.ospid}) received TERMINATE from {self.predecessor}")
                    self.ch.sendTo(receiver_pid=self.successor, message="TERMINATE")
                    os.kill(self.ospid, signal.SIGTERM)
                else:
                    self.handle_token()
                
                
    def start_sleeping(self):
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
                # print(f"{self.pid} ({self.ospid}) used token, pending: {self.pending_requests}")
                if self.pending_requests:
                    self.pending_requests = False
                    # print(f"{self.pid} ({self.ospid}) will send token to: ",self.successor)
                    self.holder=False
                    self.ch.sendTo( receiver_pid=self.successor, message="TOKEN")
                    # print(f"{self.pid} ({self.ospid}) sent token to: ",self.successor)
            elif not self.asked:
                self.ch.sendTo( receiver_pid=self.predecessor, message="REQUEST")
                # print(f"{self.pid} ({self.ospid}) sent request to: ",self.predecessor)
                self.asked=True
            # todo wait until using?
    
    def handle_token(self):
        """
        Handle the token
        """
        # print(f"{self.pid} ({self.ospid}) received token from: ",self.predecessor)
        with self.lock:
            self.holder = True
            self.asked = False
            if self.hungry:
                self.using=True
                self.use_resource()
                self.hungry=False
                self.using=False
            else:
                self.pending_requests = False
                self.holder=False
                self.ch.sendTo( receiver_pid=self.successor, message="TOKEN")
                # print(f"{self.pid} ({self.ospid}) Sent token to: ",self.successor)



            if self.pending_requests:
                self.pending_requests = False
                self.holder=False
                self.ch.sendTo( receiver_pid=self.successor, message="TOKEN")
                # print(f"{self.pid} ({self.ospid}) Sent token to: ",self.successor)

    def handle_request(self):
        """
        Handle the request
        """
        # print(f"{self.pid} ({self.ospid}) received request from: ",self.successor)
        with self.lock:
            # print(f"{self.pid} ({self.ospid}), holder:{self.holder}, is handling request from: ",self.successor)
            if self.holder:
                self.holder=False
                self.ch.sendTo( receiver_pid= self.successor, message="TOKEN")
                # print(f"{self.pid} ({self.ospid}) Sent token to: ", self.successor)
            else:
                self.pending_requests = True
                if not self.asked:
                    # print(f"{self.pid} ({self.ospid}) Will send request to: ", self.predecessor)
                    self.ch.sendTo(receiver_pid=self.predecessor, message="REQUEST")
                    self.asked = True
                    # print(f"{self.pid} ({self.ospid}) Sent request to: ", self.predecessor)
                else:
                    pass
                    # print(f"{self.pid} ({self.ospid}) already asked for token")


    # DO NOT LOCK, THE CALLER SHOULD LOCK
    def use_resource(self):
        file = open(self.constants.DATAFILE, "r")
        lines = file.readlines()
        file.close()
        if len(lines) == 0 or lines[0] == "\n":
            lines = [str(self.constants.DELTA*self.write_count)]
            # print("No data was found in file, writing: ", lines[0])
        cur_num = int(lines[0]) + self.constants.DELTA
        n_updates = self.write_count 
        if len(lines) > 1:
            n_updates = int(lines[1])
        if n_updates < self.constants.TOTCOUNT:
            n_updates = n_updates + 1
            to_be_written = str(cur_num) + '\n' + str(n_updates)
            file = open(self.constants.DATAFILE, "w")
            file.write(to_be_written)
            file.close()
        else:
            # graceful exit
            # print("Node ", self.pid, " is exiting")
            # print(f"Max number reached by {self.pid}, terminating and sending token to", self.successor)
            # send token to successor
            self.holder = False
            self.ch.sendTo( receiver_pid=self.successor, message="TERMINATE")
            # kill the process
            os.kill(os.getpid(), signal.SIGKILL)

            #multiprocessing.current_process().terminate()

        self.write_count += 1
        file = open(self.constants.LOGFILE, "a")
        elapsed_time = (time.monotonic_ns() / 1000000) - self.constants.START_TIME 
        log_text = f"t={elapsed_time}, pid={self.pid + 1}, ospid={self.ospid}, new={cur_num}, {n_updates}, count={self.write_count}\n"
        file.write(log_text)
        file.close()
        # print(f"-- {self.pid} ---\n", to_be_written, "\n", log_text, "\n")
