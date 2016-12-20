import os
import tempfile
import unittest

from datetime import datetime

import collections

from gaia_config import ConfigItem, BaseConfig, DictConfig, IniFileConfig


class TestConfigItem(unittest.TestCase):
    def test___new__(self):
        now = datetime.now()
        config_item = ConfigItem("k", "v", "s", now)
        self.assertEqual(config_item.key, "k")
        self.assertEqual(config_item, "v")
        self.assertEqual(config_item.source, "s")
        self.assertEqual(config_item.last_update_time, now)

    def test___new___strip_arguments(self):
        now = datetime.now()
        config_item = ConfigItem(" \t\r\nk \t\r\n", " \t\r\nv \t\r\n", " \t\r\ns \t\r\n", now)
        self.assertEqual(config_item.key, "k")
        self.assertEqual(config_item, "v")
        self.assertEqual(config_item.source, "s")
        self.assertEqual(config_item.last_update_time, now)

    def test_as_int(self):
        config_item = ConfigItem("k", "1234", "s", datetime.now())
        self.assertEqual(config_item.as_int(), 1234)

    def test_as_int_invalid(self):
        config_item = ConfigItem("k", "v", "s", datetime.now())
        self.assertRaises(ValueError, config_item.as_int)

    def test_as_float(self):
        config_item = ConfigItem("k", "0.1", "s", datetime.now())
        self.assertEqual(config_item.as_float(), 0.1)

    def test_as_float_invalid(self):
        config_item = ConfigItem("k", "v", "s", datetime.now())
        self.assertRaises(ValueError, config_item.as_float)

    def test_as_str_list(self):
        config_item = ConfigItem("k", "a0,b1,c2", "s", datetime.now())
        self.assertEqual(config_item.as_str_list(), ['a0', 'b1', 'c2'])

    def test_as_str_list_single(self):
        config_item = ConfigItem("k", "v", "s", datetime.now())
        self.assertEqual(config_item.as_str_list(), ['v'])

    def test_as_str_list_empty(self):
        config_item = ConfigItem("k", "", "s", datetime.now())
        self.assertEqual(config_item.as_str_list(), [])

    def test_as_int_list(self):
        config_item = ConfigItem("k", "0,1,2,3,4", "s", datetime.now())
        self.assertEqual(config_item.as_int_list(), [0, 1, 2, 3, 4])

    def test_as_int_list_single(self):
        config_item = ConfigItem("k", "0", "s", datetime.now())
        self.assertEqual(config_item.as_int_list(), [0])

    def test_as_int_list_empty(self):
        config_item = ConfigItem("k", "", "s", datetime.now())
        self.assertEqual(config_item.as_int_list(), [])

    def test_as_float_list(self):
        config_item = ConfigItem("k", "0.1,1.2,2.3,3.4,4.5", "s", datetime.now())
        self.assertEqual(config_item.as_float_list(), [0.1, 1.2, 2.3, 3.4, 4.5])

    def test_as_float_list_single(self):
        config_item = ConfigItem("k", "0.1", "s", datetime.now())
        self.assertEqual(config_item.as_float_list(), [0.1])

    def test_as_float_list_empty(self):
        config_item = ConfigItem("k", "", "s", datetime.now())
        self.assertEqual(config_item.as_float_list(), [])


