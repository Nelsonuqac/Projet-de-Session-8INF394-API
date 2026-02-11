def test_post_order_missing_fields(client):
    
    r = client.post("/order", json={})
    assert r.status_code == 422
    assert r.get_json()["errors"]["product"]["code"] == "missing-fields"

def test_post_order_out_of_inventory(client):
    
    r = client.post("/order", json={"product": {"id": 3, "quantity": 1}})
    assert r.status_code == 422
    assert r.get_json()["errors"]["product"]["code"] == "out-of-inventory"

def test_post_order_success_302(client):
    
    r = client.post("/order", json={"product": {"id": 1, "quantity": 2}})
    assert r.status_code == 302
    assert r.headers.get("Location", "").startswith("/order/")

def test_put_order_customer_info_missing(client):
    
    # créer une commande
    
    r = client.post("/order", json={"product": {"id": 1, "quantity": 1}})
    loc = r.headers["Location"]
    order_id = int(loc.split("/")[-1])

    r2 = client.put(f"/order/{order_id}", json={"order": {"shipping_information": {"country": "Canada"}}})
    assert r2.status_code == 422
    assert r2.get_json()["errors"]["order"]["code"] == "missing-fields"

def test_shipping_computation_thresholds(client):
    
    # Produit id=1 weight=400g, qty=2 => 800g => shipping 10$ => 1000 cents
    r = client.post("/order", json={"product": {"id": 1, "quantity": 2}})
    order_id = int(r.headers["Location"].split("/")[-1])

    # Ajouter infos client pour calcul taxes (QC 15%)
    
    r2 = client.put(f"/order/{order_id}", json={
        "order": {
            "email": "a@b.com",
            "shipping_information": {
                "country": "Canada",
                "address": "201",
                "postal_code": "G7X",
                "city": "Chicoutimi",
                "province": "QC"
            }
        }
    })
    assert r2.status_code == 200
    order = r2.get_json()["order"]
    assert order["shipping_price"] == 1000
