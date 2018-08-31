import coreapi
import coreschema
from openapi_codec.encode import _get_parameters, _get_schema_type
from unittest import TestCase


def make_array_json(json_template, array_schema, location, field=None):
    if location == 'body':
        # In Swagger 2.0, arrays in the body are defined in the schema attribute
        schema = {
            'schema': array_schema
        }
        for key in schema:
            json_template[key] = schema[key]
    elif location == 'form':
        json_template['schema']['properties'][field.name] = array_schema
    else:
        # In Swagger 2.0, arrays not in the body are defined right in the field properties
        schema = array_schema
        for key in schema:
            json_template[key] = schema[key]

    return json_template


class TestArrayParameters(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.encoding = ''

        self.definitions = []
        for location in ['body', 'query']:
            field = coreapi.Field(
                name='data',
                required=True,
                location=location,
                description='Array of Anything',
                schema=coreschema.Array()
            )
            self.definitions.append(dict(
                python=field,
                json=make_array_json({
                    'name': field.name,
                    'required': field.required,
                    'in': location,
                    'description': field.description,
                }, {
                    'type': 'array',
                    'items': {},
                }, location)
            ))

            for schema_type in coreschema.__all__:
                schema = None
                native_type = None

                try:
                    schema = schema_type()
                    native_type = _get_schema_type(schema)
                except Exception:
                    pass

                if native_type is not None and (isinstance(schema_type, coreschema.String) or native_type != 'string'):
                    field = coreapi.Field(
                        name='data',
                        required=True,
                        location=location,
                        description='Array of %s' % native_type.capitalize() + 's',
                        schema=coreschema.Array(items=schema)
                    )
                    self.definitions.append(dict(
                        python=field,
                        json=make_array_json({
                            'name': field.name,
                            'required': field.required,
                            'in': location,
                            'description': field.description,
                        }, {
                            'type': 'array',
                            'items': {
                                'type': native_type,
                            }
                        }, location)
                    ))

            field = coreapi.Field(
                name='data',
                required=True,
                location=location,
                description='Array of Objects with Properties',
                schema=coreschema.Array(
                    items=coreschema.Object(
                        properties={
                            'id': coreschema.Integer(),
                        }
                    )
                )
            )

            self.definitions.append(dict(
                python=field,
                json=make_array_json({
                    'name': field.name,
                    'required': field.required,
                    'in': location,
                    'description': field.description,
                }, {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {
                                'description': '',
                                'type': 'integer'
                            },
                        },
                    }
                }, location)
            ))

    def test_expected_path_fields(self):
        for d in self.definitions:
            swagger = _get_parameters(coreapi.Link(fields=[d['python']]), encoding=self.encoding)
            self.assertEquals(swagger[0], d['json'], msg='Encoded JSON value didn\'t match for %s' % d['python'].description)


class TestArrayFormParameters(TestArrayParameters):
        def setUp(self):
            self.maxDiff = None
            self.encoding = ''
            self.definitions = []

            location = 'form'

            field = coreapi.Field(
                name='data',
                required=True,
                location=location,
                description='Array of Anything',
                schema=coreschema.Array()
            )
            self.definitions.append(dict(
                python=field,
                json=make_array_json({
                    'name': field.name,
                    'in': 'body',
                    'schema': {
                        'required': [field.name],
                        'type': 'object',
                        'properties': {},
                    },
                }, {
                    'type': 'array',
                    'description': field.description,
                    'items': {},
                }, location, field)
            ))


class TestArrayEncodedFormParameters(TestArrayParameters):
    def setUp(self):
        self.maxDiff = None
        self.encoding = 'multipart/form-data'
        self.definitions = []

        location = 'form'
        swagger_location = 'formData'

        field = coreapi.Field(
            name='data',
            required=True,
            location=location,
            description='Array of Anything',
            schema=coreschema.Array()
        )
        self.definitions.append(dict(
            python=field,
            json=make_array_json({
                'name': field.name,
                'required': field.required,
                'in': swagger_location,
                'description': field.description,
            }, {
                'type': 'array',
                'items': {},
            }, swagger_location)
        ))
