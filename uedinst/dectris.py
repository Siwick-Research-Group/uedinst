import base64
import os.path
import json
import re
import fnmatch
import shutil
from http import client
from urllib import request
import numpy as np
from . import InstrumentException


"""
original class provided by Dectris below
version 2.0
date 2019/03/03
methods renamed and minor changes introduced
"""


class DEigerClient(object):
    """
    class DEigerClient provides a low level interface to the EIGER API
    """

    def __init__(self, host='127.0.0.1', port=80, verbose=False, url_prefix=None, user=None):
        """
        Create a client object to talk to the EIGER API.
        Args:
            host: hostname of the detector computer
            port: port usually 80 (http)
            verbose: bool value
            url_prefix: String prepended to the urls. Should be None. Added for future convenience.
            user: "username:password". Should be None. Added for future convenience.
        """
        super(DEigerClient, self).__init__()
        self._host = host
        self._port = port
        self._version = '1.6.0'
        self._verbose = verbose
        self._urlPrefix = ""
        self._user = None
        self._connectionTimeout = 24 * 3600
        self._connection = client.HTTPConnection(self._host, self._port, timeout=self._connectionTimeout)
        self._serializer = None

        self.set_url_prefix(url_prefix)
        self.set_user(user)

    def serializer(self):
        """
        The serializer object shall have the methods loads(string) and dumps(obj), which load
        the string from json into a python object or store a python object into a json string
        """
        return self._serializer

    def set_serializer(self, serializer):
        """
        Set an explicit serializer object that converts native python objects to json string and vice versa.
        The serializer object shall have the methods loads(string) and dumps(obj), which load
        the string from json into a python object or store a python object into a json string
        """
        self._serializer = serializer

    def set_verbose(self, verbose):
        """ Switch verbose mode on and off.
        Args:
            verbose: bool value
        """
        self._verbose = bool(verbose)

    def set_connection_timeout(self, timeout):
        """
        If DEigerClient has not received a reply from EIGER after
        timeout seconds, the request is aborted. timeout should be at
        least as long as the triggering command takes.
        Args:
            timeout timeout in seconds
        """
        self._connectionTimeout = timeout
        self._connection = client.HTTPConnection(self._host, self._port, timeout=self._connectionTimeout)

    def set_url_prefix(self, url_prefix):
        """Set url prefix, which is the string that is prepended to the
        urls. There is usually no need to call the command explicitly.
        Args:
           url_prefix: String
        """
        if url_prefix is None:
            self._urlPrefix = ""
        else:
            self._urlPrefix = str(url_prefix)
            if len(self._urlPrefix) > 0 and self._urlPrefix[-1] != "/":
                self._urlPrefix += "/"

    def set_user(self, user):
        """
        Set username and password for basic authentication.
        There is usually no need to call the command explicitly.
        Args:
           user: String of the form username:password
        """
        if user is None:
            self._user = None
        else:
            self._user = base64.encodestring(user).replace('\n', '')

    def version(self, module='detector'):
        """
        Get version of a api module (i.e. 'detector', 'filewriter')
        Args:
            module: 'detector' or 'filewriter'
        """
        return self._get_request(url='/{0}{1}/api/version/'.format(self._urlPrefix, module))

    def send_system_command(self, command):
        """
        Sending command "restart" restarts the SIMPLON API on the EIGER control unit
        """
        return self._put_request(self._url('system', 'command', command), data_type='native', data=None)

    def send_stream_command(self, command):
        """
        Sending command "initialize" restarts the stream interface and disables it
        """
        return self._put_request(self._url('stream', 'command', command), data_type='native', data=None)

    def list_detector_config_params(self):
        """Get list of all detector configuration parameters (param arg of configuration() and setConfiguration()).
        Convenience function, that does detectorConfig(param = 'keys')
        Returns:
            List of parameters.
        """
        return self.detector_config('keys')

    def detector_config(self, param=None, data_type=None):
        """Get detector configuration parameter
        Args:
            param: query the configuration parameter param, if None get full configuration, if 'keys' get all configuration parameters.
            data_type: None (= 'native'), 'native' ( return native python object) or 'tif' (return tif data).
        Returns:
            If param is None get configuration, if param is 'keys' return list of all parameters, else return the value of
            the parameter. If data_type is 'native' a dictionary is returned that may contain the keys: value, min, max,
            allowed_values, unit, value_type and access_mode. If data_type is 'tif', tiff formated data is returned as a python
            string.
        """
        return self._get_request(self._url('detector', 'config', param), data_type)

    def set_detector_config(self, param, value, data_type=None):
        """
        Set detector configuration parameter param.
        Args:
            param: Parameter
            value: Value to set. If data_type is 'tif' value may be a string containing the tiff data or
                   a file object pointing to a tiff file.
            data_type: None, 'native' or 'tif'. If None, the data type is auto determined. If 'native' value
                      may be a native python object (e.g. int, float, str), if 'tif' value shell contain a
                      tif file (python string or file object to tif file).
        Returns:
            List of changed parameters.
        """
        return self._put_request(self._url('detector', 'config', param), data_type, value)

    def set_detector_config_multiple(self, *params):
        """
        Convenience function that calls setDetectorConfig(param,value,data_type = None) for
        every pair param, value in *params.
        Args:
            *params: List of successive params of the form param0, value0, param1, value1, ...
                     The parameters are set in the same order they appear in *params.
        Returns:
            List of changed parameters.
        """
        change_list = []
        p = None
        for x in params:
            if p is None:
                p = x
            else:
                data = x
                change_list += self.set_detector_config(param=p, value=data, data_type=None)
                p = None
        return list(set(change_list))

    def list_detector_commands(self):
        """
        Get list of all commands that may be sent to EIGER via sendDetectorCommand().
        Returns:
            List of commands
        """
        return self._get_request(self._url('detector', 'command', 'keys'))

    def send_detector_command(self, command, parameter=None):
        """
        Send command to EIGER. The list of all available commands is obtained via listCommands().
        Args:
            command: Detector command
            parameter: Call command with parameter. If command = "trigger" a float parameter may be passed
        Returns:
            The commands 'arm' and 'trigger' return a dictionary containing 'sequence id'.
        """
        return self._put_request(self._url('detector', 'command', command), data_type='native', data=parameter)

    def detector_status(self, param='keys'):
        """Get detector status information
        Args:
            param: query the status parameter param, if 'keys' get all status parameters.
        Returns:
            If param is None get configuration, if param is 'keys' return list of all parameters, else return dictionary
            that may contain the keys: value, value_type, unit, time, state, critical_limits, critical_values
        """
        return self._get_request(self._url('detector', 'status', parameter=param))

    def file_writer_config(self, param='keys'):
        """Get filewriter configuration parameter
        Args:
            param: query the configuration parameter param, if 'keys' get all configuration parameters.
        Returns:
            If param is None get configuration, if param is 'keys' return list of all parameters, else return dictionary
            that may contain the keys: value, min, max, allowed_values, unit, value_type and access_mode
        """
        return self._get_request(self._url('filewriter', 'config', parameter=param))

    def set_file_writer_config(self, param, value):
        """
        Set file writer configuration parameter param.
        Args:
            param: parameter
            value: value to set
        Returns:
            List of changed parameters.
        """
        return self._put_request(self._url('filewriter', 'config', parameter=param), data_type='native', data=value)

    def send_file_writer_command(self, command):
        """
        Send filewriter command to EIGER.
        Args:
            command: Command to send (up to now only "clear")
        Returns:
            Empty string
        """
        return self._put_request(self._url("filewriter", "command", parameter=command), data_type="native")

    def file_writer_status(self, param='keys'):
        """Get filewriter status information
        Args:
            param: query the status parameter param, if 'keys' get all status parameters.
        Returns:
            If param is None get configuration, if param is 'keys' return list of all parameters, else return dictionary
            that may contain the keys: value, value_type, unit, time, state, critical_limits, critical_values
        """
        return self._get_request(self._url('filewriter', 'status', parameter=param))

    def file_writer_files(self, filename=None, method='GET'):
        """
        Obtain file from detector.
        Args:
             filename: Name of file on the detector side. If None return list of available files
             method: 'GET' (get the content of the file) or 'DELETE' (delete file from server)
        Returns:
            List of available files if 'filename' is None,
            else if method is 'GET' the content of the file.
        """
        if method == 'GET':
            if filename is None:
                return self._get_request(self._url('filewriter', 'files'))
            else:
                return self._get_request(url='/{0}data/{1}'.format(self._urlPrefix, filename), data_type='hdf5')
        elif method == 'DELETE':
            return self._del_request(url='/{0}data/{1}'.format(self._urlPrefix, filename))
        else:
            raise RuntimeError('Unknown method {0}'.format(method))

    def file_writer_save(self, filename, target_dir, regex=False):
        """
        Saves filename in targetDir. If regex is True, filename is considered to be a regular expression.
        Save all files that match filename
        Args:
            filename: Name of source file, may contain the wildcards '*' and '?' or regular expressions
            target_dir: Directory, where to store the files
            regex: look for regex in filename
        """
        if regex:
            pattern = re.compile(filename)
            [self.file_writer_save(f, target_dir) for f in self.file_writer_files() if pattern.match(f)]
        elif any([c in filename for c in ['*', '?', '[', ']']]):
            # for f in self.fileWriterFiles():
            #    self._log('DEBUG ', f, '  ', fnmatch.fnmatch(f,filename))
            [self.file_writer_save(f, target_dir) for f in self.file_writer_files() if fnmatch.fnmatch(f, filename)]
        else:
            target_path = os.path.join(target_dir, filename)
            url = 'http://{0}:{1}/{2}data/{3}'.format(self._host, self._port, self._urlPrefix, filename)
            req = request.urlopen(url, timeout=self._connectionTimeout)
            with open(target_path, 'wb') as fp:
                self._log('Writing ', target_path)
                shutil.copyfileobj(req, fp, 512 * 1024)
            # self._getRequest(url = '/{0}data/{1}'.format(self._urlPrefix, filename), data_type = 'hdf5',file_id = targetFile)
            # targetFile.write(self.fileWriterFiles(filename))
            assert os.access(target_path, os.R_OK)
        return

    def monitor_config(self, param='keys'):
        """Get monitor configuration parameter
        Args:
            param: query the configuration parameter param, if 'keys' get all configuration parameters.
        Returns:
            If param is 'keys' return list of all parameters, else return dictionary
            that may contain the keys: value, min, max, allowed_values, unit, value_type and access_mode
        """
        return self._get_request(self._url('monitor', 'config', parameter=param))

    def set_monitor_config(self, param, value):
        """
        Set monitor configuration parameter param.
        Args:
            param: parameter
            value: value to set
        Returns:
            List of changed parameters.
        """
        return self._put_request(self._url('monitor', 'config', parameter=param), data_type='native', data=value)

    def monitor_images(self, param=None):
        """
        Obtain file from detector.
        Args:
             param: Either None (return list of available frames) or "monitor" (return latest frame),
                    "next"  (next image from buffer) or tuple(sequence id, image id) (return specific image)
        Returns:
            List of available frames (param = None) or tiff content of image file (param = "next", "monitor", (seqId,imgId))
        """
        if param is None:
            return self._get_request(self._url('monitor', 'images', parameter=None))
        elif param == "next":
            return self._get_request(self._url('monitor', "images", parameter="next"), data_type="tif")
        elif param == "monitor":
            return self._get_request(self._url('monitor', 'images', parameter="monitor"), data_type="tif")
        else:
            try:
                seq_id = int(param[0])
                img_id = int(param[1])
                return self._get_request(self._url('monitor', "images", parameter="{0}/{1}".format(seq_id, img_id)),
                                         data_type='tif')
            except (TypeError, ValueError):
                pass
        raise RuntimeError('Invalid parameter {0}'.format(param))

    def monitor_save(self, param, path):
        """
        Save frame to path as tiff file.
        Args:
            param: Either None (return list of available frames) or "monitor" (return latest frame),
                   "next"  (next image from buffer) or tuple(sequence id, image id) (return specific image)
            path: path to image save dir
        Returns:
            None
        """
        data = None
        if param in ["next", "monitor"]:
            data = self.monitor_images(param)
        else:
            try:
                int(param[0])
                int(param[1])
                data = self.monitor_images(param)
            except (TypeError, ValueError):
                pass
        if data is None:
            raise RuntimeError('Invalid parameter {0}'.format(param))
        else:
            with open(path, 'wb') as f:
                self._log('Writing ', path)
                f.write(data)
            assert os.access(path, os.R_OK)
        return

    def monitor_status(self, param="keys"):
        """
        Get monitor status information
        Args:
            param: query the status parameter param, if 'keys' get all status parameters.
        Returns:
            Dictionary that may contain the keys: value, value_type, unit, time, state,
            critical_limits, critical_values
        """
        return self._get_request(self._url('monitor', 'status', parameter=param))

    def send_monitor_command(self, command):
        """
        Send monitor command to EIGER.
        Args:
            command: Command to send (up to now only "clear")
        Returns:
            Empty string
        """
        return self._put_request(self._url("monitor", "command", parameter=command), data_type="native")

    def stream_config(self, param='keys'):
        """
        Get stream configuration parameter
        Args:
            param: query the configuration parameter param, if 'keys' get all configuration parameters.
        Returns:
            If param is 'keys' return list of all parameters, else return dictionary
            that may contain the keys: value, min, max, allowed_values, unit, value_type and access_mode
        """
        return self._get_request(self._url('stream', 'config', parameter=param))

    def set_stream_config(self, param, value):
        """
        Set stream configuration parameter param.
        Args:
            param: parameter
            value: value to set
        Returns:
            List of changed parameters.
        """
        return self._put_request(self._url('stream', 'config', parameter=param), data_type='native', data=value)

    def stream_status(self, param):
        """Get stream status information
        Args:
            param: query the status parameter param, if 'keys' get all status parameters.
        Returns:
            Dictionary that may contain the keys: value, value_type, unit, time, state,
            critical_limits, critical_values
        """
        return self._get_request(self._url('stream', 'status', parameter=param))

    # Private Methods
    def _log(self, *args):
        if self._verbose:
            print(' '.join([str(elem) for elem in args]))

    def _url(self, module, task, parameter=None):
        url = "/{0}{1}/api/{2}/{3}/".format(self._urlPrefix, module, self._version, task)
        if not parameter is None:
            url += '{0}'.format(parameter)
        return url

    def _get_request(self, url, data_type='native', file_id=None):
        if data_type is None:
            data_type = 'native'
        if data_type == 'native':
            mime_type = 'application/json; charset=utf-8'
        elif data_type == 'tif':
            mime_type = 'application/tiff'
        elif data_type == 'hdf5':
            mime_type = 'application/hdf5'
        return self._request(url, 'GET', mime_type, file_id=file_id)

    def _put_request(self, url, data_type, data=None):
        data, mime_type = self._prepare_data(data, data_type)
        return self._request(url, 'PUT', mime_type, data)

    def _del_request(self, url):
        self._request(url, 'DELETE', mime_type=None)
        return None

    def _request(self, url, method, mime_type, data=None, file_id=None):
        if data is None:
            body = ''
        else:
            body = data
        headers = {}
        if method == 'GET':
            headers['Accept'] = mime_type
        elif method == 'PUT':
            headers['Content-type'] = mime_type
        if not self._user is None:
            headers["Authorization"] = "Basic {0}".format(self._user)

        self._log('sending request to {0}'.format(url))
        number_of_tries = 0
        response = None
        while response is None:
            try:
                self._connection.request(method, url, body=data, headers=headers)
                response = self._connection.getresponse()
            except Exception as e:
                number_of_tries += 1
                if number_of_tries == 50:
                    self._log("Terminate after {0} tries\n".format(number_of_tries))
                    raise e
                self._log("Failed to connect to host. Retrying\n")
                self._connection = client.HTTPConnection(self._host, self._port, timeout=self._connectionTimeout)
                continue

        status = response.status
        reason = response.reason
        if file_id is None:
            data = response.read()
        else:
            buffer_size = 8 * 1024
            while True:
                data = response.read(buffer_size)
                if len(data) > 0:
                    file_id.write(data)
                else:
                    break

        mime_type = response.getheader('content-type', 'text/plain')
        self._log('Return status: ', status, reason)
        if not response.status in range(200, 300):
            raise RuntimeError((reason, data))
        if 'json' in mime_type:
            if self._serializer is None:
                return json.loads(data)
            else:
                return self._serializer.loads(data)
        else:
            return data

    def _prepare_data(self, data, data_type):
        if data is None:
            return '', 'text/html'
        if data_type != 'native':
            if type(data) == 'file':
                data = data.read()
            if data_type is None:
                mime_type = self._guess_mime_type(data)
                if not mime_type is None:
                    return data, mime_type
            elif data_type == 'tif':
                return data, 'application/tiff'
        mime_type = 'application/json; charset=utf-8'
        if self._serializer is None:
            return json.dumps({'value': data}), mime_type
        else:
            return self._serializer.dumps({"value": data}), mime_type

    def _guess_mime_type(self, data):
        if type(data) == str:
            if data.startswith('\x49\x49\x2A\x00') or data.startswith('\x4D\x4D\x00\x2A'):
                self._log('Determined mimetype: tiff')
                return 'application/tiff'
            if data.startswith('\x89\x48\x44\x46\x0d\x0a\x1a\x0a'):
                self._log('Determined mimetype: hdf5')
                return 'application/hdf5'
        return None


