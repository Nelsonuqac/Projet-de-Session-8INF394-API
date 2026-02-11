import os

class Config:
    DB_PATH = os.environ.get("INF349_DB_PATH", os.path.join(os.getcwd(), "db.sqlite3"))

    PRODUCTS_URL = os.environ.get(
        "INF349_PRODUCTS_URL",
        "http://dimensweb.uqac.ca/~jgnault/shops/products/"
    )

    PAYMENT_URL = os.environ.get(
    "INF349_PAYMENT_URL",
    "https://dimensweb.uqac.ca/~jgnault/shops/pay/"
)
