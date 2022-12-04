import redis
import random
import pickle
import os
import time

class Channel:
    def __init__(self, nBits=5, hostIP='localhost', portNo=6379):
        self.channel   = redis.StrictRedis(host=hostIP, port=portNo, db=0)
        self.osmembers = {} 
        self.nBits     = nBits
        self.MAXPROC   = pow(2, nBits)

    def join(self, subgroup):
        members = self.channel.smembers('members')
        newpid = random.choice(list(set([str(i) for i in range(self.MAXPROC)]) - members))
        s_pid = self.serialize(newpid)
        self.channel.sadd('members', s_pid)
        self.channel.sadd(subgroup, s_pid)
        self.bind(str(newpid))
        return str(newpid)
	
    def bind(self, pid):
        ospid = os.getpid()
        self.osmembers[ospid] = str(pid)

    def exists(self, pid):
        return self.channel.sismember('members', self.serialize(pid))

    def subgroup(self, subgroup):
        return [self.deserialize(pid) for pid in list(self.channel.smembers(subgroup))]

    def sendTo(self, destinationSet, message):
        caller = self.find_caller()
        for i in destinationSet: 
            assert self.is_member('members', i), f'{i} is not a member!'
            self.sendToHelper(caller, i, message)

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

    def recvFrom(self, senderSet, timeout=0):
        caller = self.find_caller()
        # if senderSet is a list iterate, else just use the single sender
        if isinstance(senderSet, list):
            for x in senderSet: 
                i = int(x)
                assert self.is_member('members', x), f'{x} is not a member (sender set was: {senderSet})!'
                xchan = [self.serialize(f'{str(i)}-{str(caller)}') for i in senderSet]
        else:
            assert self.is_member('members', senderSet), f'{senderSet} is not a member (sender set was: {senderSet})!'
            xchan = [self.serialize(f'{str(senderSet)}-{str(caller)}')]
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