"""

"""

import copy
import os
from ConfigParser import RawConfigParser
from datetime import datetime


class ConfigItem(str):
    def __new__(cls, key, value, source, last_update_time):
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
        item = str.__new__(cls, value.strip())
        item.key = key.strip()
        item.source = source.strip()
        item.last_update_time = last_update_time
        return item

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

    def as_str_list(self):
        """
        :return:
        ":rtype: list of str
        """
        if self == '':
            return []
        return self.split(',')

    def as_int_list(self):
        """
        :return:
        ":rtype: list of int
        """
        ret = self.as_str_list()
        for i in range(0, len(ret)):
            ret[i] = int(ret[i])
        return ret

    def as_float_list(self):
        """

        :return:
        ":rtype: list of float
        """
        ret = self.as_str_list()
        for i in range(0, len(ret)):
            ret[i] = float(ret[i])
        return ret


class BaseConfig(object):
    def __init__(self, name, base_config, item_dict=None):
        """
        :param name:
        :type name: str
        :param base_config:
        :type base_config: BaseConfig
        :param item_dict:
        :type item_dict: dict
        """
        self.name = name
        self.base_config = base_config
        if item_dict is None:
            self.__item_dict = dict()
        else:
            self.__item_dict = item_dict

    def __getitem__(self, key):
        """

        :param key:str
        :return:
        ":rtype: ConfigItem
        """
        try:
            return self.__item_dict[key]
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
            return self.__item_dict.keys()
        keys = self.base_config.keys()
        for key in self.__item_dict.iterkeys():
            if key not in self.base_config.__item_dict:
                keys.append(key)
        return keys

    def items(self):
        """

        :return:
        :rtype: list of tuple
        """
        ret = self.__item_dict.items()
        if self.base_config is not None:
            for k, v in self.base_config.items():
                if k not in self.__item_dict:
                    ret.append((k, v))
        return ret

    def reload(self):
        if self.base_config is not None:
            self.base_config.reload()
        self._do_reload()

    def _do_reload(self):
        pass

    def copy(self):
        """
        Returns a shallow copy of the configuration
        :return: a shallow copy of the configuration
        ":rtype: BaseConfiguration
        """
        if self.base_config is None:
            return BaseConfig(self.name, None, self.__item_dict)
        return BaseConfig(self.name, self.base_config.copy(), self.__item_dict)

    def _do_reload_from_dict(self, value_dict):
        """

        :param value_dict:
        ":type value_dict: dict
        """
        old_item_dict = self.__item_dict
        new_item_dict = dict()
        value_changed = False
        for k, v in value_dict.iteritems():
            item = old_item_dict.get(k)
            if item != v:
                new_item_dict[k] = ConfigItem(k, v, self.name, datetime.now())
                value_changed = True
            elif item is not None:
                new_item_dict[k] = item
        if value_changed or len(new_item_dict) != len(old_item_dict):
            self.__item_dict = new_item_dict

    def _do_reload_from_ini(self, filename):
        """

        :param filename:
        :type filename: str
        """
        old_item_dict = self.__item_dict
        new_item_dict = dict()
        value_changed = False
        parser = RawConfigParser()
        parser.read(filename)
        for section in parser.sections():
            for k, v in parser.items(section):
                k = section + '.' + k
                item = old_item_dict.get(k)
                if item != v:
                    new_item_dict[k] = ConfigItem(k, v, self.name, datetime.now())
                    value_changed = True
                elif item is not None:
                    new_item_dict[k] = item
        if value_changed or len(new_item_dict) != len(old_item_dict):
            self.__item_dict = new_item_dict


class DictConfig(BaseConfig):
    def __init__(self, name, value_dict=None, base_config=None):
        BaseConfig.__init__(self, name, base_config)
        if value_dict is None:
            self.value_dict = dict()
        else:
            self.value_dict = value_dict
            self._do_reload()

    def _do_reload(self):
        self._do_reload_from_dict(self.value_dict)


class IniFileConfig(BaseConfig):
    def __init__(self, filename, base_config=None):
        BaseConfig.__init__(self, filename, base_config)
        self._do_reload()

    def _do_reload(self):
        self._do_reload_from_ini(self.name)


class SystemEnvConfig(BaseConfig):
    def __init__(self, base_config=None):
        BaseConfig.__init__(self, "System Environment", base_config)
        self._do_reload()

    def _do_reload(self):
        self._do_reload_from_dict(os.environ)
