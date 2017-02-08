from openapi_codec import OpenAPICodec
import coreapi
import coreschema


codec = OpenAPICodec()
doc = coreapi.Document(
    url='https://api.example.com/',
    title='Example API',
    content={
        'simple_link': coreapi.Link('/simple_link/', description='example link'),
        'location': {
            'query': coreapi.Link('/location/query/', fields=[
                coreapi.Field(name='a', required=True, schema=coreschema.String(description='example field')),
                coreapi.Field(name='b')
            ]),
            'form': coreapi.Link('/location/form/', action='post', fields=[
                coreapi.Field(name='a', required=True, schema=coreschema.String(description='example field')),
                coreapi.Field(name='b'),
            ]),
            'body': coreapi.Link('/location/body/', action='post', fields=[
                coreapi.Field(name='example', location='body')
            ]),
            'path': coreapi.Link('/location/path/{id}/', fields=[
                coreapi.Field(name='id', location='path', required=True)
            ])
        },
        'encoding': {
            'multipart': coreapi.Link('/encoding/multipart/', action='post', encoding='multipart/form-data', fields=[
                coreapi.Field(name='a', required=True),
                coreapi.Field(name='b')
            ]),
            'multipart-body': coreapi.Link('/encoding/multipart-body/', action='post', encoding='multipart/form-data', fields=[
                coreapi.Field(name='example', location='body')
            ]),
            'urlencoded': coreapi.Link('/encoding/urlencoded/', action='post', encoding='application/x-www-form-urlencoded', fields=[
                coreapi.Field(name='a', required=True),
                coreapi.Field(name='b')
            ]),
            'urlencoded-body': coreapi.Link('/encoding/urlencoded-body/', action='post', encoding='application/x-www-form-urlencoded', fields=[
                coreapi.Field(name='example', location='body')
            ]),
            'upload': coreapi.Link('/encoding/upload/', action='post', encoding='application/octet-stream', fields=[
                coreapi.Field(name='example', location='body', required=True)
            ]),
        }
    }
)


def test_mapping():
    """
    Ensure that a document that is encoded into OpenAPI and then decoded
    comes back as expected.
    """
    content = codec.dump(doc)
    new = codec.load(content)
    assert new.title == 'Example API'

    assert new['simple_link'] == coreapi.Link(
        url='https://api.example.com/simple_link/',
        action='get',
        description='example link'
    )

    assert new['location']['query'] == coreapi.Link(
        url='https://api.example.com/location/query/',
        action='get',
        fields=[
            coreapi.Field(
                name='a',
                location='query',
                schema=coreschema.String(description='example field'),
                required=True
            ),
            coreapi.Field(
                name='b',
                location='query',
                schema=coreschema.String()
            )
        ]
    )

    assert new['location']['path'] == coreapi.Link(
        url='https://api.example.com/location/path/{id}/',
        action='get',
        fields=[
            coreapi.Field(
                name='id',
                location='path',
                required=True,
                schema=coreschema.String()
            )
        ]
    )

    assert new['location']['form'] == coreapi.Link(
        url='https://api.example.com/location/form/',
        action='post',
        encoding='application/json',
        fields=[
            coreapi.Field(
                name='a',
                location='form',
                required=True,
                schema=coreschema.String(description='example field')
            ),
            coreapi.Field(
                name='b',
                location='form',
                schema=coreschema.String()
            )
        ]
    )

    assert new['location']['body'] == coreapi.Link(
        url='https://api.example.com/location/body/',
        action='post',
        encoding='application/json',
        fields=[
            coreapi.Field(
                name='example',
                location='body',
                schema=coreschema.String()
            )

        ]
    )

    assert new['encoding']['multipart'] == coreapi.Link(
        url='https://api.example.com/encoding/multipart/',
        action='post',
        encoding='multipart/form-data',
        fields=[
            coreapi.Field(
                name='a',
                location='form',
                required=True,
                schema=coreschema.String()
            ),
            coreapi.Field(
                name='b',
                location='form',
                schema=coreschema.String()
            )
        ]
    )

    assert new['encoding']['urlencoded'] == coreapi.Link(
        url='https://api.example.com/encoding/urlencoded/',
        action='post',
        encoding='application/x-www-form-urlencoded',
        fields=[
            coreapi.Field(
                name='a',
                location='form',
                required=True,
                schema=coreschema.String()
            ),
            coreapi.Field(
                name='b',
                location='form',
                schema=coreschema.String()
            )
        ]
    )

    assert new['encoding']['upload'] == coreapi.Link(
        url='https://api.example.com/encoding/upload/',
        action='post',
        encoding='application/octet-stream',
        fields=[
            coreapi.Field(
                name='example',
                location='body',
                required=True,
                schema=coreschema.String()
            )
        ]
    )

    # Swagger doesn't really support form data in the body, but we
    # map it onto something reasonable anyway.
    assert new['encoding']['multipart-body'] == coreapi.Link(
        url='https://api.example.com/encoding/multipart-body/',
        action='post',
        encoding='multipart/form-data',
        fields=[
            coreapi.Field(
                name='example',
                location='body',
                schema=coreschema.String()
            )
        ]
    )

    assert new['encoding']['urlencoded-body'] == coreapi.Link(
        url='https://api.example.com/encoding/urlencoded-body/',
        action='post',
        encoding='application/x-www-form-urlencoded',
        fields=[
            coreapi.Field(
                name='example',
                location='body',

                schema=coreschema.String()
            )
        ]
    )
