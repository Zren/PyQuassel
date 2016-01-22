import socket
from qt import *

import json
def pp(data):
    print(json.dumps(data, sort_keys=True, indent=4))


class Protocol:
    magic = 0x42b33f00

    class Type:
        InternalProtocol = 0x00
        LegacyProtocol = 0x01
        DataStreamProtocol = 0x02

    class Feature:
        Encryption = 0x01
        Compression = 0x02


class QuasselClient():
    def __init__(self):
        self.socket = QTcpSocket()
        self.stream = QDataStream(self.socket)
    
    def connectToHost(self, hostName, port):
        self.socket.connectToHost(hostName, port)

    def disconnectFromHost(self):
        self.socket.disconnectFromHost()

    def onSocketConnect(self):
        # https://github.com/quassel/quassel/blob/b49c64970b6237fc95f8ca88c8bb6bcf04c251d7/src/core/coreauthhandler.cpp#L57
        # https://github.com/sandsmark/QuasselDroid/blob/8d8d7b34a515dfc7c570a5fa7392b877206b385b/QuasselDroid/src/main/java/com/iskrembilen/quasseldroid/io/CoreConnection.java#L475
        self.stream.writeUInt32BE(Protocol.magic)
        self.stream.writeUInt32BE(Protocol.Type.LegacyProtocol)
        self.stream.writeUInt32BE(0x01 << 31) # protoFeatures

        data = self.stream.readUInt32BE()
        # print(data)
        connectionFeatures = data >> 24
        if (connectionFeatures & 0x01) > 0:
            print('Core Supports SSL')
        if (connectionFeatures & 0x02) > 0:
            print('Core Supports Compression')

    def sendClientInit(self):
        m = {}
        m['MsgType'] = 'ClientInit'
        m['ClientVersion'] = 'QuasselClient.py v1'
        m['ClientDate'] = 'Apr 14 2014 17:18:30'
        m['ProtocolVersion'] = 10
        m['UseCompression'] = False
        m['UseSsl'] = False
        self.stream.write(m)

    def readClientInit(self):
        data = self.stream.read()
        return data

    def sendClientLogin(self, username, password):
        m = {}
        m['MsgType'] = 'ClientLogin'
        m['User'] = username
        m['Password'] = password
        self.stream.write(m)

    def readClientLogin(self):
        data = self.stream.read()
        return data

    def readSessionState(self):
        data = self.stream.read()
        sessionState = data['SessionState']
        self.buffers = {}
        for bufferInfo in sessionState['BufferInfos']:
            self.buffers[bufferInfo['id']] = bufferInfo

        self.networks = {}
        for networkId in sessionState['NetworkIds']:
            # print(networkId)
            self.networks[networkId] = None
        # print(self.networks)

        return data

    def sendNetworkInits(self):
        for networkId in self.networks.keys():
            print(networkId)
            l = [
                3, # RequestType.InitRequest
                'Network',
                str(networkId),
            ]
            self.stream.write(l)
            self.readPackedFunc()


    def readPackedFunc(self):
        data = self.stream.read()
        requestType = data[0]
        if requestType == 2: # RequestType.RpcCall
            functionName = data[1]
            if functionName == b'2displayMsg(Message)':
                message = data[2]
                # print(message)
                self.onMessageRecieved(message)
                return

        elif requestType == 4: # RequestType.InitData
            className = data[1]
            objectName = data[2]
            if className == b'Network':
                initMap = data[3]
                # pp(initMap)
                self.networks[networkId] = initMap
                print(initMap['networkName'])
                return
        
        # print(data)

    def sendInput(self, bufferId, message):
        print('sendInput', bufferId, message)
        bufferInfo = self.buffers[bufferId]
        l = [
            2, # RequestType.RpcCall
            '2sendInput(BufferInfo,QString)',
            QUserType('BufferInfo', bufferInfo),
            message,
        ]
        pp(l)
        self.stream.write(l)

    def onMessageRecieved(self, message):
        if message['type'] == 1 or message['type'] == 4:
            messageFormat = '{}\t<{}>\t{}'
            output = messageFormat.format(*[
                message['bufferInfo']['name'],
                message['sender'].split('!')[0],
                message['content'],
            ])
            print(output)




if __name__ == '__main__':
    host = 'localhost'
    port = 4242
    username = 'AdminUser'
    password = ''

    import os
    if os.path.exists('config.py'):
        import config
        host = config.host
        port = config.port
        username = config.username
        password = config.password
    
    quasselClient = QuasselClient()
    quasselClient.connectToHost(host, port)
    quasselClient.onSocketConnect()

    quasselClient.sendClientInit()
    quasselClient.readClientInit()
    quasselClient.sendClientLogin(username, password)
    quasselClient.readClientLogin()

    quasselClient.readSessionState()
    # quasselClient.sendNetworkInits()

    def findBufferId(bufferName, networkId=None, networkName=None):
        for buffer in quasselClient.buffers.values():
            if buffer['name'] == bufferName:
                if networkId is not None:
                    if buffer['network'] == networkId:
                        return buffer['id']
                elif networkName is not None:
                    network = self.networks[buffer['network']]
                    if network['networkName'] == networkName:
                        return buffer['id']
                else:
                    return buffer['id']
        return None



    # bufferId = findBufferId('#zren', networkId=1)
    # quasselClient.sendInput(bufferId, '\x032Test message please ignore')


    # import time
    # time.sleep(5)

    quasselClient.socket.socket.settimeout(15)
    while True:
        try:
            quasselClient.readPackedFunc()
        except socket.timeout:
            pass
        # time.sleep(0.1)

    quasselClient.disconnectFromHost()

