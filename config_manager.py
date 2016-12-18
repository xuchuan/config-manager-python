"""

"""

import copy
import os
from ConfigParser import RawConfigParser
from abc import abstractmethod
from datetime import datetime


class ConfigItem(str):
    def __init__(self, key, value, source, last_update_time):
        """
        :param key:
        :type key: str
        :param value:
        :type value: str
        :param source:
        :type source: str
        :param last_update_time:
        :type last_update_time: datetime
        """
        str.__init__(value)
        self.key = key
        self.source = source
        self.last_update_time = last_update_time

    def as_int(self):
        """
        :return:
        :rtype: int
        """
        return int(self)

    def as_float(self):
        """
        :return:
        :rtype: float
        """
        return float(self)

    def as_bool(self):
        """

        :return:
        :rtype: bool
        """
        return bool(self)

    def as_str_list(self):
        """
        :return:
        ":rtype: list of str
        """
        return self.split(',')

    def as_int_list(self):
        """
        :return:
        ":rtype: list of int
        """
        ret = self.split(',')
        for i in range(0, len(ret)):
            ret[i] = int(ret[i])
        return ret

    def as_float_list(self):
        """

        :return:
        ":rtype: list of float
        """
        ret = self.split(',')
        for i in range(0, len(ret)):
            ret[i] = float(ret[i])
        return ret


class BaseConfiguration(object):
    def __init__(self, name, base_config, item_dict=None):
        """
        :param name:
        :type name: str
        :param base_config:
        :type base_config: BaseConfiguration
        :param item_dict:
        :type item_dict: dict
        """
        self.name = name
        self.base_config = base_config
        if item_dict is None:
            self.item_dict = dict()
        else:
            self.item_dict = item_dict

    def __getitem__(self, key):
        """

        :param key:str
        :return:
        ":rtype: ConfigItem
        """
        try:
            return self.item_dict[key]
        except KeyError:
            if self.base_config is None:
                raise
            else:
                return self.base_config[key]

    def keys(self):
        """

        :return:
        :rtype: list of str
        """
        if self.base_config is None:
            return self.item_dict.keys()
        keys = self.base_config.keys()
        for key in self.item_dict.iterkeys():
            if key not in self.base_config.item_dict:
                keys.append(key)
        return keys

    def items(self):
        """

        :return:
        :rtype: list of tuple
        """
        if self.base_config is None:
            return self.item_dict.items()
        ret = self.base_config.items()
        for k, v in self.item_dict.iteritems():
            if k not in self.base_config.item_dict:
                ret.append((k, v))
        return ret

    def reload(self):
        if self.base_config is not None:
            self.base_config.reload()
        self.do_reload()

    def copy(self):
        """
        Returns a shallow copy of the configuration
        :return: a shallow copy of the configuration
        ":rtype: BaseConfiguration
        """
        return copy.copy(self)

    @abstractmethod
    def do_reload(self):
        pass

    def _do_reload_from_dict(self, value_dict):
        """

        :param value_dict:
        ":type value_dict: dict
        """
        item_dict = dict(self.item_dict)
        value_changed = False
        for k, v in value_dict.iteritems():
            if item_dict.get(k) != v:
                item_dict[k] = ConfigItem(k, v, self.name, datetime.now())
                value_changed = True
        if value_changed:
            self.item_dict = item_dict

    def _do_reload_from_ini(self, filename):
        """

        :param filename:
        :type filename: str
        """
        item_dict = dict(self.item_dict)
        value_changed = False
        parser = RawConfigParser()
        parser.read(filename)
        for section in parser.sections():
            for k, v in parser.items(section):
                k = section + '.' + k
                if item_dict.get(k) != v:
                    item_dict[k] = ConfigItem(k, v, self.name, datetime.now())
                    value_changed = True
        if value_changed:
            self.item_dict = item_dict


class DictConfiguration(BaseConfiguration):
    def __init__(self, name, value_dict, base_config=None):
        BaseConfiguration.__init__(self, name, base_config)
        self.value_dict = value_dict
        self.do_reload()

    def do_reload(self):
        self._do_reload_from_dict(self.value_dict)


class IniFileConfiguration(BaseConfiguration):
    def __init__(self, filename, base_config=None):
        BaseConfiguration.__init__(self, filename, base_config)
        self.do_reload()

    def do_reload(self):
        self._do_reload_from_ini(self.name)


class SystemEnvConfiguration(BaseConfiguration):
    def __init__(self, base_config=None):
        BaseConfiguration.__init__(self, "System Environment", base_config)
        self.do_reload()

    def do_reload(self):
        self._do_reload_from_dict(os.environ)
