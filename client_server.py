import custom_channel as channel


class Server:
    def __init__(self):
        self.ci = channel.Channel()
        self.server = self.ci.join('server')

    def run(self):
        cont = True
        while cont:
            msg = self.ci.recvFromAny(timeout=1)
            if msg:
                if msg[1] == 'Shutdown':
                    print('\nSERVER :: Goodbye!\n')
                    break
                sender = msg[0]
                response = f'Received {msg[1]}'
                print(f'SERVER :: Message from {sender}: "{msg[1]}"')
                self.ci.sendTo([sender], response)


class Client:
    def __init__(self):
        self.ci = channel.Channel()
        self.client = self.ci.join('client')
        self.server = []
        while len(self.server) == 0:
            self.server = self.ci.subgroup('server')

    def run(self, shutdown=False):
        if not shutdown:
            self.ci.sendTo(self.server, 'Hello from ' + self.client)
            response = self.ci.recvFrom(self.server)
            print(f'CLIENT :: Response from server: "{response[1]}"')
        else:
            self.ci.sendTo(self.server, 'Shutdown')
            print('CLIENT :: Shutdown signal')
