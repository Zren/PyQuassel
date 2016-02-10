from enum import IntEnum

class Message(dict):
    class Type(IntEnum):
        Plain     = 0x00001
        Notice    = 0x00002
        Action    = 0x00004
        Nick      = 0x00008
        Mode      = 0x00010
        Join      = 0x00020
        Part      = 0x00040
        Quit      = 0x00080
        Kick      = 0x00100
        Kill      = 0x00200
        Server    = 0x00400
        Info      = 0x00800
        Error     = 0x01000
        DayChange = 0x02000
        Topic     = 0x04000
        NetsplitJoin = 0x08000
        NetsplitQuit = 0x10000
        Invite = 0x20000

    class Flag(IntEnum):
        NoFlags = 0x00
        Self = 0x01
        Highlight = 0x02 # Set clientside: https://github.com/quassel/quassel/blob/b49c64970b6237fc95f8ca88c8bb6bcf04c251d7/src/qtui/qtuimessageprocessor.cpp#L112
        Redirected = 0x04
        ServerMsg = 0x08
        Backlog = 0x80

    @property
    def senderNick(self):
        return self['sender'].split('!')[0]


class BufferInfo:
    class Type(IntEnum):
        InvalidBuffer = 0x00
        StatusBuffer = 0x01
        ChannelBuffer = 0x02
        QueryBuffer = 0x04
        GroupBuffer = 0x08

    class Activity(IntEnum):
        NoActivity = 0x00
        OtherActivity = 0x01
        NewMessage = 0x02
        Highlight = 0x40


class RequestType(IntEnum):
    Invalid = 0
    Sync = 1
    RpcCall = 2
    InitRequest = 3
    InitData = 4
    HeartBeat = 5
    HeartBeatReply = 6

class Protocol:
    magic = 0x42b33f00

    class Type:
        InternalProtocol = 0x00
        LegacyProtocol = 0x01
        DataStreamProtocol = 0x02

    class Feature:
        Encryption = 0x01
        Compression = 0x02