class TestBaseConfig(unittest.TestCase):
    def setUp(self):
        self.base_dict = {'k': 'v', 'k1': 'v'}
        self.base_config = DictConfig("base", self.base_dict)
        self.dict = {'k1': 'v1', 'k2': 'v2', 'k3': 'v3'}
        self.config = BaseConfig("test", self.base_config, self.dict)

    def test___init__(self):
        self.config = BaseConfig("test", self.base_config)
        self.assertEqual(self.config.name, "test")
        self.assertEqual(self.config.base_config, self.base_config)
        self.assertEqual(self.config._BaseConfig__item_dict, dict())

    def test___init___with_item_dict(self):
        self.assertEqual(self.config.name, "test")
        self.assertEqual(self.config.base_config, self.base_config)
        self.assertEqual(self.config._BaseConfig__item_dict, self.dict)

    def test___getitem__(self):
        self.assertEqual(self.config['k'], "v")
        self.assertEqual(self.config['k1'], "v1")
        self.assertEqual(self.config['k2'], "v2")
        self.assertEqual(self.config['k3'], "v3")

    def test___getitem___without_base_config(self):
        self.config = BaseConfig("test", None, self.dict)
        self.assertRaises(KeyError, self.config.__getitem__, 'k')
        self.assertEqual(self.config['k1'], "v1")
        self.assertEqual(self.config['k2'], "v2")
        self.assertEqual(self.config['k3'], "v3")

    def test_keys(self):
        self.assertEqual(collections.Counter(self.config.keys()), collections.Counter(['k', 'k1', 'k2', 'k3']))

    def test_keys_without_base_config(self):
        self.config = BaseConfig("test", None, self.dict)
        self.assertEqual(collections.Counter(self.config.keys()), collections.Counter(['k1', 'k2', 'k3']))

    def test_items(self):
        self.assertEqual(collections.Counter(self.config.items()),
                         collections.Counter([('k', 'v'), ('k1', 'v1'), ('k2', 'v2'), ('k3', 'v3')]))

    def test_items_without_base_config(self):
        self.config = BaseConfig("test", None, self.dict)
        self.assertEqual(collections.Counter(self.config.items()),
                         collections.Counter([('k1', 'v1'), ('k2', 'v2'), ('k3', 'v3')]))

    def test_copy(self):
        config = self.config.copy()
        self.assertEqual(self.config.name, config.name)
        self.assertNotEqual(self.base_config, config.base_config)
        self.assertEqual(self.dict, config._BaseConfig__item_dict)
        self.assertEqual('base', config.base_config.name)
        self.assertIsNone(config.base_config.base_config)
        self.assertEqual(self.base_dict, config.base_config._BaseConfig__item_dict)


class TestDictConfig(unittest.TestCase):
    def setUp(self):
        self.dict = {'k': 'v'}
        self.config = DictConfig('test', self.dict)

    def test___init__(self):
        self.assertEqual('test', self.config.name)
        self.assertIsNone(self.config.base_config)
        self.assertEqual(self.dict, self.config.value_dict)
        self.assertEqual('v', self.config['k'])

    def test___init__with_base_config(self):
        config = BaseConfig('base', None)
        self.config = DictConfig('test', self.dict, config)
        self.assertEqual('test', self.config.name)
        self.assertEqual(config, self.config.base_config)
        self.assertEqual(self.dict, self.config.value_dict)
        self.assertEqual('v', self.config['k'])

    def test_reload(self):
        del self.dict['k']
        self.dict['x'] = 'y'
        self.config.reload()
        self.assertRaises(KeyError, self.config.__getitem__, 'k')
        self.assertEqual('y', self.config['x'])


class TestIniFileConfig(unittest.TestCase):
    def setUp(self):
        fd, self.filename = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write('''
[DEFAULT]
x = y
[sec1]
a = 0
b = 1
[sec2]
c = 3
d = 4
            ''')
        self.config = IniFileConfig(self.filename)

    def tearDown(self):
        os.remove(self.filename)

    def test___init__(self):
        self.assertEqual(self.filename, self.config.name)
        self.assertIsNone(self.config.base_config)
        self.assertEqual(collections.Counter(self.config.items()),
                         collections.Counter(
                             [('sec1.x', 'y'), ('sec1.a', '0'), ('sec1.b', '1'),
                              ('sec2.x', 'y'), ('sec2.c', '3'), ('sec2.d', '4')]))

    def test___init__with_base_config(self):
        config = BaseConfig('base', None)
        self.config = IniFileConfig(self.filename, config)
        self.assertEqual(self.filename, self.config.name)
        self.assertEqual(config, self.config.base_config)
        self.assertEqual(collections.Counter(self.config.items()),
                         collections.Counter(
                             [('sec1.x', 'y'), ('sec1.a', '0'), ('sec1.b', '1'), ('sec2.x', 'y'), ('sec2.c', '3'),
                              ('sec2.d', '4')]))

    def test_reload(self):
        with open(self.filename, 'w') as f:
            f.write('''
[DEFAULT]
x=y
[sec1]
a=0
[sec2]
c=3
            ''')
        self.config.reload()
        self.assertRaises(KeyError, self.config.__getitem__, 'k')
        self.assertEqual(collections.Counter(self.config.items()),
                         collections.Counter([('sec1.x', 'y'), ('sec1.a', '0'), ('sec2.x', 'y'), ('sec2.c', '3')]))


if __name__ == '__main__':
    unittest.main()