"""
wrapper to make the use more pythonic
"""

# CONSTANTS
# these lists are read by the following classes to generate some of their methods
CONFIGS_READ = ['description',
                'detector_number',
                'eiger_fw_version',
                'software_version',
                'x_pixel_size',
                'y_pixel_size',
                'x_pixels_in_detector',
                'y_pixels_in_detector',
                'number_of_excluded_pixels',
                'bit_depth_image',
                'bit_depth_readout',
                'sensor_material',
                'sensor_thickness',
                ]
CONFIGS_WRTIE_NUM = ['beam_center_x',
                     'beam_center_y',
                     'count_time',
                     'frame_time',
                     'nimages',
                     'ntrigger',
                     'trigger_start_delay',
                     ]
STATS = ['state', 'time', 'humidity', 'temperature']
COMMANDS = ['initialize', 'arm', 'disarm', 'trigger', 'cancel', 'abort', 'check_connections', 'hv_reset']
FW_STATS = ['buffer_free', 'files', 'state']
FW_COMMANDS = ['clear']
MON_STATS = ['buffer_fill_level', 'dropped', 'error', 'monitor_image_number', 'next_image_number', 'state']
MON_COMMANDS = ['clear']


class FileWriter:
    """
    class for interaction with the filewriter subsystem of the Dectris DCU
    """

    def __init__(self, parent):
        self.parent = parent

        # read available command from constants defined above and create corresponding methods
        for command in FW_COMMANDS:
            setattr(self, command, self.__make_command_method(command))

    def __getattribute__(self, key):
        """
        if the requested attribute represents a state of the filewriter subsystem of the DCU, the api is called to
        return the state
        for all other attributes the default behaviour of object is mirrored
        """
        if key in FW_STATS:
            return self.parent.file_writer_status(key)['value']
        return object.__getattribute__(self, key)

    def __make_command_method(self, command):
        """
        method factory for commands that may be sent to the filewriter subsystem of the DCU
        """

        def command_method():
            self.parent.send_file_writer_command(command)

        command_method.__name__ = command
        return command_method

    def save(self, *args, **kwargs):
        self.parent.file_writer_save(*args, **kwargs)

    """
    all methods below mirror the names of the variables found in the SIMPLON API manual
    """

    @property
    def image_nr_start(self):
        return self.parent.file_writer_config('image_nr_start')['value']

    @image_nr_start.setter
    def image_nr_start(self, i):
        if not isinstance(i, int):
            raise InstrumentException(f'setting image_nr_start requires value of type int; not {type(i)}')
        self.parent.set_file_writer_config('image_nr_start', i)

    @property
    def mode(self):
        return self.parent.file_writer_config('mode')['value']

    @mode.setter
    def mode(self, mode):
        if mode not in ['enabled', 'disabled']:
            raise InstrumentException(f'setting mode requires "enabled" or "disabled"')
        self.parent.set_file_writer_config('mode', mode)

    @property
    def name_pattern(self):
        return self.parent.file_writer_config('name_pattern')['value']

    @name_pattern.setter
    def name_pattern(self, pattern):
        if not isinstance(pattern, str):
            raise InstrumentException(f'setting name_pattern requires value of type str; not {type(pattern)}')
        self.parent.set_file_writer_config('name_pattern', pattern)

    @property
    def nimages_per_file(self):
        return self.parent.file_writer_config('nimages_per_file')['value']

    @nimages_per_file.setter
    def nimages_per_file(self, n):
        if not isinstance(n, int):
            raise InstrumentException(f'setting nimages_per_file requires value of type int; not {type(n)}')
        if n < 0:
            raise InstrumentException('setting nimages_per_file cannot be negative')
        self.parent.set_file_writer_config('nimages_per_file', n)


