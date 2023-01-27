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


class AwareAttrDict(dict):
    def __init__(self, initial_dict, parent=None):
        self.__dict__ = self
        self.__parent = parent
        for k, v in initial_dict.items():
            if isinstance(v, dict):
                initial_dict[k] = AwareAttrDict(v, parent=self)
        super().__init__(initial_dict)

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            _value = AwareAttrDict(value)
        else:
            _value = value
        super().__setitem__(key, _value)
        self.__entry_changed_signal()

    def __setattr__(self, key, value):
        if not key.startswith("_"):
            if isinstance(value, dict):
                value = AwareAttrDict(value)
            super().__setattr__(key, value)
            self.__entry_changed_signal()
        else:
            super().__setattr__(key, value)

    def __entry_changed_signal(self):
        if self.__parent is not None and isinstance(self.__parent, AwareAttrDict):
            self.__parent.__entry_changed_signal()
        else:
            if hasattr(self.__parent, "_entry_changed_action"):
                self.__parent._entry_changed_action()
            else:
                self._entry_changed_action()

    def _entry_changed_action(self):
        pass


class Cheetah:
    def __init__(self, ip, port, dacs_file=None, bpc_file=None):
        self._url = f"http://{ip}:{port}"
        # upload DACS and BPC
        if dacs_file is not None:
            self._dacs = dacs_file
            self.dacs = self._dacs
        if bpc_file is not None:
            self._bpc = bpc_file
            self.bpc = self._bpc

        self.__get_request("")  # check if interface is reachable

    def __setattr__(self, key, val):
        if not key.startswith("_"):
            print(key, val)
        return super().__setattr__(key, val)

    def acquire(self):
        self.__get_request("/measurement/start")

    @property
    def Config(self):
        return self.Config

    @Config.setter
    def Config(self, config):
        self.__put_request("/detector/config", config)

    @property
    def Dacs(self):
        return self._dacs

    @Dacs.setter
    def Dacs(self, dacs):
        self.__get_request("/config/load?format=dacs&file=" + dacs)

    @property
    def Bpc(self):
        return self._bpc

    @Bpc.setter
    def Bpc(self, bpc):
        self.__get_request("/config/load?format=pixelconfig&file=" + bpc)

    def __update_info(self):
        info = self.__get_request("/*")
        for k, v in info.items():
            if not k.startswith("_"):
                self.__dict__[k] = v

    def __get_request(self, url_extension):
        url = self._url + url_extension
        response = requests.get(url=url)
        if response.status_code != 200:
            raise CheetahGetException(
                f"Failed GET request: {url}, {response.status_code}: {response.text}"
            )
        try:
            response_json = json.loads(response.text)
            return AwareAttrDict(response_json, parent=self)
        except json.decoder.JSONDecodeError:
            return response.text

    def __put_request(self, url_extension, data):
        url = self.url + url_extension
        response = requests.put(url=url, data=json.dumps(data))
        if response.status_code != 200:
            raise CheetahGetException(
                f"Failed PUT request: {url}, {response.status_code}: {response.text}"
            )
        return json.loads(response.text)

    def _entry_changed_action(self):
        print("update config!")


if __name__ == "__main__":
    # C = Cheetah(IP, PORT, DACS_FILE, BPC_FILE)
    C = Cheetah(IP, PORT)
    # conf = C.config
    # conf.nTriggers = 3
    # conf.TriggerPeriod = 0.4
    # conf.ExposureTime = 0.1
    # conf.TriggerMode = "AUTOTRIGSTART_TIMERSTOP"
    # C.config = conf
    # C.acquire()

    C._Cheetah__update_info()
    # print(type(C.Measurement.Config))
    # print(C.Measurement.Config.Corrections)
    # C.Detector["Config"]["nTriggers"] = 5
    # C.Detector["Config"]["nTriggers"] = 50
    C.Detector.Config.nTriggers = 5
    C.Detector.Config.nTriggers = 50
    # C.Detector.Config.nTriggers = 5

