"""

"""

import os
import threading
from ConfigParser import RawConfigParser
from datetime import datetime


class ConfigItem(str):
    """Represents a configuration item.

    Attributes:
        key (str): the configuration key
        source (str): the configuration from which the value comes
        last_update_time (datetime): the time when the value is last updated
    """

    def __new__(cls, key, value, source, last_update_time):
        """Constructs a ConfigItem object

        Args:
            key (str): the configuration key
            value (str): the configuration value
            source (str): the configuration from which the value comes
            last_update_time (datetime): the time when the value is last updated

        Returns:
            ConfigItem: the ConfigItem object
        """
        item = str.__new__(cls, value.strip())
        item.key = key.strip()
        item.source = source.strip()
        item.last_update_time = last_update_time
        return item

    def as_int(self):
        """Returns the integer represented by the config item value.

        Returns:
            int: the integer represented by the config item value.

        Raises:
            ValueError: if the config item value can not be converted to an integer.
        """
        return int(self)

    def as_float(self):
        """Returns the float represented by the config item value.

        Returns:
            float: the float represented by the config item value.

        Raises:
            ValueError: if the config item value can not be converted to a float.
        """
        return float(self)

    def as_str_list(self):
        """Returns the string list represented by the config item value.

        Returns:
            list of str: the string list represented by the config item value.
        """
        if self == '':
            return []
        return self.split(',')

    def as_int_list(self):
        """Returns the int list represented by the config item value.

        Returns:
            list of int: the int list represented by the config item value.
        """
        ret = self.as_str_list()
        for i in range(0, len(ret)):
            ret[i] = int(ret[i])
        return ret

    def as_float_list(self):
        """Returns the float list represented by the config item value.

        Returns:
            list of float: the float list represented by the config item value.
        """
        ret = self.as_str_list()
        for i in range(0, len(ret)):
            ret[i] = float(ret[i])
        return ret


class BindInfo:
    """Contains the information of a configuration-variable binding

    Attributes:
        key(str): the configuration key
        obj(object): the object to which the configuration key binds
        attr(str): the attribute to which the configuration key binds
        method (str): the name of a ConfigItem method for type conversion(name starts with 'as_'). If it is None, no
            conversion will be done. That is, the value will be a str.
        default_value (object): the default value to set if the key does not exist in the configuration.
    """

    def __init__(self, key, obj, attr, method, default_value):
        """Initialize all information

        Args:
            key(str): the configuration key
            obj(object): the object to which the configuration key binds
            attr(str): the attribute to which the configuration key binds
            method (str): the name of a ConfigItem method for type conversion(name starts with 'as_'). If it is None, no
                conversion will be done. That is, the value will be a str.
            default_value (object): the default value to set if the key does not exist in the configuration.
        """
        self.key = key
        self.obj = obj
        self.attr = attr
        self.method = method
        self.default_value = default_value


