import glob
import os.path
from importlib.machinery import SourceFileLoader
import traceback
from quassel import *
from quasselclient import QuasselClient

class QuasselBot(QuasselClient):
    def __init__(self, config):
        super().__init__(config)
        self.pushNotification = None
        self.plugins = []
        self.defaultPlugins = [
            'logger',
        ]

    @property
    def pluginsToLoad(self):
        return getattr(self.config, 'enabledPlugins', self.defaultPlugins)

    def loadPlugins(self):
        for pluginFilepath in glob.glob('plugins/*.py'):
            self.loadPlugin(pluginFilepath)

    def loadPlugin(self, pluginFilepath):
        pluginName = pluginFilepath[len('plugins/'):-len('.py')]
        if pluginName not in self.pluginsToLoad:
            return
        
        try:
            pluginModuleName = 'plugin_' + pluginName
            loader = SourceFileLoader(pluginModuleName, pluginFilepath)
            pluginModule = loader.load_module()
            self.plugins.append(pluginModule)
            print('Plugin "{}" loaded.'.format(pluginFilepath))
        except Exception as e:
            print('Error loading plugin "{}".'.format(pluginFilepath))
            traceback.print_exc()

    def pluginCall(self, fnName, *args):
        for plugin in self.plugins:
            try:
                fn = getattr(plugin, fnName, None)
                if fn:
                    fn(self, *args)
            except Exception as e:
                print('Error while calling {}.{}'.format(plugin.__name__, fnName))
                traceback.print_exc()

    def onSessionStarted(self):
        # self.sendNetworkInits() # Slooooow. Also adds 4-8 Mb to RAM.
        # self.sendBufferInits()

        self.pluginCall('onSessionStarted')

    def onMessageRecieved(self, message):
        self.pluginCall('onMessageRecieved', message)

    def onSocketClosed(self):
        print('\n\nSocket Closed\n\nReconnecting\n')
        self.reconnect()



if __name__ == '__main__':
    import sys, os
    if not os.path.exists('config.py'):
        print('Please create a config.py as mentioned in the ReadMe.')
        sys.exit(1)

    import config
    quasselClient = QuasselBot(config)
    quasselClient.loadPlugins()
    quasselClient.run()

    quasselClient.disconnectFromHost()
