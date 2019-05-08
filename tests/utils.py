import json
from runway import RunwayModel

def get_test_client(rw_model):
    assert isinstance(rw_model, RunwayModel)
    rw_model.app.config['TESTING'] = True
    return rw_model.app.test_client()

def get_manifest(client):
    response = client.get('/meta')
    return json.loads(response.data)
