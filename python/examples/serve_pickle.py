import sys, os, logging
import asyncio, json
from io import BytesIO
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import xviz_avs
from xviz_avs.builder import XVIZBuilder, XVIZMetadataBuilder
from xviz_avs.server import XVIZServer, XVIZBaseSession

from scenarios.pickle_test import PickleScenario


class ScenarioSession(XVIZBaseSession):
    def __init__(self, socket, request, scenario=PickleScenario()):
        super().__init__(socket, request)
        self._scenario = scenario
        self._socket = socket

    def on_connect(self):
        print("Connected!")
 
    def on_disconnect(self):
        print("Disconnect!")

    async def main(self):
        # metadata = self._scenario.get_metadata()
        file_list = []
        file = open('D:\\项目\\数据标注平台\\平台原型开发\\场景提取模块\\数据demo\\output\\1-frame.pbe','rb')
        metadata = BytesIO(file.read()).read()
        pbe_folder = 'D:\项目\数据标注平台\平台原型开发\场景提取模块\数据demo\output'
        for root, dirs, files_name in os.walk(pbe_folder):
            for file_name in files_name:
                file_list.append(os.path.join(root, file_name))
        file_list.sort()
        print(file_list)
        # await self._socket.send(json.dumps(metadata))
        await self._socket.send(metadata)

        t = 0
        while t < 30:
            # message = self._scenario.get_message(t)
            # await self._socket.send(json.dumps(message))
            num = int(t*10 + 1)
            pbe_file = open(file_list[num],'rb')
            message = BytesIO(pbe_file.read()).read()
            await self._socket.send(message)
            t += 0.1
            await asyncio.sleep(0.1)

class ScenarioHandler:
    def __init__(self):
        pass

    def __call__(self, socket, request):
        return ScenarioSession(socket, request)

if __name__ == "__main__":
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    logging.getLogger("xviz-server").addHandler(handler)

    server = XVIZServer(ScenarioHandler(), port=8081)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server.serve())
    loop.run_forever()
