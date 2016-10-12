from collections import OrderedDict

from coreapi.compat import urlparse
from openapi_codec.utils import (get_encoding, get_links_from_document,
                                 get_location, get_method)


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

    swagger['paths'] = _get_paths_object(document)

    return swagger


def _add_tag_prefix(item):
    operation_id, link, tags = item
    if tags:
        operation_id = tags[0] + '_' + operation_id
    return (operation_id, link, tags)


def _get_links(document):
    """
    Return a list of (operation_id, link, [tags])
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


def _get_paths_object(document):
    paths = OrderedDict()

    links = _get_links(document)

    for operation_id, link, tags in links:
        if link.url not in paths:
            paths[link.url] = OrderedDict()

        method = get_method(link)
        operation = _get_operation(operation_id, link, tags)
        paths[link.url].update({method: operation})

    return paths


def _get_operation(operation_id, link, tags):
    encoding = get_encoding(link)
    description = link.description.strip()
    summary = description.splitlines()[0] if description else None

    operation = {
        'operationId': operation_id,
        'responses': _get_responses(link),
        'parameters': _get_parameters(link, encoding)
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


def _get_parameters(link, encoding):
    """
    Generates Swagger Parameter Item object.
    """
    parameters = []
    properties = {}
    required = []

    for field in link.fields:
        location = get_location(link, field)
        if location == 'form':
            if encoding in ('multipart/form-data',
                            'application/x-www-form-urlencoded'):
                # 'formData' in swagger MUST be one of these media types.
                parameter = {
                    'name': field.name,
                    'required': field.required,
                    'in': 'formData',
                    'description': field.description,
                    'type': 'string'
                }
                parameters.append(parameter)
            else:
                # Expand coreapi fields with location='form' into a single swagger
                # parameter, with a schema containing multiple properties.
                schema_property = {'description': field.description}
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
                'description': field.description,
                'schema': schema
            }
            parameters.append(parameter)
        else:
            parameter = {
                'name': field.name,
                'required': field.required,
                'in': location,
                'description': field.description,
                'type': 'string'
            }
            parameters.append(parameter)

    if properties:
        parameters_dict = {
            'name': 'data',
            'in': 'body',
            'schema': {
                'type': 'object',
                'properties': properties,
            }
        }
        # Add required fields to the schema just if there are required
        # params see https://github.com/core-api/python-openapi-codec/issues/16
        if required:
            parameters_dict['schema']['required'] = required
        parameters.append(parameters_dict)

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
