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
        self.swagger = _get_parameters(coreapi.Link(fields=[self.field]), encoding='', definitions=OrderedDict())

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

        # Clashing name
        self.clashing_name = 'author'

        # Schema objects
        name_schema_obj = coreschema.schemas.Object(
            properties=OrderedDict({'name': coreschema.schemas.String(description='name')})
        )
        bday_schema_obj = coreschema.schemas.Object(
            properties=OrderedDict({'birthday': coreschema.schemas.String(description='birthday')})
        )

        # Fields
        author_field = coreapi.Field(
            name='author',
            required=True,
            location='form',
            schema=name_schema_obj
        )
        clashing_author_field = coreapi.Field(
            name='author',
            required=True,
            location='form',
            schema=bday_schema_obj
        )
        co_authoors_field = coreapi.Field(
            name='co_authoors',
            required=True,
            location='form',
            schema=coreschema.schemas.Array(
                items=bday_schema_obj
            )
        )

        # Link objects
        v1_songs_link = coreapi.Link(
            url='/api/v1/songs/',
            action=u'post',
            encoding=u'application/json',
            fields=[author_field],
        )
        v2_songs_link = coreapi.Link(
            url='/api/v2/songs/',
            action=u'post',
            encoding=u'application/json',
            fields=[clashing_author_field, co_authoors_field],
        )

        self.links = OrderedDict({
            'v1': OrderedDict({'list': v1_songs_link}),
            'v2': OrderedDict({'list': v2_songs_link})
        })

        # Coreapi document object
        self.document = coreapi.Document(
            'test api',
            content=self.links
        )

        # Init definitions and swagger object
        self.definitions = _get_definitions(self.document)
        self.swagger = generate_swagger_object(self.document)

    def test_clashing_names(self):

        # Basic checks
        self.assertIn('definitions', self.swagger)
        self.assertEqual(len(self.swagger['definitions'].keys()), 2, 'Unexpected definitions count')

        # Check nothing unexpected is in definitions
        defs = filter(
            lambda d: d.startswith('{}_def_item'.format(self.clashing_name)), self.swagger['definitions'].keys()
        )
        self.assertEqual(len(defs), 2, 'Unexpected definitions count')