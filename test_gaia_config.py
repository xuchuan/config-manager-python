import os
import tempfile
import unittest

from datetime import datetime

import collections

import test_utils
from gaia_config import ConfigItem, BaseConfig, DictConfig, IniFileConfig


class TestConfigItem(test_utils.ConcurrentTestCase):
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


class Empty:
    pass


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

    def test_bind(self):
        obj = Empty()
        self.config.bind('k1', obj, 'k1')
        self.assertEqual(obj.k1, 'v1')
        self.config._do_reload = lambda: self.dict.pop('k1', None)
        self.config.reload()
        self.assertEqual(obj.k1, 'v')

    def test_bind_different_method(self):
        obj = Empty()
        self.config.bind('x', obj, 'x', 'as_int')
        self.assertIsNone(obj.x)
        self.base_dict['x'] = '1234'
        self.config.reload()
        self.assertEqual(obj.x, 1234)

    def test_bind_set_value_failure(self):
        obj = Empty()
        self.assertRaises(ValueError, self.config.bind, 'k', obj, 'k', 'as_int')

    def test_bind_default_value(self):
        obj = Empty()
        self.config.bind('x', obj, 'x', 'as_int', 4321)
        self.assertEqual(obj.x, 4321)
        self.base_dict['x'] = '1234'
        self.config.reload()
        self.assertEqual(obj.x, 1234)
        del self.base_dict['x']
        self.config.reload()
        self.assertEqual(obj.x, 4321)

    def test_unbind(self):
        obj = Empty()
        self.config.bind('k', obj, 'k')
        self.assertEqual(obj.k, 'v')
        self.config.unbind('k')
        self.assertIsNone(obj.k)
        self.base_dict['k'] = ''
        self.config.reload()
        self.assertIsNone(obj.k)

    def test_unbind_invalid_key(self):
        self.assertRaises(KeyError, self.config.unbind, 'no_such_key')

    def test_reload(self):
        self.base_dict['kk'] = 'vv'
        self.config._do_reload = lambda: self.dict.pop('k1', None)
        self.config.reload()
        self.assertEqual(self.config['kk'], 'vv')
        self.assertEqual(self.config['k1'], 'v')

    def test_reload_update_bind(self):
        self.base_dict['kk'] = 'vv'
        self.base_dict['k1'] = 'v2'
        del self.base_dict['k']
        self.config._do_reload = lambda: self.dict.pop('k1', None) and self.dict.update(k2='vv2', k4='v4')
        obj = Empty()
        self.config.bind('k', obj, 'k')
        self.config.bind('kk', obj, 'kk')
        self.config.bind('k1', obj, 'k1')
        self.config.bind('k2', obj, 'k2')
        self.config.bind('k4', obj, 'k4')
        self.assertEqual(obj.k, 'v')
        self.assertIsNone(obj.kk)
        self.assertEqual(obj.k1, 'v1')
        self.assertEqual(obj.k2, 'v2')
        self.assertIsNone(obj.k4)
        self.config.reload()
        self.assertIsNone(obj.k)
        self.assertEqual(obj.kk, 'vv')
        self.assertEqual(obj.k1, 'v2')
        self.assertEqual(obj.k2, 'vv2')
        self.assertEqual(obj.k4, 'v4')

    def test_reload_bind_failure(self):
        obj = Empty()
        self.config.bind('u', obj, 'u', )
        self.config.bind('v', obj, 'v', )
        self.config.bind('w', obj, 'w', )
        self.config.bind('x', obj, 'x', 'as_int')
        self.config.bind('y', obj, 'y', 'as_int')
        self.config.bind('z', obj, 'z', )
        self.base_dict['u'] = 'a'
        self.base_dict['v'] = 'b'
        self.base_dict['w'] = 'c'
        self.base_dict['x'] = 'd'
        self.base_dict['y'] = 'e'
        self.base_dict['z'] = 'f'
        bind_failure = self.config.reload()
        self.assertEqual(len(bind_failure), 2)
        self.assertEqual(obj.u, 'a')
        self.assertEqual(obj.v, 'b')
        self.assertEqual(obj.w, 'c')
        self.assertIsNone(obj.x)
        self.assertIsNone(obj.y)
        self.assertEqual(obj.z, 'f')


class TestBaseConfigMultiThread(test_utils.ConcurrentTestCase):
    def test_multi_thread(self):
        base_dict = dict()
        base_config = DictConfig("base", base_dict)
        config_dict = dict()
        config = BaseConfig("test", base_config, config_dict)

        max_tasks = 100
        max_rounds_per_task = 10
        max_variables = 30

        def create_task(task_id):
            def run():
                obj = Empty()
                key_prefix = 'key%d_' % task_id
                for i in range(0, max_rounds_per_task):
                    for j in range(0, max_variables):
                        if i > 0:
                            key = '%s%d' % (key_prefix, i - 1 + j)
                            config.unbind(key)
                            del config_dict[key]
                    for j in range(0, max_variables):
                        key = '%s%d' % (key_prefix, i + j)
                        config.bind(key, obj, key)
                        config_dict[key] = key
                    config.reload()
                    for j in range(0, max_variables):
                        key = '%s%d' % (key_prefix, i + j)
                        self.assertEqual(getattr(obj, key), key)

            return run

        self.assertConcurrent('multi', [create_task(i) for i in range(1, max_tasks + 1)], 30)


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
