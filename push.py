
# import pushbullet

# class PushBullet(pushbullet.PushBullet):
#     def refresh(self):
#         pass

#     def get_device(self, nickname):
#         req_device = next((device for device in self.devices if device.nickname == nickname), None)
        
#         if req_device is None:
#             raise InvalidKeyError()
        
#         return req_device

#     def get_push(self, iden):
#         import json
#         r = self._session.get("{}/{}".format(self.PUSH_URL, iden))

#         import requests
#         if r.status_code == requests.codes.ok:
#             return r.json()
#         else:
#             from pushbullet import PushError
#             raise PushError(r.text)

from push2 import PushBullet

class PushBulletNotification(PushBullet):
    def __init__(self, apiKey, deviceName=None):
        super().__init__(apiKey)
        self.activePush = None
        self.device = None
        if deviceName:
            self._load_devices()
            self.device = self.get_device(deviceName)

    def pushMessage(self, channel, senderNick, messageContent):
        messageFormat = '[{}] {}: {}'
        title = ''
        body = ''
        
        if self.activePush is not None:
            push = self.get_push(self.activePush['iden'])
            print(push)
            if not push['dismissed']:
                title = push.get('title', '')
                body = push.get('body', '')
            if push['active']:
                self.delete_push(self.activePush['iden'])

        messageLine = messageFormat.format(channel, senderNick, messageContent)
        if len(title) > 0:
            if len(body) > 0:
                body += '\n' + messageLine
            else:
                body = messageLine
        else:
            title = messageLine

        push = self.push_note(title, body, device=self.device)
        print(push)
        self.activePush = push

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)

    import config
    # p = PushBullet(config.pushbulletApiKey)
    p = PushBulletNotification(config.pushbulletApiKey, deviceName=config.pushbulletDeviceName)
    # p.device = 'ujAjoxHjkmisjAcc26Tgia'

    
    p.pushMessage('#zren', 'Zren', 'Testing 123')
    import time
    time.sleep(3)
    p.pushMessage('#zren', 'Zren', 'Testing 123')
    time.sleep(10)
    p.pushMessage('#zren', 'Zren', 'Testing 123')


