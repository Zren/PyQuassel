import socket
import time
import datetime
from pprint import pprint

from qt import *
from quassel import *

class QuasselQDataStream(QDataStream):
    def readUserType(self, name):
        if name == 'NetworkId':
            return self.readQInt()
        elif name == 'IdentityId':
            return self.readQInt()
        elif name == 'BufferId':
            return self.readQInt()
        elif name == 'MsgId':
            return self.readQInt()
        elif name == 'Identity':
            return self.readQMap()
        elif name == 'Network::Server':
            return self.readQMap()
            # print(val)
        elif name == 'BufferInfo':
            val = {}
            val['id'] = self.readQInt()
            val['network'] = self.readQInt()
            val['type'] = BufferInfo.Type(self.readQShort())
            val['group'] = self.readQInt()
            val['name'] = self.readQByteArray().decode('utf-8')
            return val
        elif name == 'Message':
            val = {}
            val['id'] = self.readQInt()
            val['timestamp'] = datetime.datetime.fromtimestamp(self.readQUInt())
            val['type'] = Message.Type(self.readQUInt())
            val['flags'] = Message.Flag(self.readUInt8())
            val['bufferInfo'] = self.readUserType('BufferInfo')
            val['sender'] = self.readQByteArray().decode('utf-8')
            val['content'] = self.readQByteArray().decode('utf-8')
            return val
        else:
            return None

class QuasselClient:
    def __init__(self, config=None):
        self.config = config
        self.running = False
        self.socket = None
        self.stream = None
        
    def createSocket(self):
        self.socket = QTcpSocket()
        self.stream = QuasselQDataStream(self.socket)
    
    def connectToHost(self, hostName=None, port=None):
        if hostName is None:
            hostName = self.config.host
        if port is None:
            port = self.config.port
            
        if self.socket is None:
            self.createSocket()
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

    def sendClientLogin(self, username=None, password=None):
        if username is None:
            username = self.config.username
        if password is None:
            password = self.config.password
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
            # print(networkId)
            l = [
                RequestType.InitRequest,
                'Network',
                str(networkId),
            ]
            self.stream.write(l)

    def sendBufferInits(self):
        for bufferId, buffer in self.buffers.items():
            # print(networkId)
            l = [
                RequestType.InitRequest,
                'IrcChannel',
                '{}/{}'.format(buffer['network'], buffer['name']),
            ]
            self.stream.write(l)


    def readPackedFunc(self):
        data = self.stream.read()
        requestType = data[0]
        if requestType == RequestType.RpcCall:
            functionName = data[1]
            if functionName == b'2displayMsg(Message)':
                message = data[2]
                # print(message)
                self.onMessageRecieved(message)
                return

        elif requestType == RequestType.InitData:
            className = data[1]
            objectName = data[2]
            if className == b'Network':
                networkId = int(objectName)
                initMap = data[3]
                # pprint(initMap)
                del data
                del initMap['IrcUsersAndChannels']

                networkInfo = {}
                networkInfo['networkName'] = initMap['networkName']
                self.networks[networkId] = networkInfo
                # print(initMap['networkName'])
                # if False:
                #     if initMap['networkName'] == 'Freenode':
                #         for key in initMap.keys():
                #             print('\tinitMap[{}]'.format(key))
                #         # del initMap['IrcUsersAndChannels']

                #         with open('output-network.log', 'w') as f:
                #             f.write(str(initMap).replace(', \'', ',\n\''))
                #         # pprint(initMap)
                return
            elif className == b'IrcChannel':
                networkId, bufferName = objectName.split('/')
                networkId = int(networkId)
                for buffer in self.buffers.values():
                    if buffer['network'] == networkId and buffer['name'] == bufferName:
                        initMap = data[3]
                        del data
                        del initMap['UserModes']
                        buffer['isJoined'] = True
                        buffer['topic'] = initMap['topic']
                        break
                return
        elif requestType == RequestType.HeartBeat:
            self.sendHeartBeatReply()
            return
        elif requestType == RequestType.HeartBeatReply:
            # print('HeartBeatReply', data)
            return

        # import sys
        # output = str(data)
        # output = output.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
        # print(output)

    def sendInput(self, bufferId, message):
        print('sendInput', bufferId, message)
        bufferInfo = self.buffers[bufferId]
        l = [
            RequestType.RpcCall,
            '2sendInput(BufferInfo,QString)',
            QUserType('BufferInfo', bufferInfo),
            message,
        ]
        pprint(l)
        self.stream.write(l)

    def sendHeartBeat(self):
        t = datetime.datetime.now().time()
        # print('sendHeartBeat', t)
        l = [
            RequestType.HeartBeat,
            t,
        ]
        self.stream.write(l)

    def sendHeartBeatReply(self):
        t = datetime.datetime.now().time()
        # print('sendHeartBeatReply', t)
        l = [
            RequestType.HeartBeatReply,
            t,
        ]
        self.stream.write(l)

    # findBufferId(..., networkName="") requires calling quasselClient.sendNetworkInits() first.
    def findBufferId(self, bufferName, networkId=None, networkName=None):
        for buffer in self.buffers.values():
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

    def createSession(self):
        self.connectToHost()
        self.onSocketConnect()

        self.sendClientInit()
        self.readClientInit()
        self.sendClientLogin()
        self.readClientLogin()

        self.readSessionState()

    def reconnect(self):
        self.createSession()
        self.running = True

    def run(self):
        self.createSession()
        self.onSessionStarted()
        self.running = True
        self.lastHeartBeatSentAt = None
        while self.running:
            try:
                self.readPackedFunctionLoop()
            except IOError:
                self.running = False
                self.onSocketClosed()


    def readPackedFunctionLoop(self):
        self.socket.socket.settimeout(15)
        self.socket.logReadBuffer = False
        while self.running:
            try:
                self.readPackedFunc()
                # print('TCP >>')
                # for buf in self.socket.readBufferLog:
                #     print('\t', buf)
                del self.socket.readBufferLog[:]

                t = int(time.time() * 1000)
                if self.lastHeartBeatSentAt is None or t - self.lastHeartBeatSentAt > 60 * 1000:
                    self.sendHeartBeat()
                    self.lastHeartBeatSentAt = t

                    # import gc
                    # gc.collect()
            except socket.timeout:
                pass
            except Exception as e:
                import traceback
                traceback.print_exc()
                print('TCP >>')
                for buf in self.socket.readBufferLog:
                    print('\t', buf)
                raise e

    def onSessionStarted(self):
        self.sendNetworkInits() # Slooooow.
        self.sendBufferInits()

    def onMessageRecieved(self, message):
        pass

    def onSocketClosed(self):
        pass

if __name__ == '__main__':
    raise Exception("You ran the wrong file.")

    import sys, os
    if not os.path.exists('config.py'):
        print('Please create a config.py as mentioned in the ReadMe.')
        sys.exit(1)

    import config
    quasselClient = QuasselClient(config)
    quasselClient.run()
    
    quasselClient.disconnectFromHost()
