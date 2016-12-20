# GaiaConfig

# Usage
```python
from gaia_config import DictConfig, IniFileConfig, SystemEnvConfig

# Read from system environments
config = SystemEnvConfig()

# Read from config file
config = IniFileConfig('my.conf')

# Read from dict
d = {'a': '0', 'b': '1'}
config = DictConfig('memory', d)

# Update and reload
d['a'] = '1'
config.reload()

# A typical composite Config
config = DictConfig('hotfix', base_config=IniFileConfig('conf.prop', SystemEnvConfig()))

# Reload the Config when something has changed
config.reload()

# Get a snapshot first so that properties are not updated between read operations.
config = config.copy()
prop = config['prop1']
int_prop = config['intProp'].as_int()
```