import requests
import os
import json
from . import get_base_path


IP = "localhost"
PORT = 8080
DACS_FILE = os.path.join(get_base_path(), "cheetah_configs", "tpx3-demo.dacs")
BPC_FILE = os.path.join(get_base_path(), "cheetah_configs", "tpx3-demo.bpc")


class CheetahGetException(Exception):
    pass


class CheetahPutException(Exception):
    pass


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    def __repr__(self):
        ret_str = ""
        for k, v in self.items():
            ret_str += f"{k}: {v}\n"
        return ret_str[:-1]


class Cheetah:
    def __init__(self, ip, port, dacs_file, bpc_file):
        self.url = f"http://{ip}:{port}"
        self._dacs = dacs_file
        self._bpc = bpc_file

        self.__get_request("")  # check if interface is reachable

        # upload DACS and BPC
        self.dacs = self._dacs
        self.bpc = self._bpc

    def acquire(self):
        self.__get_request("/measurement/start")

    @property
    def config(self):
        data = self.__get_request("/detector/config").text
        return AttrDict(json.loads(data))

    @config.setter
    def config(self, config):
        self.__put_request("/detector/config", json.dumps(config))

    @property
    def dacs(self):
        return self._dacs

    @dacs.setter
    def dacs(self, dacs):
        self.__get_request("/config/load?format=dacs&file=" + dacs)

    @property
    def bpc(self):
        return self._bpc

    @bpc.setter
    def bpc(self, bpc):
        self.__get_request("/config/load?format=pixelconfig&file=" + bpc)

    def __get_request(self, url_extension):
        url = self.url + url_extension
        response = requests.get(url=url)
        if response.status_code != 200:
            raise CheetahGetException(
                f"Failed GET request: {url}, {response.status_code}: {response.text}"
            )
        return response

    def __put_request(self, url_extension, data):
        url = self.url + url_extension
        response = requests.put(url=url, data=data)
        if response.status_code != 200:
            raise CheetahGetException(
                f"Failed PUT request: {url}, {response.status_code}: {response.text}"
            )
        return response


if __name__ == "__main__":
    C = Cheetah(IP, PORT, DACS_FILE, BPC_FILE)
    conf = C.config
    conf.nTriggers = 3
    conf.TriggerPeriod = 0.4
    conf.ExposureTime = 0.1
    conf.TriggerMode = "AUTOTRIGSTART_TIMERSTOP"
    C.config = conf
    C.acquire()
