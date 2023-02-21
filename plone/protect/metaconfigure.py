from App.config import getConfiguration

from zope.interface import Interface

from plone.keyring.interfaces import IKeyManager
from plone.keyring.keymanager import KeyManager

from zope.component.zcml import handler
from pathlib import Path
import pickle

# Default
defaultKeyManagerConfig = dict(
    type=None,
    data_dir=None,
    timeout=None,
    name="default"
)


class IKeyManagerConfiguration(Interface):
    """Configuration-less directive which is intended to be used once only.

    It looks up the product configuration in zope.conf and configures global
    components accordingly.
    """


def del_timeouts(folder, timeout):
    """Delete serialized objects that have been created longer than timeout."""
    if not folder:
        return

    if not timeout:
        return

    import os
    import time
    import subprocess

    now = time.time()

    files = [os.path.join(folder, filename) for filename in os.listdir(folder)]
    for filename in files:
        if (now - os.stat(filename).st_mtime) > timeout:
            command = "rm {0}".format(filename)
            subprocess.call(command, shell=True)


def new(zope, path_to_save=None, file_to_save=None):
    """Register new utility and then serialize object to be recreated."""
    keyManager = KeyManager()

    zope.action(
        discriminator=('utility', IKeyManager, u""),
        callable=handler,
        args=('registerUtility', keyManager, IKeyManager, u""),
        kw=dict(info={}),
    )

    if path_to_save:
        serialize(keyManager, path_to_save, file_to_save)


def serialize(km, path_to_save=None, file_to_save=None):
    """Serialize object to file."""
    _path = Path(path_to_save)
    if not _path.exists():
        _path.mkdir(parents=True, exist_ok=True)

    with open(concat_path_w_name(path_to_save, file_to_save), "wb") as f:
        pickle.dump(km, f)


def deserialize(zope, path_saved):
    """Deserialize object and registers utility."""
    import os

    if os.path.exists(path_saved):
        with open(path_saved, "rb") as f:
            keyManager = pickle.load(f)

            zope.action(
                discriminator=('utility', IKeyManager, u""),
                callable=handler,
                args=('registerUtility', keyManager, IKeyManager, u""),
                kw=dict(info={}),
            )

            return True

    return None


def concat_path_w_name(path, name):
    """Check if path plus filename are formatted correctly."""
    if path[-1:] == '/':
        path = path[:-1]

    return "%s/%s" % (path, name)


def keyManagerConfiguration(_context):
    """Read configuration from zope.conf and register component accordingly."""
    cfg = getConfiguration()

    if not hasattr(cfg, 'product_config'):
        new(_context)
        return

    key_manager_config = cfg.product_config.get('keymanager', {})

    if not key_manager_config:
        new(_context)
        return

    # Set defaults for keys not set in the configuration
    key_manager_with_defaults = defaultKeyManagerConfig.copy()
    key_manager_with_defaults.update(key_manager_config)

    del_timeouts(
        folder=key_manager_with_defaults["data_dir"],
        timeout=key_manager_with_defaults["timeout"])

    #
    # Only serializes if type == file.
    #
    if key_manager_with_defaults["type"] != 'file':
        new(_context)
        return

    file_deserialized = deserialize(
        zope=_context,
        path_saved=concat_path_w_name(
            key_manager_with_defaults["data_dir"],
            key_manager_with_defaults["name"]),
    )
    if file_deserialized:
        pass
    else:
        new(
            zope=_context,
            path_to_save=key_manager_with_defaults["data_dir"],
            file_to_save=key_manager_with_defaults["name"]
        )
