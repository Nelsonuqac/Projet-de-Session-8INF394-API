import json
from flask import Flask, request, jsonify

from config import Config
from models import db, Product, Order
from services import http_get_json, http_post_json
from errors import missing_fields, out_of_inventory, already_paid, not_found

TAX_RATES = {
    "QC": 0.15,
    "ON": 0.13,
    "AB": 0.05,
    "BC": 0.12,
    "NS": 0.14,
}

def compute_shipping_cents(total_weight_g: int) -> int:
    
    # Jusqu'à 500g: 5$ ; 500g à 2kg: 10$ ; 2kg et plus: 25$ :contentReference[oaicite:7]{index=7}
    if total_weight_g <= 500:
        return 500
    if total_weight_g < 2000:
        return 1000
    return 2500

def compute_totals(order: Order):
    
    if not order.product or not order.quantity:
        order.total_price = 0
        order.total_price_tax = 0
        order.shipping_price = 0
        return

    # price est en cents selon l'énoncé :contentReference[oaicite:8]{index=8}
    total_price = int(order.product.price) * int(order.quantity)
    order.total_price = total_price

    total_weight = int(order.product.weight) * int(order.quantity)
    order.shipping_price = compute_shipping_cents(total_weight)

    rate = TAX_RATES.get((order.ship_province or "").upper(), 0.0)
    order.total_price_tax = int(round(total_price * (1.0 + rate)))

def order_to_dict(order: Order):
    
    return {
        "id": order.id,
        "total_price": order.total_price,
        "total_price_tax": order.total_price_tax if order.total_price_tax else 0,
        "email": order.email,
        "credit_card": json.loads(order.credit_card_json or "{}"),
        "shipping_information": {
            "country": order.ship_country,
            "address": order.ship_address,
            "postal_code": order.ship_postal_code,
            "city": order.ship_city,
            "province": order.ship_province,
        } if order.ship_country or order.ship_province else {},
        "paid": order.paid,
        "transaction": json.loads(order.transaction_json or "{}"),
        "product": {
            "id": order.product.product_id,
            "quantity": order.quantity
        } if order.product else {},
        "shipping_price": order.shipping_price,
    }

def product_to_dict(p: Product):
    
    return {
        "name": p.name,
        "id": p.product_id,
        "in_stock": p.in_stock,
        "description": p.description,
        "price": p.price,
        "weight": p.weight,
        "image": p.image,
    }
    
def to_cents(value) -> int:
    
    # Accepte int/float/str; retourne des cents (int)
    if value is None:
        return 0
    try:
        s = str(value).strip()
        s = s.replace(",", ".")
        f = float(s)
        
        # Heuristique : si c'est petit (ex: 28, 29.45) => dollars -> cents
        # si c'est grand (ex: 2810, 2945) => déjà cents
        
        if f < 1000:
            return int(round(f * 100))
        return int(round(f))
    except (ValueError, TypeError):
        return 0

