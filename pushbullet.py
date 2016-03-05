"""
Uses 6Mb less RAM than the pushbullet python library.
Using urllib instead of requests to shave off ~1Mb of RAM.
"""

import urllib.request
import urllib.error
import json

class JsonSession:
    def __init__(self):
        self.headers = {}

    def request(self, url, data=None, headers=None, method='GET'):
        payload = json.dumps(data).encode('latin1') if data else None
        req_headers = self.headers
        if headers:
            req_headers = req_headers.copy().update(headers)
        
        req = urllib.request.Request(url, data=payload, headers=req_headers, method=method)
        with urllib.request.urlopen(req) as res:
            res_data = res.read().decode('utf-8')
            return json.loads(res_data)

    def get(self, *args, **kwargs):
        return self.request(*args, method='GET', **kwargs)

    def post(self, *args, **kwargs):
        return self.request(*args, method='POST', **kwargs)

    def delete(self, *args, **kwargs):
        return self.request(*args, method='DELETE', **kwargs)


class PushBullet:
    def __init__(self, access_token):
        self.access_token = access_token
        self.session = JsonSession()
        self.session.headers = {
            'Access-Token': self.access_token,
            'Content-Type': 'application/json',
        }

    def get_device_list(self):
        # https://docs.pushbullet.com/#list-devices
        data = self.session.get('https://api.pushbullet.com/v2/devices')
        return data['devices']

    def get_device(self, iden=None, nickname=None):
        device_list = self.get_device_list()
        for device in device_list:
            # pprint(device)
            if iden is not None and iden == device['iden']:
                return device
            if nickname is not None and nickname == device.get('nickname'):
                return device
        return None

    def get_push(self, push_iden):
        try:
            return self.session.get('https://api.pushbullet.com/v2/pushes/' + push_iden)
        except urllib.error.HTTPError:
            return None # Push was deleted

    def delete_push(self, push_iden):
        return self.session.delete('https://api.pushbullet.com/v2/pushes/' + push_iden)

    def push(self, **kwargs):
        # https://docs.pushbullet.com/#create-push
        return self.session.post('https://api.pushbullet.com/v2/pushes', data=kwargs)
        
    def push_note(self, title, body, **kwargs):
        data = {}
        data['type'] = 'note'
        data['title'] = title
        data['body'] = body
        data.update(kwargs)
        return self.push(**data)

if __name__ == '__main__':
    import re
    from pprint import pprint
        
    import config
    p = PushBullet(config.pushbulletAccessToken)

    # device_list = p.get_device_list()
    # pprint(device_list)

    device = p.get_device(nickname=config.pushbulletDeviceName)
    device_iden = None if device is None else device['iden']
    push = p.push_note('Meh', 'test', device_iden=device_iden)

    # push = p.get_push('ujAjoxHjkmisjAmJtb1z08')
    # pprint(push)
