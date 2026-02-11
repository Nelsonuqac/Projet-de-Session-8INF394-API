-- schema.sql (documentaire uniquement)

CREATE TABLE product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    price INTEGER NOT NULL,
    weight INTEGER NOT NULL,
    in_stock BOOLEAN NOT NULL,
    image TEXT
);

CREATE TABLE "order" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    email TEXT,
    ship_country TEXT,
    ship_address TEXT,
    ship_postal_code TEXT,
    ship_city TEXT,
    ship_province TEXT,
    total_price INTEGER,
    total_price_tax INTEGER,
    shipping_price INTEGER,
    credit_card_json TEXT,
    transaction_json TEXT,
    paid BOOLEAN DEFAULT 0,
    FOREIGN KEY(product_id) REFERENCES product(id)
);
