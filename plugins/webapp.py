import re
import base64
from flask import Flask, render_template, request, redirect, session, jsonify
from quassel import *
from collections import defaultdict, deque

app = Flask(__name__, static_folder='webapp/static', template_folder='webapp/templates')
quasselClient = None
bufferMessages = defaultdict(lambda: deque(maxlen=50))

def onSessionStarted(bot):
    global quasselClient
    quasselClient = bot

    import os    
    
    if len(bot.config.webappSessionKey) > 0:
        if isinstance(bot.config.webappSessionKey, str):
            bot.config.webappSessionKey = bot.config.webappSessionKey.encode('utf-8')
        app.secret_key = bot.config.webappSessionKey # Bad?
    else:
        bot.config.webappSessionKey = os.urandom(24)
        app.secret_key = os.urandom(24)

    bot.config.webappUrl = 'http://{}:{}/?key={}'.format(*[
        bot.config.webappServerName,
        bot.config.webappPort,
        base64.urlsafe_b64encode(bot.config.webappSessionKey).decode('utf-8'),
    ])

    import threading
    thread = threading.Thread(target=app.run, kwargs={
        'host': '0.0.0.0',
        'port': bot.config.webappPort,
    })
    thread.daemon = True
    thread.start()

    print('[webapp] ' + bot.config.webappUrl)
    # import webbrowser
    # webbrowser.open(bot.config.webappUrl)

def onMessageRecieved(bot, message):
    if message['type'] in [Message.Type.Plain, Message.Type.Action]:
        messages = bufferMessages[message['bufferInfo']['id']]
        messages.append(Message(message))



def getState():
    state = {}
    state['networks'] = {}
    for networkId, network in quasselClient.networks.items():
        if network is None:
            state['networks'][networkId] = {
                'id': networkId,
                'name': '',
                'myNick': '',
                'isConnected': False,
            }
        else:
            state['networks'][networkId] = {
                'id': networkId,
                'name': network['networkName'],
                'myNick': network['myNick'],
                'isConnected': network['isConnected'],
            }

    state['buffers'] = {}
    for bufferId, buffer in quasselClient.buffers.items():
        network = state['networks'][buffer['network']]
        messages = [
            {
                'id': message['id'],
                'bufferId': message['bufferInfo']['id'],
                'type': int(message['type']),
                'isSelf': message['flags'] & Message.Flag.Self,
                'timestamp': message['timestamp'],
                'sender': message['sender'].split('!')[0],
                'content': message['content'],
            } for message in bufferMessages[bufferId]
        ]
        state['buffers'][bufferId] = {
            'id': bufferId,
            'networkId': buffer['network'],
            'type': int(buffer['type']),
            'name': buffer['name'],
            'unreadMessageCount': 0,
            'isJoined': buffer.get('isJoined', False),
            'messages': messages,
        }
    
    # for networkId, network in state['networks'].items()
    #     network['buffers'] = [buffer for buffer in state['buffers'].values() if buffer['networkId'] == networkId)

    return state

import functools
def require_login(f):
    @functools.wraps(f)
    def g(*args, **kwargs):
        key = request.values.get('key')
        if key:
            key = base64.urlsafe_b64decode(key.encode('utf-8'))
            if key == quasselClient.config.webappSessionKey:
                session['key'] = key
        
        if session.get('key') != quasselClient.config.webappSessionKey:
            return 'Not Logged In', 403

        ret = f(*args, **kwargs)
        return ret
    return g

@app.route('/')
@require_login
def index():
    def bufferSortKey(bufferId):
        b = quasselClient.buffers[bufferId]
        return (b['network'], b['name'].lower())

    state = getState()

    chatList = []
    for network in sorted(state['networks'].values(), key=lambda network: network['name'].lower()):
        if not network['isConnected']:
            continue
        
        networkBuffers = [buffer for buffer in state['buffers'].values() if buffer['networkId'] == network['id']]
        networkBuffers = [buffer for buffer in networkBuffers if len(buffer['messages']) > 0]
        networkBuffers = sorted(networkBuffers, key=lambda buffer: buffer['name'].lower())
        
        chatList.append((network['id'], [buffer['id'] for buffer in networkBuffers]))
    
    state['chatList'] = chatList

    return render_template('index.html', **state)


    # sortedBufferIds = []
    # for bufferId, messages in bufferMessages.items():
    #     if len(messages) 
    # sortedBufferIds = list(bufferMessages.keys())
    # sortedBufferIds = sorted(sortedBufferIds, key=bufferSortKey)
    # sortedBufferMessages = [(bufferId, bufferMessages[bufferId]) for bufferId in sortedBufferIds]
    # return render_template('index.html', **{
    #     'bufferMessages': sortedBufferMessages,
    #     'buffers': quasselClient.buffers,
    # })

@app.route('/api/state.json')
def api_state():
    state = getState()
    return jsonify(state)

@app.route('/api/send', methods=['GET', 'POST'])
@require_login
def api_send():
    bufferId = int(request.values.get('bufferId'))
    message = request.values.get('message')
    quasselClient.sendInput(bufferId, message)
    return redirect('/')

@app.errorhandler(Exception)
def internal_error(error):
    import traceback
    tb = traceback.format_exc()
    import logging
    logging.error(tb)
    return "<h1>500: Internal Error</h1><pre>{0}</pre>".format(tb), 500

