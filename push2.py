"""
Uses 6Mb less RAM than pushbullet library
"""

import urllib.request
from base64 import b64encode
import json

def _basic_auth_str(username, password):
    s = '{}:{}'.format(username, password)
    s = s.encode('latin1')
    s = b64encode(s)
    s = 'Basic ' + s.decode('latin1').strip()
    return s

class PushBullet:
    def __init__(self, apiKey):
        self.apiKey = apiKey
        self.headers = {
            'Authorization': _basic_auth_str(self.apiKey, ''),
            'Content-Type': 'application/json',
        }

    def _request(self, url, data=None, headers=None, method='GET'):
        if data:
            payload = json.dumps(data).encode('latin1')
        else:
            payload = None
        req = urllib.request.Request(url, data=payload, headers=headers, method=method)
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode('utf-8'))

    def _get(self, *args, **kwargs):
        return self._request(*args, headers=self.headers, method='GET', **kwargs)

    def _post(self, *args, **kwargs):
        return self._request(*args, headers=self.headers, method='POST', **kwargs)

    def _delete(self, *args, **kwargs):
        return self._request(*args, headers=self.headers, method='DELETE', **kwargs)

    def _load_devices(self):
        import config
        self.device_iden = config.pushbulletDeviceIden

    def get_device(self, nickname):
        pass

    def get_push(self, iden):
        return self._get('https://api.pushbullet.com/v2/pushes/' + iden)

    def delete_push(self, iden):
        return self._delete('https://api.pushbullet.com/v2/pushes/' + iden)

    def _push(self, data):
        return self._post('https://api.pushbullet.com/v2/pushes', data=data)
        
    def push_note(self, title, body, device=None):
        data = {}
        data['type'] = 'note'
        data['title'] = title
        data['body'] = body
        data['device_iden'] = self.device_iden
        return self._push(data)
