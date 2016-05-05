"""Compatibility module"""

import os
import re
import warnings
from . import plugin, lib
from .vendor import six

# Aliases
Selector = plugin.Collector
Conformer = plugin.Integrator

_filename_ascii_strip_re = re.compile(r'[^-\w.]')
_windows_device_files = ('CON', 'AUX', 'COM1', 'COM2', 'COM3', 'COM4',
                         'LPT1', 'LPT2', 'LPT3', 'PRN', 'NUL')


def sort(*args, **kwargs):
    warnings.warn("pyblish.api.sort has been deprecated; "
                  "use pyblish.api.sort_plugins")
    return plugin.sort(*args, **kwargs)


def deregister_all(*args, **kwargs):
    warnings.warn("pyblish.api.deregister_all has been deprecated; "
                  "use pyblish.api.deregister_all_paths")
    return plugin.deregister_all_paths(*args, **kwargs)


# AbstractEntity
#
# The below members represent backwards compatibility
# features, kept separate for maintainability as they
# will no longer be updated and eventually discarded.


@lib.deprecated
def set_data(self, key, value):
    """DEPRECATED - USE .data DICTIONARY DIRECTLY

    Modify/insert data into entity

    Arguments:
        key (str): Name of data to add
        value (object): Value of data to add

    """

    self.data[key] = value


@lib.deprecated
def remove_data(self, key):
    """DEPRECATED - USE .data DICTIONARY DIRECTLY

    Remove data from entity

    Arguments;
        key (str): Name of data to remove

    """

    self.data.pop(key)


@lib.deprecated
def has_data(self, key):
    """DEPRECATED - USE .data DICTIONARY DIRECTLY

    Check if entity has key

    Arguments:
        key (str): Key to check

    Return:
        True if it exists, False otherwise

    """

    return key in self.data


@lib.deprecated
def add(self, other):
    """DEPRECATED - USE .append

    Add member to self

    This is to mimic the interface of set()

    """

    return self.append(other)


@lib.deprecated
def remove(self, other):
    """DEPRECATED - USE .pop

    Remove member from self

    This is to mimic the interface of set()

    """

    index = self.index(other)
    return self.pop(index)


plugin.AbstractEntity.add = add
plugin.AbstractEntity.remove = remove
plugin.AbstractEntity.set_data = set_data
plugin.AbstractEntity.remove_data = remove_data
plugin.AbstractEntity.has_data = has_data


# Context

@lib.deprecated
def create_asset(self, *args, **kwargs):
    return self.create_instance(*args, **kwargs)


@lib.deprecated
def add(self, other):
    return super(plugin.Context, self).append(other)


plugin.Context.create_asset = create_asset
plugin.Context.add = add

if six.PY3:
    @lib.deprecated
    def format_filename(filename):
        pass


    @lib.deprecated
    def format_filename2(filename):
        pass

else:
    def format_filename(filename):
        """Convert arbitrary string to valid filename, django-style.
    
        Modified from django.utils.text.get_valid_filename()
    
        Returns the given string converted to a string that can be used for a clean
        filename. Specifically, leading and trailing spaces are removed; other
        spaces are converted to underscores; and anything that is not a unicode
        alphanumeric, dash, underscore, or dot, is removed.
    
        Usage:
            >> format_filename("john's portrait in 2004.jpg")
            'johns_portrait_in_2004.jpg'
            >> format_filename("something^_SD.dda.//fd/ad.exe")
            'something_SD.dda.fdad.exe'
            >> format_filename("Napoleon_:namespaces_GRP|group1_GRP")
            'Napoleon_namespaces_GRPgroup1_GRP'
    
        """
    
        filename = filename.strip().replace(' ', '_')
    
        # on nt a couple of special files are present in each folder.  We
        # have to ensure that the target file is not such a filename.  In
        # this case we prepend an underline
        if os.name == 'nt' and filename and \
           filename.split('.')[0].upper() in _windows_device_files:
            filename = '_' + filename
    
        return re.sub(r'(?u)[^-\w.]', '', filename)
    
    
    def format_filename2(filename):
        """Convert arbitrary string to valid filename, werkzeug-style.
    
        Modified from werkzeug.utils.secure_filename()
    
        Pass it a filename and it will return a secure version of it.  This
        filename can then safely be stored on a regular file system and passed
        to :func:`os.path.join`. The filename returned is an ASCII only string
        for maximum portability.
    
        On windows system the function also makes sure that the file is not
        named after one of the special device files.
    
        Arguments:
            filename (str): the filename to secure
    
        Usage:
            >> format_filename2("john's portrait in 2004.jpg")
            'johns_portrait_in_2004.jpg'
            >> format_filename2("something^_SD.dda.//fd/ad.exe")
            'something_SD.dda._fd_ad.exe'
            >> format_filename2("Napoleon_:namespaces_GRP|group1_GRP")
            'Napoleon_namespaces_GRPgroup1_GRP'
    
        .. warning:: The function might return an empty filename.  It's your
            responsibility to ensure that the filename is unique and that you
            generate random filename if the function returned an empty one.
    
        .. versionadded:: 1.0.9
    
        """
    
        if isinstance(filename, six.text_type):
            from unicodedata import normalize
            filename = normalize('NFKD', filename).encode('ascii', 'ignore')
    
        for sep in os.path.sep, os.path.altsep:
            if sep:
                filename = filename.replace(sep, ' ')
        filename = str(_filename_ascii_strip_re.sub('', '_'.join(
                       filename.split()))).strip('._')
    
        # on nt a couple of special files are present in each folder.  We
        # have to ensure that the target file is not such a filename.  In
        # this case we prepend an underline
        if os.name == 'nt' and filename and \
           filename.split('.')[0].upper() in _windows_device_files:
            filename = '_' + filename
    
        return filename


lib.format_filename = format_filename
lib.format_filename2 = format_filename2
