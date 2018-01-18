import random
import string
import coreschema

from collections import OrderedDict
from coreapi.document import Field
from coreapi.compat import urlparse
from openapi_codec.utils import get_method, get_encoding, get_location, get_links_from_document


def generate_swagger_object(document):
    """
    Generates root of the Swagger spec.
    """
    parsed_url = urlparse.urlparse(document.url)

    swagger = OrderedDict()

    swagger['swagger'] = '2.0'
    swagger['info'] = OrderedDict()
    swagger['info']['title'] = document.title
    swagger['info']['version'] = ''  # Required by the spec

    if parsed_url.netloc:
        swagger['host'] = parsed_url.netloc
    if parsed_url.scheme:
        swagger['schemes'] = [parsed_url.scheme]

    if not parsed_url.netloc and not parsed_url.scheme:
        swagger['host'] = document.url

    swagger['definitions'] = _get_definitions(document)
    swagger['paths'] = _get_paths_object(document, swagger['definitions'])

    return swagger


def _get_or_update_definitions(update_def_data, update_def_name, definitions):
    """
    Updates definitions with provided data If definition is not present in map, returns found definition
    data in case definition overlaps with existing one.
    """

    # Check if there's existing definition with same name or props
    clashing_def_names = filter(
        lambda d: d.startswith(update_def_name) or definitions.get(d) == update_def_data,
        definitions.keys()
    )

    for clashing_def_name in clashing_def_names:
        clash_def_data = definitions.get(clashing_def_name)
        if clash_def_data == update_def_data:
            return clash_def_data
    else:
        if clashing_def_names:
            rand_part = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(5)])
            update_def_name = '{}_{}'.format(update_def_name, rand_part)
        definitions[update_def_name] = update_def_data
        return update_def_data


def _get_field_definition_data(field_item, defs):
    """
    Returns dictionary with field definition data.
    """
    definition_data = {
        'type': 'object',
        'properties': {}
    }

    if isinstance(field_item, coreschema.Object):
        props = field_item.properties
    elif isinstance(field_item.schema, coreschema.schemas.Array):
        props = field_item.schema.items.properties
    else:
        try:
            props = field_item.schema.properties
        except AttributeError:
            props = OrderedDict()

    for f_name, f_schema in iter(props.items()):

        if _get_field_type(f_schema) is 'object':
            def_data = _get_or_update_definitions(
                _get_field_definition_data(f_schema, defs),
                '{}_def_item'.format(f_schema.name),
                defs
            )
            if def_data:
                return def_data
        else:
            definition_data['properties'][f_name] = {
                'type': _get_field_type(f_schema),
                'description': ''
            }

    return definition_data


def _get_definitions(document):
    """
    Returns dictionary with schema definitions.
    """

    definitions = OrderedDict()
    links = _get_links(document)

    for _, link, _ in links:
        for field in link.fields:
            field_type = _get_field_type(field)

            # Get field definition data
            if field_type == 'array':
                def_data = _get_field_definition_data(field.schema.items, definitions)
            else:
                def_data = _get_field_definition_data(field, definitions)

            _get_or_update_definitions(
                def_data,
                '{}_def_item'.format(field.name),
                definitions
            )

    return definitions


def _add_tag_prefix(item):
    """
    Returns tuple (operation_id, link, tags) with modified operation_id in case of tags.
    """

    operation_id, link, tags = item
    if tags:
        operation_id = tags[0] + '_' + operation_id
    return operation_id, link, tags


def _get_links(document):
    """
    Return a list of (operation_id, link, [tags]).
    """
    # Extract all the links from the first or second level of the document.
    links = []
    for keys, link in get_links_from_document(document):
        if len(keys) > 1:
            operation_id = '_'.join(keys[1:])
            tags = [keys[0]]
        else:
            operation_id = keys[0]
            tags = []
        links.append((operation_id, link, tags))

    # Determine if the operation ids each have unique names or not.
    operation_ids = [item[0] for item in links]
    unique = len(set(operation_ids)) == len(links)

    # If the operation ids are not unique, then prefix them with the tag.
    if not unique:
        return [_add_tag_prefix(item) for item in links]

    return links


def _get_paths_object(document, definitions):
    """
    Returns dictionary with document paths.
    """
    paths = OrderedDict()

    links = _get_links(document)

    for operation_id, link, tags in links:
        if link.url not in paths:
            paths[link.url] = OrderedDict()

        method = get_method(link)
        operation = _get_operation(operation_id, link, tags, definitions)
        paths[link.url].update({method: operation})

    return paths