class BaseConfig(object):
    """Base class of configuration

    Attributes:
        name (str): the name of this configuration
        base_config (BaseConfig): the base configuration, may be None.
        __item_dict (dict): a dict containing all configuration items
    """

    def __init__(self, name, base_config, item_dict=None):
        """Initialize the configuration

        Args:
            name (str): the name of this configuration
            base_config (BaseConfig): the base configuration, may be None.
            item_dict (dict): the initial item dict
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
        """Returns the configuration item.

        Args:
            key (str): the configuration key

        Returns:
            ConfigItem: the corresponding configuration item.

        Raises:
            KeyError: if there is no configuration item matches the specified key
        """
        try:
            return self.__item_dict[key]
        except KeyError:
            if self.base_config is None:
                raise
            else:
                return self.base_config[key]

    def keys(self):
        """Returns all keys in this configuration(including all base configs).

        Returns:
            list of str: all keys in this configuration.
        """
        if self.base_config is None:
            return self.__item_dict.keys()
        return list(set(self.__item_dict.keys()) | set(self.base_config.keys()))

    def items(self):
        """Returns all (key, ConfigItem) pairs in this configuration(including all base configs).

        Returns:
            list of (key, ConfigItem) pairs: all items in this configuration.
        """
        item_dict = self.__item_dict
        ret = item_dict.items()
        if self.base_config is not None:
            for k, v in self.base_config.items():
                if k not in item_dict:
                    ret.append((k, v))
        return ret

    def __update_bound_attr(self, bind_info):
        """
        Args:
            bind_info(BindInfo):
        """
        try:
            value = self.__getitem__(bind_info.key)
            if bind_info.method is None:
                setattr(bind_info.obj, bind_info.attr, str(value))
            else:
                setattr(bind_info.obj, bind_info.attr, getattr(value, bind_info.method)())
        except KeyError:
            setattr(bind_info.obj, bind_info.attr, bind_info.default_value)

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
            key (str): the key to bind
            obj (object): the object to whose attribute to be bound
            attr (str): the name of the attribute to be bound
            method (str): the name of a ConfigItem method for type conversion(name starts with 'as_'). If it is None, no
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
            if key not in self.__bind_dict:
                info_list = []
                self.__bind_dict[key] = info_list
            else:
                info_list = self.__bind_dict[key]

            info = BindInfo(key, obj, attr, method, default_value)
            info_list.append(info)
            self.__update_bound_attr(info)

    def unbind_all(self, key):
        """Unbind the key from its associated attributes. Restore all attributes to their default values.

        Args:
            key(str): the key to unbind

        Raises:
            KeyError: if the key has not been bound to any attribute
        """
        with self.__lock:
            info_list = self.__bind_dict.pop(key)
            for info in info_list:
                setattr(info.obj, info.attr, info.default_value)

    def unbind_one(self, key, obj, attr):
        """Unbind the key from one of its associated attributes. Restore the attribute to its default value.

        Args:
            key(str): the key to unbind
            obj(object): the object to whose attribute to be unbound
            attr(str): the name of the attribute to be unbound

        Raises:
            KeyError: if the key has not been bound to the specified attribute
        """
        with self.__lock:
            info_list = self.__bind_dict[key]
            for i in range(0, len(info_list)):
                info = info_list[i]
                if info.obj == obj and info.attr == attr:
                    setattr(obj, attr, info.default_value)
                    del info_list[i]
                    if len(info_list) == 0:
                        del self.__bind_dict[key]
                    return
            raise KeyError('No key has been bound to %s.%s' % (obj, attr))

    def reload(self, update_bind=True):
        with self.__lock:
            if self.base_config is not None:
                self.base_config.reload(False)
            self._do_reload()
            if not update_bind:
                return

            bind_failure = []
            for info_list in self.__bind_dict.itervalues():
                for info in info_list:
                    try:
                        self.__update_bound_attr(info)
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


def _update_from_dict(source, item_dict, value_dict):
    """Update item_dict using key-value pairs from value_dict.

    Args:
        source (str): the name of source configuration, which is used to create a new ConfigItem.
        item_dict (dict): the dict to be updated.
        value_dict (dict): the source dict
    """
    now = datetime.now()
    for k, v in value_dict.iteritems():
        item = item_dict.get(k)
        if item != v:
            item_dict[k] = ConfigItem(k, v, source, now)
    for k in item_dict.keys():
        if k not in value_dict:
            del item_dict[k]


def _update_from_ini(source, item_dict, filename):
    """Update item_dict using data from the INI file

    Args:
        source (str): the name of source configuration, which is used to create a new ConfigItem.
        item_dict (dict): the dict to be updated.
        filename (str): the path to the INI file
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
    """Represents a configuration from a dict

    Attributes:
        value_dict (dict): a (str, str) dict containing all configurations values.
    """

    def __init__(self, name, value_dict=None, base_config=None):
        """Initialize this configuration

        Args:
            name (str): the name of this configuration
            value_dict (dict): a (str, str) dict containing all configurations values
            base_config (BaseConfig): the base configuration
        """
        BaseConfig.__init__(self, name, base_config)
        if value_dict is None:
            self.value_dict = dict()
        else:
            self.value_dict = value_dict
            self._do_reload()

    def _do_reload(self):
        item_dict = self._get_item_dict()
        _update_from_dict(self.name, item_dict, self.value_dict)
        self._set_item_dict(item_dict)


class IniFileConfig(BaseConfig):
    """Represents a configuration from an INI file
    """

    def __init__(self, filename, base_config=None):
        """Initialize this configuration

        Args:
            filename (str): the path to the INI file
            base_config (BaseConfig): the base configuration
        """
        BaseConfig.__init__(self, filename, base_config)
        self._do_reload()

    def _do_reload(self):
        item_dict = self._get_item_dict()
        _update_from_ini(self.name, item_dict, self.name)
        self._set_item_dict(item_dict)


class SystemEnvConfig(BaseConfig):
    """Represents a configuration from system environment variables
    """

    def __init__(self, base_config=None):
        """Initialize this configuration

        Args:
            base_config (BaseConfig): the base configuration
        """

        BaseConfig.__init__(self, "System Environment", base_config)
        self._do_reload()

    def _do_reload(self):
        item_dict = self._get_item_dict()
        _update_from_dict(self.name, item_dict, os.environ)
        self._set_item_dict(item_dict)
