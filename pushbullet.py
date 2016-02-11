"""
Uses 6Mb less RAM than the pushbullet python library.
"""

import urllib.request
import json

class PushBullet:
    def __init__(self, access_token):
        self.access_token = access_token
        self.session_headers = {
            'Access-Token': self.access_token,
            'Content-Type': 'application/json',
        }

    # JSON HTTP Requests
    def _request(self, url, data=None, headers=None, method='GET'):
        payload = json.dumps(data).encode('latin1') if data else None
        req_headers = self.session_headers
        if headers:
            req_headers = req_headers.copy().update(headers)
        
        req = urllib.request.Request(url, data=payload, headers=req_headers, method=method)
        with urllib.request.urlopen(req) as res:
            res_data = res.read().decode('utf-8')
            return json.loads(res_data)

    def _get(self, *args, **kwargs):
        return self._request(*args, method='GET', **kwargs)

    def _post(self, *args, **kwargs):
        return self._request(*args, method='POST', **kwargs)

    def _delete(self, *args, **kwargs):
        return self._request(*args, method='DELETE', **kwargs)


    def get_device_list(self):
        # https://docs.pushbullet.com/#list-devices
        data = self._get('https://api.pushbullet.com/v2/devices')
        return data['devices']

    def get_device(self, iden=None, nickname=None):
        device_list = self.get_device_list()
        for device in device_list:
            print(device)
            if iden is not None and iden == device['iden']:
                return device
            if nickname is not None and nickname == device.get('nickname'):
                return device
        return None

    def get_push(self, push_iden):
        return self._get('https://api.pushbullet.com/v2/pushes/' + push_iden)

    def delete_push(self, push_iden):
        return self._delete('https://api.pushbullet.com/v2/pushes/' + push_iden)

    def push(self, **kwargs):
        # https://docs.pushbullet.com/#create-push
        return self._post('https://api.pushbullet.com/v2/pushes', data=kwargs)
        
    def push_note(self, title, body, device_iden=None):
        data = {}
        data['type'] = 'note'
        data['title'] = title
        data['body'] = body
        data['device_iden'] = device_iden
        return self.push(**data)

if __name__ == '__main__':
    import re
    def pp(data):
        s = json.dumps(data, sort_keys=True, indent=4)
        s = re.sub(r'(\{|\[)\n\s+', r'\1   ', s)
        print(s)
        
    import config
    p = PushBullet(config.pushbulletAccessToken)
    # device_list = p.get_device_list()
    # pp(device_list)
    device = p.get_device(nickname=config.pushbulletDeviceName)
    push = p.push_note('Meh', 'test', device_iden=device['iden'])
