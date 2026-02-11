import os
import pytest

from inf349 import create_app
from models import db, Product, Order

@pytest.fixture
def app(tmp_path, monkeypatch):
    test_db = tmp_path / "test.sqlite3"
    monkeypatch.setenv("INF349_DB_PATH", str(test_db))

    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        db.connect(reuse_if_open=True)
        db.create_tables([Product, Order])

        # Produits de test (évite d'appeler le service distant pendant les tests)
        
        Product.create(product_id=1, name="P1", description="d", price=1000, weight=400, in_stock=True, image="0.jpg")
        Product.create(product_id=2, name="P2", description="d", price=2000, weight=2100, in_stock=True, image="1.jpg")
        Product.create(product_id=3, name="P3", description="d", price=1500, weight=300, in_stock=False, image="2.jpg")

        db.close()

    yield app