class Monitor:
    """
    class for interaction with the monitor subsystem of the Dectris DCU
    """

    def __init__(self, parent):
        self.parent = parent

        # read available command from constants defined above and create corresponding methods
        for command in MON_COMMANDS:
            setattr(self, command, self.__make_command_method(command))

    def __getattribute__(self, key):
        """
        if the requested attribute represents a state of the monitor subsystem of the DCU, the api is called to
        return the state
        for all other attributes the default behaviour of object is mirrored
        """
        if key in MON_STATS:
            return self.parent.monitor_status(key)['value']
        return object.__getattribute__(self, key)

    def __make_command_method(self, command):
        """
        method factory for commands that may be sent to the filewriter subsystem of the DCU
        """

        def command_method():
            self.parent.send_monitor_command(command)

        command_method.__name__ = command
        return command_method

    @property
    def last_image(self):
        """
        return the newest image in monitor
        """
        return self.parent.monitor_images('monitor')

    @property
    def first_image(self):
        """
        return the oldest image in monitor
        """
        return self.parent.monitor_images('next')

    @property
    def image_list(self):
        """
        return list of images in monitor
        """
        return self.parent.monitor_images(None)

    def save_last_image(self, path):
        """
        save the newest image in monitor to disk
        """
        self.parent.monitor_save('monitor', path)

    def save_first_image(self, path):
        """
        save the oldest image in monitor to disk
        """
        self.parent.monitor_save('next', path)

    """
    all methods below mirror the names of the variables found in the SIMPLON API manual
    """

    @property
    def buffer_size(self):
        return self.parent.monitor_config('buffer_size')['value']

    @buffer_size.setter
    def buffer_size(self, n):
        if not isinstance(n, int):
            raise InstrumentException(f'setting buffer_size requires value of type int; not {type(n)}')
        if n < 0:
            raise InstrumentException('setting buffer_size cannot be negative')
        # TODO: ADD CHECK FOR MAX VALUE
        self.parent.set_monitor_config('buffer_size', n)

    @property
    def discard_new(self):
        return self.parent.monitor_config('discard_new')['value']

    @discard_new.setter
    def discard_new(self, state):
        if not isinstance(state, bool):
            raise InstrumentException(f'setting discard new must be of type bool; not {type(state)}')
        self.parent.set_monitor_config('discard_new', state)

    @property
    def mode(self):
        return self.parent.set_monitor_config('mode')['value']

    @mode.setter
    def mode(self, mode):
        if mode not in ['enabled', 'disabled']:
            raise InstrumentException(f'setting mode requires "enabled" or "disabled"')
        self.parent.set_monitor_config('mode', mode)


