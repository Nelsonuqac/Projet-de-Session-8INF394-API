def test_get_root_products(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.get_json()
    assert "products" in data
    assert len(data["products"]) >= 3
