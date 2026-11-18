"""Admin is a separate page, while REST endpoints stay authenticated."""

def test_admin_ui_separate_but_publicly_served(client):
    r=client.get('/admin')
    assert r.status_code==200
    assert 'id="login-form"' in r.text
    assert '/static/admin.js?v=20261117.7' in r.text
    assert r.headers.get('cache-control')=='no-store'
    assert client.get('/api/v1/admin/overview').status_code==401

def test_admin_assets_are_served(client):
    for path in ('/static/admin.js?v=20261117.7','/static/navigation.js?v=20261116.2','/static/atlas.css?v=20261116.2'):
        assert client.get(path).status_code==200
