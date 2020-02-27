import logging
import json

try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config

from ckan.lib import base
from ckan.plugins import toolkit
from ckan.plugins.toolkit import abort, ObjectNotFound, ValidationError
from ckan import model, logic
from ckan.common import c, _, request, response
from ckanext.dataexplorer.lib import FileWriterService

log = logging.getLogger(__name__)

DUMP_FORMATS = 'csv', 'xlsx', 'json', 'xml'

class DataExplorer(base.BaseController):

    ctrl = 'ckanext.dataexplorer.controllers.dataexplorer:DataExplorer'

    def _get_ctx(self):
        return {
            'model': model, 'session': model.Session,
            'user': c.user,
            'auth_user_obj': c.userobj,
            'for_view': True
        }

    def _get_action(self, action, data_dict):
        return toolkit.get_action(action)(self._get_ctx(), data_dict)

    def extract(self):

        writer = FileWriterService()
        columns = []

        if request.method == 'POST':
            data_dict = dict(request.POST)
            data = json.loads(data_dict['extract_data'])
            data['limit'] = config.get('ckanext.dataexplorer.extract_rows_limit', 30000)
            format = data.pop('format')

            resource_meta = self._get_action('resource_show', {'id': data['resource_id']})
            name =  resource_meta.get('name', "extract").replace(' ', '_')

            try:
                import ckanext.nhs.action as nhs_action
                resource_data = self._get_action('nhs_action.datastore_search', data)

                for key in resource_data['fields']:
                    columns.append(key['id'])

                try:
                    columns.remove('_id')
                except ValueError:
                    pass
                try:
                    columns.remove('_full_count')
                except ValueError:
                    pass
                try:
                    columns.remove('rank')
                except ValueError:
                    pass

            except ObjectNotFound:
                abort(404, _('DataStore resource not found'))

            try:
                writer.write_to_file(columns,
                                     resource_data.get('records'),
                                     format,
                                     response,
                                     name)
            except ValidationError:
                abort(400, _(
                    u'Format: must be one of %s') % u', '.join(DUMP_FORMATS))