class Quadro(DEigerClient):
    """
    main class for interacting with the Dectris DCU and the connected Detector
    all interactions with the detector itself are bound to self
    all interactions with the monitor subsystem are bound to self.mon
    all interactions with the filewriter subsystem are ound to self.fw
    the stream subsystem is yet to be added
    """

    def __init__(self, *args, **kwargs):
        """
        all arguments of the __init__ method are passed to the SIMPLON API DEigerClient class
        """
        super(Quadro, self).__init__(*args, **kwargs)

        # read available command from constants defined above and create corresponding methods
        for command in COMMANDS:
            setattr(self, command, self.__make_command_method(command))

        # creating instances of subsystems
        self.fw = FileWriter(parent=self)
        self.mon = Monitor(parent=self)

    def __getattribute__(self, key):
        """
        if the requested attribute represents a state of the detector, the api is called to return it
        for all other attributes the default behaviour of object is mirrored
        """
        if key in CONFIGS_READ or key in CONFIGS_WRTIE_NUM:
            return self.detector_config(key)['value']
        if key in STATS:
            return self.detector_status(key)['value']
        return object.__getattribute__(self, key)

    def __setattr__(self, key, value):
        """
        if the attribute to set represents a writeable numeric configuration of the detector, the api is called
        to write it
        for all other attributes the default behaviour of object is mirrored (or overwritten in the following)
        """
        if key in CONFIGS_WRTIE_NUM:
            if not isinstance(value, (int, float)):
                raise InstrumentException(f'setting {key} requires value of type int or float; not {type(value)}')
            ans = self.detector_config('frame_time')
            if 'min' in ans.keys():
                low = ans['min']
            else:
                low = -np.inf
            if 'max' in ans.keys():
                high = ans['max']
            else:
                high = np.inf
            if value < low or value > high:
                raise InstrumentException(f'setting out of range: {low} < {key} < {high}')
            self.set_detector_config(key, value)
        else:
            object.__setattr__(self, key, value)

    def __str__(self):
        """
        get basic detector info from print function
        """
        return f'Detector:                 {self.description}\n' \
               f'Serial:                   {self.detector_number}\n' \
               f'Eiger FW Version:         {self.eiger_fw_version}\n' \
               f'Decetor software Version: {self.software_version}\n' \
               f'Resolution:               {self.x_pixels_in_detector}x{self.y_pixels_in_detector}\n' \
               f'Pixel size:               {self.x_pixel_size * 1e6}x{self.y_pixel_size * 1e6} µm^2'

    def __make_command_method(self, command):
        """
        method factory for commands that may be sent to the detector
        """

        def command_method():
            self.send_detector_command(command)

        command_method.__name__ = command
        return command_method

    """
    all methods below mirror the names of the variables found in the SIMPLON API manual
    """

    @property
    def auto_summation(self):
        return self.detector_config('auto_summation')['value']

    @auto_summation.setter
    def auto_summation(self, status):
        if not isinstance(status, bool):
            raise InstrumentException('auto_summation property is expecting dtype "bool"')
        self.set_detector_config('auto_summation', status)

    @property
    def incident_energy(self):
        return self.detector_config('incident_energy')['value']

    @incident_energy.setter
    def incident_energy(self, e):
        allowed = np.array(self.detector_config('incident_energy')['allowed_values'])
        if not isinstance(e, (int, float)):
            raise InstrumentException('incident energy property is expecting dtype "int"')
        if e not in allowed:
            e = float(allowed[np.argmin(abs(allowed - e))])
            print(f'WARNING: given incident energy is not allowed; rounding to nearest allowed energy {e:.0f}eV')
        self.set_detector_config('incident_energy', e)

    @property
    def trigger_mode(self):
        return self.detector_config('trigger_mode')['value']

    @trigger_mode.setter
    def trigger_mode(self, mode):
        allowed = self.detector_config('trigger_mode')['allowed_values']
        if mode not in allowed:
            raise InstrumentException(f'trigger mode {mode} not allowed; use one of {allowed}')
        self.set_detector_config('trigger_mode', mode)
