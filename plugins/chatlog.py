from quassel import *
import sys

def onMessageRecieved(bot, message):
    if message['type'] == Message.Type.Plain or message['type'] == Message.Type.Action:
        messageFormat = '[{}] {:<16}\t{:>16}: {}'
        output = messageFormat.format(*[
            message['timestamp'].strftime('%H:%M'),
            message['bufferInfo']['name'],
            message['sender'].split('!')[0],
            message['content'],
        ])
        # Strip stuff the console hates.
        output = output.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
        print(output)
