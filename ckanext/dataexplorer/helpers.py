# -*- coding: utf-8 -

try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config


import logging
import json
from datetime import date, timedelta, datetime
from decimal import Decimal
import ckan.lib.helpers as ckan_helpers

log = logging.getLogger(__name__)

NAIVE_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATE_FORMAT = '%Y-%m-%d'


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return json.JSONEncoder.default(self, obj)
        except TypeError:
            if type(obj) is date:
                return obj.strftime(DATE_FORMAT)

            if type(obj) is datetime:
                return obj.strftime(NAIVE_DATETIME_FORMAT)

            if type(obj) is timedelta:
                # return it as rounded milliseconds
                return int(obj.total_seconds() * 1000)

            if type(obj) is Decimal:
                return str(obj)

            raise

def _get_logic_functions(module_root, logic_functions={}):
    '''Helper function that scans extension logic dir for all logic functions.'''
    for module_name in ['create', 'delete', 'get', 'patch', 'update']:
        module_path = '%s.%s' % (module_root, module_name,)

        module = __import__(module_path)

        for part in module_path.split('.')[1:]:
            module = getattr(module, part)

        for key, value in module.__dict__.items():
            if not key.startswith('_') and (hasattr(value, '__call__')
                                            and (value.__module__ == module_path)):
                logic_functions[key] = value

    return logic_functions


def dataexplorer_resource_view_get_fields(resource):
    '''Returns sorted list of text and time fields of a resource
    from a configuration file.'''

    if not resource.get('datastore_active'):
        return []

    fields =  config.get('ckanext.dataexplorer.fields', '').split()

    if fields is '':
        ckan_helpers.resource_view_get_fields(resource)
    else:
        return sorted(fields)