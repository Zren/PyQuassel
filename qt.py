from enum import Enum, IntEnum
import socket
import struct

import json
def pp(data):
    print(json.dumps(data, sort_keys=True, indent=4))

class QVariant:
    def __init__(self, obj):
        self.obj = obj
        if isinstance(obj, bool):
            self.type = QDataStream.Type.BOOL
        elif isinstance(obj, int):
            self.type = QDataStream.Type.UINT
        elif isinstance(obj, dict):
            self.type = QDataStream.Type.MAP
        elif isinstance(obj, str):
            self.type = QDataStream.Type.STRING
        elif isinstance(obj, list):
            self.type = QDataStream.Type.LIST

class QUserType(QVariant, dict):
    def __init__(self, name, obj):
        super().__init__(obj)
        self.name = name
        self.type = QDataStream.Type.USERTYPE

    def __repr__(self):
        return self.obj.__repr__()



class QTcpSocket:
    def __init__(self):
        self.socket = socket.socket()
        self.socket.settimeout(2)
    
    def connectToHost(self, hostName, port):
        self.socket.connect((hostName, port))
    
    def disconnectFromHost(self):
        self.socket.close()

    def read(self, maxSize):
        buf = self.socket.recv(maxSize)
        # print('QTcpSocket >>', buf)
        return buf

    def write(self, data):
        # print('QTcpSocket <<', data)
        self.socket.sendall(data)




