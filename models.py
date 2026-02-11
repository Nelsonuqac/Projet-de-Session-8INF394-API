import json
from peewee import (
    Model, SqliteDatabase,
    IntegerField, CharField, BooleanField, TextField, ForeignKeyField
)
from config import Config

db = SqliteDatabase(Config.DB_PATH)

class BaseModel(Model):
    class Meta:
        database = db

class Product(BaseModel):
    product_id = IntegerField(unique=True)     # id distant
    name = CharField()
    description = TextField(null=True)
    price = IntegerField()                     # en cents (selon l'énoncé)
    weight = IntegerField()                    # en grammes
    in_stock = BooleanField()
    image = CharField(null=True)

class Order(BaseModel):
    
    # Informations client
    email = CharField(null=True)

    ship_country = CharField(null=True)
    ship_address = CharField(null=True)
    ship_postal_code = CharField(null=True)
    ship_city = CharField(null=True)
    ship_province = CharField(null=True)

    # Produit (une seule ligne produit pour la remise 1)
    
    product = ForeignKeyField(Product, backref="orders", null=True)
    quantity = IntegerField(null=True)

    # Totaux calculés
    total_price = IntegerField(default=0)        # cents (sans shipping)
    total_price_tax = IntegerField(default=0)    # cents (sans shipping)
    shipping_price = IntegerField(default=0)     # cents

    # Paiement
    paid = BooleanField(default=False)

    # Stockage JSON des données retournées
    
    credit_card_json = TextField(default="{}")
    transaction_json = TextField(default="{}")

    def credit_card(self):
        return json.loads(self.credit_card_json or "{}")

    def transaction(self):
        return json.loads(self.transaction_json or "{}")
