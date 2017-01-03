"""

"""

import os
import threading
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
        """ Returns the integer represented by the config item value.

        Returns:
            int. the integer represented by the config item value.

        Raises:
            ValueError: if the config item value can not be converted to an integer.
        """
        return int(self)

    def as_float(self):
        """ Returns the float represented by the config item value.

        Returns:
            float. the float represented by the config item value.

        Raises:
            ValueError: if the config item value can not be converted to a float.
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
        self.__bind_dict = dict()
        self.__lock = threading.Lock()

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
        return list(set(self.__item_dict.keys()) | set(self.base_config.keys()))

    def items(self):
        """

        :return:
        :rtype: list of tuple
        """
        item_dict = self.__item_dict
        ret = item_dict.items()
        if self.base_config is not None:
            for k, v in self.base_config.items():
                if k not in item_dict:
                    ret.append((k, v))
        return ret

    def __update_bound_attr(self, key):
        obj, attr, method, default_value = self.__bind_dict[key]
        try:
            value = self.__getitem__(key)
            if method is None:
                setattr(obj, attr, str(value))
            else:
                setattr(obj, attr, getattr(value, method)())
        except KeyError:
            setattr(obj, attr, default_value)

    def bind(self, key, obj, attr, method=None, default_value=None):
        """Bind the configuration key to an attribute. When the configuration value is updated, the associated attribute
        will be updated accordingly. The attribute value will be updated in this method.

        Aware that all bound attributes are updated one by one. You SHOULD NEVER assume that multiple attributes will be
        updated simultaneously.

        Usage:
            # bind 'data_path' to data_store.data_path
            bind('data_path', data_store, 'data_path')

            # bind 'buffer_size' to channel.buffer_size. Type is int and default value is 4096.
            bind('buffer_size', channel, 'buffer_size', 'as_int', 4096)

        Args:
            key (str): The key to bind
            obj (object): The object to whose attribute to be bound
            attr (str): The name of the attribute to be bound
            method (str): The name of a ConfigItem method for type conversion(name starts with 'as_'). If it is None, no
                conversion will be done. That is, the value will be a str.
            default_value (object): the default value to set if the key does not exist in the configuration.

        Raises:
            TypeError: if method is not None and is not of type str
            ValueError: if method is not None and is not a method for type conversion(name starts with 'as_')
        """
        with self.__lock:
            if method is not None:
                if type(method) is not str:
                    raise TypeError('method should be of str type')
                if not method.startswith('as_') and not callable(getattr(ConfigItem, method, None)):
                    raise ValueError('Invalid method ' + method)
            self.__bind_dict[key] = (obj, attr, method, default_value)
            self.__update_bound_attr(key)

    def unbind(self, key):
        """Unbind the key from its associated attribute. Restore the attribute to its default value as specified when
        bound.

        Args:
            key(str): The key to unbind

        Raises:
            KeyError: if the key has not been bound to any attribute
        """
        with self.__lock:
            obj, attr, method, default_value = self.__bind_dict.pop(key)
            setattr(obj, attr, default_value)

    def reload(self, update_bind=True):
        with self.__lock:
            if self.base_config is not None:
                self.base_config.reload(False)
            self._do_reload()
            if not update_bind:
                return

            bind_failure = []
            for k in self.__bind_dict.iterkeys():
                try:
                    self.__update_bound_attr(k)
                except ValueError as e:
                    bind_failure.append(e)
            if len(bind_failure) > 0:
                return bind_failure

    def _do_reload(self):
        pass

    def _get_item_dict(self):
        return dict(self.__item_dict)

    def _set_item_dict(self, item_dict):
        self.__item_dict = dict(item_dict)

    def copy(self):
        """Returns a shallow copy of this configuration

        Returns:
            BaseConfiguration. a shallow copy of this configuration
        """
        if self.base_config is None:
            return BaseConfig(self.name, None, self.__item_dict)
        return BaseConfig(self.name, self.base_config.copy(), self.__item_dict)


def update_from_dict(source, item_dict, value_dict):
    """
    :param source:
    :type source: str
    :param item_dict:
    :type item_dict: dict
    :param value_dict:
    ":type value_dict: dict
    """
    now = datetime.now()
    for k, v in value_dict.iteritems():
        item = item_dict.get(k)
        if item != v:
            item_dict[k] = ConfigItem(k, v, source, now)
    for k in item_dict.keys():
        if k not in value_dict:
            del item_dict[k]


def update_from_ini(source, item_dict, filename):
    """
    :param source:
    :type source: str
    :param item_dict:
    :type item_dict: dict
    :param filename:
    :type filename: str
    """
    parser = RawConfigParser()
    parser.read(filename)
    now = datetime.now()
    keys = set()
    for section in parser.sections():
        for k, v in parser.items(section):
            k = section + '.' + k
            keys.add(k)
            item = item_dict.get(k)
            if item != v:
                item_dict[k] = ConfigItem(k, v, source, now)
    for k in item_dict.keys():
        if k not in keys:
            del item_dict[k]


class DictConfig(BaseConfig):
    def __init__(self, name, value_dict=None, base_config=None):
        BaseConfig.__init__(self, name, base_config)
        if value_dict is None:
            self.value_dict = dict()
        else:
            self.value_dict = value_dict
            self._do_reload()

    def _do_reload(self):
        item_dict = self._get_item_dict()
        update_from_dict(self.name, item_dict, self.value_dict)
        self._set_item_dict(item_dict)


class IniFileConfig(BaseConfig):
    def __init__(self, filename, base_config=None):
        BaseConfig.__init__(self, filename, base_config)
        self._do_reload()

    def _do_reload(self):
        item_dict = self._get_item_dict()
        update_from_ini(self.name, item_dict, self.name)
        self._set_item_dict(item_dict)


class SystemEnvConfig(BaseConfig):
    def __init__(self, base_config=None):
        BaseConfig.__init__(self, "System Environment", base_config)
        self._do_reload()

    def _do_reload(self):
        item_dict = self._get_item_dict()
        update_from_dict(self.name, item_dict, os.environ)
        self._set_item_dict(item_dict)
