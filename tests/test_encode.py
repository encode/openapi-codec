import coreapi
import coreschema

from collections import OrderedDict
from openapi_codec.encode import generate_swagger_object, _get_parameters, _get_definitions
from unittest import TestCase


class TestBasicInfo(TestCase):
    def setUp(self):
        self.document = coreapi.Document(title='Example API', url='https://www.example.com/')
        self.swagger = generate_swagger_object(self.document)

    def test_info(self):
        self.assertIn('info', self.swagger)
        expected = {
            'title': self.document.title,
            'version': ''
        }
        self.assertEquals(self.swagger['info'], expected)

    def test_swagger_version(self):
        self.assertIn('swagger', self.swagger)
        expected = '2.0'
        self.assertEquals(self.swagger['swagger'], expected)

    def test_host(self):
        self.assertIn('host', self.swagger)
        expected = 'www.example.com'
        self.assertEquals(self.swagger['host'], expected)

    def test_schemes(self):
        self.assertIn('schemes', self.swagger)
        expected = ['https']
        self.assertEquals(self.swagger['schemes'], expected)

    def test_definitions(self):
        self.assertIn('definitions', self.swagger)
        expected = dict()
        self.assertEquals(self.swagger['definitions'], expected)


class TestPaths(TestCase):
    def setUp(self):
        self.path = '/users/'
        self.document = coreapi.Document(
            content={
                'users': {
                    'create': coreapi.Link(
                        action='post',
                        url=self.path
                    ),
                    'list': coreapi.Link(
                        action='get',
                        url=self.path
                    )
                }
            }
        )
        self.swagger = generate_swagger_object(self.document)

    def test_paths(self):
        self.assertIn('paths', self.swagger)
        self.assertIn(self.path, self.swagger['paths'])
        self.assertIn('get', self.swagger['paths'][self.path])
        self.assertIn('post', self.swagger['paths'][self.path])
        expected = {
            'responses': {
                '200': {
                    'description': ''
                }
            },
            'parameters': [],
            'operationId': 'list',
            'tags': ['users']
        }
        self.assertEquals(self.swagger['paths'][self.path]['get'], expected)
        expected = {
            'responses': {
                '201': {
                    'description': ''
                }
            },
            'parameters': [],
            'operationId': 'create',
            'tags': ['users']
        }
        self.assertEquals(self.swagger['paths'][self.path]['post'], expected)


class TestParameters(TestCase):
    def setUp(self):
        self.field = coreapi.Field(
            name='email',
            required=True,
            location='query',
            schema=coreschema.String(description='A valid email address.')
        )
        self.swagger = _get_parameters(coreapi.Link(fields=[self.field]), encoding='')

    def test_expected_fields(self):
        self.assertEquals(len(self.swagger), 1)
        expected = {
            'name': self.field.name,
            'required': self.field.required,
            'in': 'query',
            'description': self.field.schema.description,
            'type': 'string'  # Everything is a string for now.
        }
        self.assertEquals(self.swagger[0], expected)


class TestDefinitions(TestCase):

    def setUp(self):

        obj_props = OrderedDict()
        obj_props['foo'] = coreschema.String()
        obj_props['bar'] = coreschema.Integer()

        self.object_field = coreapi.Field(
            name='dummy_object',
            required=True,
            location='form',
            schema=coreschema.Object(
                properties=obj_props
            )
        )

        self.array_field = coreapi.Field(
            name='dummy_array',
            location='form',
            schema=coreschema.Array(
                items=self.object_field
            )
        )

        self.link = coreapi.Link(
            action='post',
            url='/users/',
            fields=[self.object_field, self.array_field]
        )

        self.document = coreapi.Document(
            content={
                'users': {
                    'create': self.link,
                }
            }
        )

        self.definitions = _get_definitions(self.document)
        self.parameters = _get_parameters(self.link, '')
        self.swagger = generate_swagger_object(self.document)

    def test_basic_definitions(self):

        print self.definitions

        self.assertIn('definitions', self.swagger)
        self.assertIn('dummy_object', self.definitions)
        self.assertIn('dummy_array_item', self.definitions)

        expected_dummy_object_def = {
            'type': 'object',
            'properties': {
                'foo': {'type': 'string', 'description': ''},
                'bar': {'type': 'integer', 'description': ''}
            }
        }

        self.assertEqual(self.definitions.get('dummy_object'), expected_dummy_object_def)
        self.assertEqual(self.definitions.get('dummy_array_item'), expected_dummy_object_def)

        expected_dummy_parameters = [{
            'schema': {
                'required': ['dummy_object'],
                'type': 'object',
                'properties': {
                    'dummy_array': {
                        'items': {
                            '$ref': '#/definitions/dummy_array_item'
                        },
                        'type': 'array',
                        'description': ''
                    },
                    'dummy_object': {
                        '$ref': '#/definitions/dummy_object'
                    }
                }
            },
            'name': 'data',
            'in': 'body'
        }]
        self.assertEqual(self.parameters, expected_dummy_parameters)
