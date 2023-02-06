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


def strip_awareattrdict(aad):
    plain_dict = {}
    for k, v in aad.items():
        if not k.startswith("_"):
            plain_dict[k] = v
            if isinstance(v, AwareAttrDict):
                plain_dict[k] = strip_awareattrdict(v)
    return plain_dict


class Cheetah:
    VALID_FLIPS = ["horizontal", "vertical"]
    VALID_ROTATIONS = ["left", "right", "180"]

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

    def acquire(self):
        self.__get_request("/measurement/start")

    @property
    def Config(self):
        return self.Config

    @Config.setter
    def Config(self, config):
        self.__put_request("/detector/config", config["Detector"]["Config"])
        self.__put_request("/measurement/config", config["Measurement"]["Config"])

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
        url = self._url + url_extension
        response = requests.put(url=url, data=json.dumps(data))
        if response.status_code != 200:
            raise CheetahGetException(
                f"Failed PUT request: {url}, {response.status_code}: {response.text}"
            )
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return response.text

    def _entry_changed_action(self):
        # print('update conf')
        new_config = {"Detector": self.Detector, "Measurement": self.Measurement, "Server": self.Server}
        new_config = strip_awareattrdict(new_config)
        json.dumps(new_config)
        self.Config = new_config

    def shutdown(self):
        self.__get_request("/server/shutdown")

    def start(self):
        self.__get_request("/measurement/start")

    def stop(self):
        self.__get_request("/measurement/stop")

    def preview(self):
        self.__get_request("/measurement/preview")

    def change_orientation(self, flip=None, rotation=None, reset=True):
        command = "?"
        if reset:
            command += "reset&"

        if flip is not None:
            if flip.lower() not in self.VALID_FLIPS:
                raise CheetahGetException(f"{flip.lower()} is not a valid flip command; use one of {self.VALID_FLIPS}")
            command += f"flip={flip.lower()}&"

        if rotation is not None:
            rotation = str(rotation)
            if rotation.lower() not in self.VALID_ROTATIONS:
                raise CheetahGetException(f"{rotation.lower()} is not a valid rotation command; use on of {self.VALID_ROTATIONS}")
            command += f"rotation={rotation.lower()}&"

        if command.endswith("&"):
            command = command[:-1]

        self.__get_request(f"/detector/layout/{command}")


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
    C.change_orientation(flip='horizontal', rotation=180, reset=True)
