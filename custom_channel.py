import redis
import pickle
import os
import time

class Channel:
    def __init__(self, nBits=20, hostIP='localhost', portNo=6379):
        self.channel   = redis.StrictRedis(host=hostIP, port=portNo, db=0)
        self.osmembers = {} 
        self.nBits     = nBits
        self.MAXPROC   = pow(2, nBits)

    def join(self, pid, ospid):
        self.pid = pid
        self.ospid = ospid

        self.channel.sadd('members', self.pid)
        self.bind(str(self.pid))
        return str(self.pid)
	
    def bind(self, pid):
        ospid = os.getpid()
        self.osmembers[ospid] = str(pid)

    def exists(self, pid):
        return self.channel.sismember('members', self.serialize(pid))

    def subgroup(self, subgroup):
        return [self.deserialize(pid) for pid in list(self.channel.smembers(subgroup))]

    def sendTo(self, receiver_pid, message):
        self.sendToHelper(self.pid, receiver_pid, message)

    def sendToAll(self, message):
        caller = self.find_caller()
        for i in self.channel.smembers('members'): 
            self.sendToHelper(caller, i, message)

    def recvFromAny(self, timeout=0):
        caller = self.find_caller()
        members = self.channel.smembers('members')
        deserialized_members = [self.deserialize(member) for member in members]
        xchan = [self.serialize(f'{str(i)}-{str(caller)}') for i in deserialized_members]
        if len(xchan) == 0:
            time.sleep(timeout)
            return
        msg = self.channel.blpop(xchan, timeout)
        if msg:
            sender = self.deserialize(msg[0]).split('-')[0]
            message = self.deserialize(msg[1])
            return sender, message

    def recvFrom(self, sender_pid, timeout=0):
        xchan = [self.serialize(f'{str(sender_pid)}-{str(self.pid)}')]
        msg = self.channel.blpop(xchan, timeout)
        if msg:
            sender = self.deserialize(msg[0]).split('-')[0]
            message = self.deserialize(msg[1])
            return sender, message

	# Helper functions
    def serialize(self, string):
        return pickle.dumps(str(string))
	
    def deserialize(self, byte_stream):
        return pickle.loads(byte_stream)
				
    def find_caller(self):
        caller = self.osmembers[os.getpid()]
        assert self.is_member('members', caller), 'Caller is not a member!'
        return caller		

    def is_member(self, subgroup, pid):
        return self.channel.sismember(subgroup, self.serialize(pid))

    def sendToHelper(self, caller, dest, message):
        self.channel.rpush(self.serialize(f'{str(caller)}-{str(dest)}'), self.serialize(message))