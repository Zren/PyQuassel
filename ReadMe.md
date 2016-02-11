# PyQuassel

Pure python implementation of QuasselClient. Doesn't depend on any PySide/PyQt libraries.

Based on:
 * https://github.com/magne4000/node-libquassel/
 * https://github.com/sandsmark/QuasselDroid/

## Setup

### Install

```bash
git clone https://github.com/Zren/PyQuassel.git
cd PyQuassel
```

### Create `config.py`

```python
host = 'localhost'
port = 4242
username = 'AdminUser'
password = 'PASSWORD'
```

## Run

```bash
python quasselbot.py
```

## Update

```bash
git pull origin master
```

# Plugins

Enable a plugin by adding it's name in `config.py`.

```python
enabledPlugins = [
    'chatlog',
    'pushbullet',
]
```

## chatlog

Prints chat messages to the console.

## pushbullet

Recieve push notifications for specific keywords or from query buffers. Current nick/highlight support not yet available.

![](https://i.imgur.com/G9lH5q8.png) ![](https://i.imgur.com/N9FjdB0.png)

`config.py`

```python
"""
For push notifications, you'll need an Access Token which
can gotten from your account settings.
https://www.pushbullet.com/#settings/account
"""
pushbulletAccessToken = 'asd78f69sd876f765dsf78s5da7f5as7df8a58s7dfADS'
"""
To push to all decives, push set as None.
To push to a specific device, enter the device name.
https://www.pushbullet.com/#settings/devices 
"""
pushbulletDeviceName = None
# pushbulletDeviceName = 'Motorola XT1034'

pushIfKeyword = [ # Case Insensitive
    'Zren',
    'Shadeness',
    'Pushbullet',
]
```

## webapp

A very simple webserver to glance at recent messages. When enabled, the bot uses a total ~30 Mb of RAM.

![](https://i.imgur.com/49Kqeie.png)

`config.py`

```python
"""
Webapp to read the last 50 messages in all channels.
The pushbullet plugin will send links to the webapp if enabled.
"""
webappPort = 3000
webappServerName = 'localhost'

# The session key is used instead of username/password to view the webapp.
# If left blank, a new key is generated each run.
# Generate a good key with: python -c "import os; print(os.urandom(24))"
# webappSessionKey = ''
webappSessionKey =  b'hN\xe7\xfd\x95[\xc0\xdfH\x96\xe4W\xaf\xad\xe2\x12#\xcfu\x92\x1eZ<\xf9'

```