def _get_operation(operation_id, link, tags, definitions):
    """
    Returns dictionary with operation parameters.
    """

    encoding = get_encoding(link)
    description = link.description.strip()
    summary = description.splitlines()[0] if description else None

    operation = {
        'operationId': operation_id,
        'responses': _get_responses(link),
        'parameters': _get_parameters(link, encoding, definitions)
    }

    if description:
        operation['description'] = description
    if summary:
        operation['summary'] = summary
    if encoding:
        operation['consumes'] = [encoding]
    if tags:
        operation['tags'] = tags
    return operation


def _get_field_description(field):
    """
    Returns field description.
    """

    if getattr(field, 'description', None) is not None:
        # Deprecated
        return field.description

    if field.schema is None:
        return ''

    return field.schema.description


def _get_field_type(field):
    """
    Returns field string type by the given field schema.
    """
    if getattr(field, 'type', None) is not None:
        # Deprecated
        return field.type

    if isinstance(field, Field):
        cls = field.schema.__class__
    else:
        cls = field.__class__

    return {
        coreschema.String: 'string',
        coreschema.Integer: 'integer',
        coreschema.Number: 'number',
        coreschema.Boolean: 'boolean',
        coreschema.Array: 'array',
        coreschema.Object: 'object',
    }.get(cls, 'string')


def _get_parameters(link, encoding, definitions):
    """
    Generates Swagger Parameter Item object.
    """
    parameters = []
    properties = {}
    required = []

    for field in link.fields:
        location = get_location(link, field)
        field_description = _get_field_description(field)
        field_type = _get_field_type(field)
        if location == 'form':
            if encoding in ('multipart/form-data', 'application/x-www-form-urlencoded'):
                # 'formData' in swagger MUST be one of these media types.
                parameter = {
                    'name': field.name,
                    'required': field.required,
                    'in': 'formData',
                    'description': field_description,
                    'type': field_type,
                }
                if field_type == 'array':
                    parameter['items'] = {'type': 'string'}
                parameters.append(parameter)
            else:
                # Expand coreapi fields with location='form' into a single swagger
                # parameter, with a schema containing multiple properties.

                schema_property = {
                    'description': field_description,
                    'type': field_type,
                }

                if field_type in ('object', 'array'):
                    definition_data = _get_field_definition_data(field, definitions)

                    definition_data = definition_data.get('properties')
                    defs = filter(lambda d: definitions.get(d).get('properties') == definition_data, definitions)

                    if defs:
                        # Note: Python2.X <-> Python3.X
                        try:
                            def_name = defs[0]
                        except TypeError:
                            def_name = next(defs)

                        schema_property = {'$ref': '#/definitions/{}'.format(def_name)}
                        if field_type == 'array':
                            schema_property.pop('$ref')
                            schema_property['type'] = 'array'
                            schema_property['items'] = {
                                '$ref': '#/definitions/{}'.format(def_name)
                            }

                properties[field.name] = schema_property
                if field.required:
                    required.append(field.name)
        elif location == 'body':
            if encoding == 'application/octet-stream':
                # https://github.com/OAI/OpenAPI-Specification/issues/50#issuecomment-112063782
                schema = {'type': 'string', 'format': 'binary'}
            else:
                schema = {}
            parameter = {
                'name': field.name,
                'required': field.required,
                'in': location,
                'description': field_description,
                'schema': schema
            }
            parameters.append(parameter)
        else:
            parameter = {
                'name': field.name,
                'required': field.required,
                'in': location,
                'description': field_description,
                'type': field_type or 'string',
            }
            if field_type == 'array':
                parameter['items'] = {'type': 'string'}
            parameters.append(parameter)

    if properties:
        parameter = {
            'name': 'data',
            'in': 'body',
            'schema': {
                'type': 'object',
                'properties': properties
            }
        }
        if required:
            parameter['schema']['required'] = required
        parameters.append(parameter)

    return parameters


def _get_responses(link):
    """
    Returns minimally acceptable responses object based
    on action / method type.
    """
    template = {'description': ''}
    if link.action.lower() == 'post':
        return {'201': template}
    if link.action.lower() == 'delete':
        return {'204': template}
    return {'200': template}
