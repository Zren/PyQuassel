from pushbullet import PushBullet

class PushBulletNotification(PushBullet):
    def __init__(self, apiKey):
        super().__init__(apiKey)
        self.activePush = None
        self.device = None

    @property
    def device_iden(self):
        return self.device['iden'] if self.device is not None else None

    def pushMessage(self, channel, senderNick, messageContent, **kwargs):
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

        push = self.push_note(title=title, body=body, device_iden=self.device_iden, **kwargs)
        self.activePush = push

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)

    import config
    # p = PushBullet(config.pushbulletApiKey)
    p = PushBulletNotification(config.pushbulletAccessToken)
    p.device = p.get_device(nickname=config.pushbulletDeviceName)
    # p.device = 'ujAjoxHjkmisjAcc26Tgia'

    
    p.pushMessage('#zren', 'Zren', 'Testing 1')
    import time
    time.sleep(3)
    p.pushMessage('#zren', 'Zren', 'Testing 2')
    time.sleep(10)
    p.pushMessage('#zren', 'Zren', 'Testing 3')


