import re
import base64
from flask import Flask, render_template, request, redirect, session
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
    sortedBufferIds = list(bufferMessages.keys())
    sortedBufferIds = sorted(sortedBufferIds, key=bufferSortKey)
    sortedBufferMessages = [(bufferId, bufferMessages[bufferId]) for bufferId in sortedBufferIds]
    return render_template('index.html', **{
        'bufferMessages': sortedBufferMessages,
        'buffers': quasselClient.buffers,
    })

@app.route('/api/send', methods=['GET', 'POST'])
@require_login
def send():
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