class QDataStream:
    class ByteOrder(IntEnum):
        BigEndian, LittleEndian = range(2)
    class FloatingPointPrecision(IntEnum):
        SinglePrecision, DoublePrecision = range(2)
    class Status(IntEnum):
        Ok, ReadPastEnd, ReadCorruptData, WriteFailed = range(4)
    class Version(IntEnum):
        Qt_1_0 = 1 #  Version 1 (Qt 1.x)
        Qt_2_0 = 2 #  Version 2 (Qt 2.0)
        Qt_2_1 = 3 #  Version 3 (Qt 2.1, 2.2, 2.3)
        Qt_3_0 = 4 #  Version 4 (Qt 3.0)
        Qt_3_1 = 5 #  Version 5 (Qt 3.1, 3.2)
        Qt_3_3 = 6 #  Version 6 (Qt 3.3)
        Qt_4_0 = 7 #  Version 7 (Qt 4.0, Qt 4.1)
        Qt_4_2 = 8 #  Version 8 (Qt 4.2)
        Qt_4_3 = 9 #  Version 9 (Qt 4.3)
        Qt_4_4 = 10 #  Version 10 (Qt 4.4)
        Qt_4_5 = 11 #  Version 11 (Qt 4.5)
        Qt_4_6 = 12 #  Version 12 (Qt 4.6, Qt 4.7, Qt 4.8)
    
    def __init__(self, device=None):
        self.version = QDataStream.Version.Qt_4_6
        self.status = QDataStream.Status.Ok
        self.device = device

    def writeRawData(self, data):
        self.device.write(data)

    def writeUInt32BE(self, i):
        self << struct.pack('>I', i)

    def writeBool(self, b):
        self << struct.pack('?', b)

    def __lshift__(self, obj):
        self.writeRawData(obj)

    def readByte(self):
        buf = self.device.read(1)
        # print(buf)
        return buf
        # i = struct.unpack('>H', b'\x00' + buf)[0]
        # i = struct.unpack('b', buf)[0]
        # i = int.from_bytes(buf, byteorder='little', signed=True)
        # return i


    def readInt16BE(self):
        buf = self.device.read(2)
        i = struct.unpack('>h', buf)[0]
        return i

    def readUInt16BE(self):
        buf = self.device.read(2)
        i = struct.unpack('>H', buf)[0]
        return i

    def readInt32BE(self):
        buf = self.device.read(4)
        i = struct.unpack('>i', buf)[0]
        return i

    def readUInt32BE(self):
        buf = self.device.read(4)
        i = struct.unpack('>I', buf)[0]
        return i

    def readBool(self):
        buf = self.device.read(1)
        b = struct.unpack('?', buf)[0]
        return b

    class Type(IntEnum):
        # https://github.com/sandsmark/QuasselDroid/blob/8d8d7b34a515dfc7c570a5fa7392b877206b385b/QuasselDroid/src/main/java/com/iskrembilen/quasseldroid/protocol/qtcomm/QVariantType.java
        BOOL = 1
        INT = 2
        UINT = 3
        LONG = 4
        ULONG = 5
        CHAR = 7
        MAP = 8
        LIST = 9
        STRING = 10
        STRINGLIST = 11
        BYTEARRAY = 12
        TIME = 15
        DATETIME = 16
        USERTYPE = 127
        USHORT = 133


    class Writer:
        def __init__(self, obj):
            self.buf = bytearray()
            self.type = QVariant(obj).type
            self.write(obj)

        @property
        def size(self):
            return len(self.buf)

        def __lshift__(self, obj):
            self.buf += obj

        def writeInt16BE(self, i):
            self << struct.pack('>h', i)

        def writeInt32BE(self, i):
            self << struct.pack('>i', i)

        def writeUInt32BE(self, i):
            self << struct.pack('>I', i)

        def writeBool(self, b):
            self << struct.pack('?', b)

        def write(self, obj):
            if obj is None:
                return None
            # AutoBoxed Types
            elif isinstance(obj, bool):
                self.writeQBool(obj)
            elif isinstance(obj, int):
                self.writeQUInt(obj)
            elif isinstance(obj, dict):
                self.writeQMap(obj)
            elif isinstance(obj, str):
                self.writeQString(obj)
            elif isinstance(obj, list):
                self.writeQList(obj)
            # Fuck
            else:
                raise Exception("Type not found")


        def writeQShort(self, qint):
            self.writeInt16BE(qint)

        def writeQInt(self, qint):
            self.writeInt32BE(qint)

        def writeQUInt(self, quint):
            self.writeUInt32BE(quint)

        def writeQBool(self, qbool):
            self.writeBool(qbool)

        def writeQString(self, qstring):
            if qstring is None:
                # Special case for NULL
                self.writeUInt32BE(0xffffffff)
            else:
                # Converts to a UTF-16 buffer
                b = qstring.encode('utf_16_be')
                self.writeUInt32BE(len(b))
                self << b

        def writeQByteArray(self, qbytearray):
            if qbytearray is None:
                # Special case for NULL
                self.writeUInt32BE(0xffffffff)
            else:
                # Converts to a UTF-8 buffer
                b = qbytearray.encode('utf-8')
                self.writeUInt32BE(len(b))
                self << b

        def writeQVariant(self, qvariant):
            # print(qvariant.type, qvariant.obj)
            self.writeUInt32BE(qvariant.type)
            self.writeBool(qvariant.obj is None)
            if qvariant.type == QDataStream.Type.USERTYPE:
                self.writeQByteArray(qvariant.name)
                if qvariant.name == 'BufferInfo':
                    self.writeQInt(qvariant.obj['id'])
                    self.writeQInt(qvariant.obj['network'])
                    self.writeQShort(qvariant.obj['type'])
                    self.writeQInt(qvariant.obj['group'])
                    self.writeQByteArray(qvariant.obj['name'])
            else:
                self.write(qvariant.obj)

        def writeQMap(self, m):
            size = len(m)
            self.writeUInt32BE(size)
            for key, value in m.items():
                self.write(key)
                v = value
                if not isinstance(v, QVariant):
                    v = QVariant(v)
                self.writeQVariant(v)

        def writeQList(self, l):
            size = len(l)
            self.writeUInt32BE(size)
            for item in l:
                v = item
                if not isinstance(v, QVariant):
                    v = QVariant(v)
                self.writeQVariant(v)

    class Reader:
        def __init__(self, buf):
            self.pos = 0


    def write(self, obj):
        writer = QDataStream.Writer(obj)

        self.writeUInt32BE(writer.size + 5)
        self.writeUInt32BE(writer.type)
        self.writeBool(writer.size > 0)
        self << writer.buf

        # fmt = ""
        # values = []
        
        # ftm += ""
        # bufs = []
        # size = 0
        # type = QDataStream.Types.Map
        # buf = 

    def read(self):
        # size = self.readUInt32BE()
        buf = self.device.read(4)
        if len(buf) == 0:
            raise IOError('Device Closed')
        size = struct.unpack('>I', buf)[0]

        # print('buffer size:', size)
        obj = self.readQVariant()

        # pp(obj)
        # print(obj)

        return obj

    def readQVariant(self):
        variantType = self.readUInt32BE()
        try:
            variantType = QDataStream.Type(variantType)
        except ValueError:

            m = self.readQUInt()
            print(m)
            raise Exception('QDataStream.Type', variantType)

        # print('QVariant.type', variantType)
        isNull = self.readBool()
        # print('QVariant.isNull', isNull)

        if variantType == QDataStream.Type.MAP:
            val = self.readQMap()
        elif variantType == QDataStream.Type.BOOL:
            val = self.readQBool()
        elif variantType == QDataStream.Type.STRING:
            val = self.readQString()
        elif variantType == QDataStream.Type.CHAR:
            val = self.device.read(2)
            val = val.decode('utf_16_be')
        elif variantType == QDataStream.Type.INT:
            val = self.readQInt()
        elif variantType == QDataStream.Type.UINT:
            val = self.readQUInt()
        elif variantType == QDataStream.Type.LIST:
            val = self.readQList()
        elif variantType == QDataStream.Type.STRINGLIST:
            val = self.readQStringList()
        elif variantType == QDataStream.Type.BYTEARRAY:
            val = self.readQByteArray()
        elif variantType == QDataStream.Type.USHORT:
            val = self.readQUShort()
        elif variantType == QDataStream.Type.TIME:
            secondsSinceMidnight = self.readQUInt()
            val = 1
        elif variantType == QDataStream.Type.DATETIME:
            julianDay = self.readQUInt()
            secondsSinceMidnight = self.readQUInt()
            isUTC = self.readBool()
            # from datetime import datetime
            # val = datetime.now()
            val = 1

        elif variantType == QDataStream.Type.USERTYPE:
            name = self.readQByteArray()
            name = name.decode('utf-8')
            name = name.rstrip('\0')
            # print('QUserType.name', name)
            if name == 'NetworkId':
                val = self.readQInt()
            elif name == 'IdentityId':
                val = self.readQInt()
            elif name == 'BufferId':
                val = self.readQInt()
            elif name == 'MsgId':
                val = self.readQInt()
            elif name == 'Identity':
                val = self.readQMap()
            elif name == 'Network::Server':
                val = self.readQMap()
                # print(val)
            elif name == 'BufferInfo':
                val = {
                    'id': self.readQInt(),
                    'network': self.readQInt(),
                    'type': self.readQShort(),
                    'group': self.readQInt(),
                    'name': self.readQByteArray().decode('utf-8'),
                }
            elif name == 'Message':
                val = {
                    'id': self.readQInt(),
                    'timestamp': self.readQUInt(),
                    'type': self.readQUInt(),
                    'flags': self.readByte(),
                    'bufferInfo': {
                        'id': self.readQInt(),
                        'network': self.readQInt(),
                        'type': self.readQShort(),
                        'group': self.readQInt(),
                        'name': self.readQByteArray().decode('utf-8'),
                    },
                    'sender': self.readQByteArray().decode('utf-8'),
                    'content': self.readQByteArray().decode('utf-8'),
                }
            else:
                raise Exception("QUserType.name", name)
        else:
            raise Exception('QVariant.type', variantType)

        # print('QVariant.val', val)
        return val


    def readQMap(self):
        size = self.readUInt32BE()
        # print('QMap.size', size)

        ret = {}
        for i in range(size):
            key = self.readQString()
            # print('QMap[key]', key)
            value = self.readQVariant()
            # print('QMap[value]', value)
            ret[key] = value
        return ret


    def readQString(self):
        size = self.readUInt32BE()
        if size == 0xFFFFFFFF:
            return ''
        buf = self.device.read(size)
        s = buf.decode('utf_16_be')
        return s

    def readQBool(self):
        return self.readBool()

    def readQInt(self):
        return self.readInt32BE()

    def readQUInt(self):
        return self.readUInt32BE()

    def readQShort(self):
        return self.readInt16BE()

    def readQUShort(self):
        return self.readUInt16BE()

    def readQList(self):
        size = self.readUInt32BE()
        l = []
        for i in range(size):
            val = self.readQVariant()
            l.append(val)
        return l

    def readQStringList(self):
        size = self.readUInt32BE()
        l = []
        for i in range(size):
            val = self.readQString()
            l.append(val)
        return l

    def readQByteArray(self):
        size = self.readUInt32BE()
        if size == 0xFFFFFFFF:
            return ''
        buf = self.device.read(size)
        s = buf
        return s
