from app import app


def test_helloworld_endpoint_returns_expected_results():

    app.config['TESTING'] = True
    client = app.test_client()

    response = client.get("/helloworld")

    assert response.status_code == 200
    assert "text" in response.content_type
    assert response.data.decode() == "hello world"


