import coreapi
import coreschema
from openapi_codec.encode import generate_swagger_object, _get_parameters
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