def load_products_once():
    
    # Ne pas recharger à chaque requête : seulement au lancement :contentReference[oaicite:9]{index=9}
    
    if Product.select().count() > 0:
        return

    data = http_get_json(Config.PRODUCTS_URL)
    products = data.get("products", [])

    with db.atomic():
        for item in products:
            
            # item["price"] est censé être en cents :contentReference[oaicite:10]{index=10}
            
            Product.create(
                product_id=int(item["id"]),
                name=item.get("name", ""),
                description=item.get("description"),
                price=to_cents(item.get("price", 0)),

                weight=int(item.get("weight", 0)),
                in_stock=bool(item.get("in_stock", False)),
                image=item.get("image"),
            )

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.before_first_request
    def _startup():
        db.connect(reuse_if_open=True)
        load_products_once()

    @app.teardown_appcontext
    def _shutdown(_exc):
        if not db.is_closed():
            db.close()

    @app.cli.command("init-db")
    def init_db_command():
        db.connect(reuse_if_open=True)
        db.create_tables([Product, Order])
        db.close()
        print("Database initialized.")

    # -------------------
    # GET /
    # -------------------
    @app.route("/", methods=["GET"])
    def list_products():
        prods = [product_to_dict(p) for p in Product.select().order_by(Product.product_id)]
        return jsonify({"products": prods}), 200

    # -------------------
    # POST /order
    # -------------------
    @app.route("/order", methods=["POST"])
    def create_order():
        payload = request.get_json(silent=True) or {}
        product_obj = payload.get("product")

        # Exigences : product obligatoire avec id + quantity, quantity >= 1 :contentReference[oaicite:11]{index=11}
        
        if not isinstance(product_obj, dict):
            return missing_fields("product", "La création d'une commande nécessite un produit")
        if "id" not in product_obj or "quantity" not in product_obj:
            return missing_fields("product", "La création d'une commande nécessite un produit")

        try:
            pid = int(product_obj["id"])
            qty = int(product_obj["quantity"])
        except (ValueError, TypeError):
            return missing_fields("product", "La création d'une commande nécessite un produit")

        if qty < 1:
            return missing_fields("product", "La création d'une commande nécessite un produit")

        prod = Product.get_or_none(Product.product_id == pid)
        if not prod:
            # L'énoncé ne précise pas ce cas explicitement, mais on peut traiter comme out-of-inventory
            
            return out_of_inventory()

        if not prod.in_stock:
            return out_of_inventory()

        order = Order.create(product=prod, quantity=qty)
        compute_totals(order)
        order.save()

        # 302 Found + Location /order/<id> :contentReference[oaicite:12]{index=12}
        resp = app.response_class(status=302)
        resp.headers["Location"] = f"/order/{order.id}"
        return resp

    # -------------------
    # GET /order/<id>
    # -------------------
    @app.route("/order/<int:order_id>", methods=["GET"])
    def get_order(order_id):
        order = Order.get_or_none(Order.id == order_id)
        if not order:
            return not_found()
        
        # Recalcul pour rester cohérent si province/qty existe
        
        compute_totals(order)
        order.save()
        return jsonify({"order": order_to_dict(order)}), 200

    # -------------------
    # PUT /order/<id> (infos client OU paiement)
    # -------------------
    @app.route("/order/<int:order_id>", methods=["PUT"])
    def update_order(order_id):
        order = Order.get_or_none(Order.id == order_id)
        if not order:
            return not_found()

        payload = request.get_json(silent=True) or {}

        # Règle : on ne peut pas fournir credit_card avec shipping_information/email :contentReference[oaicite:13]{index=13}
        
        has_credit = "credit_card" in payload
        has_order_obj = "order" in payload

        if has_credit and has_order_obj:
            return missing_fields("order", "Les informations du client sont nécessaire avant d'appliquer une carte de crédit")

        if has_order_obj:
            order_obj = payload.get("order") or {}
            email = order_obj.get("email")
            ship = order_obj.get("shipping_information") or {}

            required_ship = ["country", "address", "postal_code", "city", "province"]
            if not email or any(k not in ship or not ship.get(k) for k in required_ship):
                return missing_fields("order", "Il manque un ou plusieurs champs qui sont obligatoires")

            order.email = email
            order.ship_country = ship["country"]
            order.ship_address = ship["address"]
            order.ship_postal_code = ship["postal_code"]
            order.ship_city = ship["city"]
            order.ship_province = ship["province"]

            compute_totals(order)
            order.save()
            return jsonify({"order": order_to_dict(order)}), 200

        if has_credit:
            if order.paid:
                return already_paid()

            # Exigence : si pas email et/ou shipping infos -> erreur :contentReference[oaicite:14]{index=14}
            
            if not order.email or not all([order.ship_country, order.ship_address, order.ship_postal_code, order.ship_city, order.ship_province]):
                return missing_fields("order", "Les informations du client sont nécessaire avant d'appliquer une carte de crédit")

            credit = payload.get("credit_card") or {}
            
            # On laisse la validation détaillée au service distant, mais on doit transmettre tel quel.
            
            compute_totals(order)
            order.save()

            amount_charged = int(order.total_price + order.shipping_price)  # inclut shipping :contentReference[oaicite:15]{index=15}
            status, remote = http_post_json(Config.PAYMENT_URL, {
                "credit_card": credit,
                "amount_charged": amount_charged,
            })

            if status != 200:
                
                # Exigence : si le service distant retourne une erreur, la retourner au client :contentReference[oaicite:16]{index=16}
                
                return jsonify(remote), status

            # Persister credit_card + transaction :contentReference[oaicite:17]{index=17}
            order.credit_card_json = json.dumps(remote.get("credit_card", {}))
            order.transaction_json = json.dumps(remote.get("transaction", {}))
            order.paid = True
            order.save()

            return jsonify({"order": order_to_dict(order)}), 200

        # Si aucun champ reconnu
        
        return missing_fields("order", "Il manque un ou plusieurs champs qui sont obligatoires")

    return app

app = create_app()