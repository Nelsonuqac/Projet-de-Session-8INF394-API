from flask import jsonify

def error_response(status_code: int, scope: str, code: str, name: str):
    return jsonify({"errors": {scope: {"code": code, "name": name}}}), status_code

def missing_fields(scope: str, name: str):
    return error_response(422, scope, "missing-fields", name)

def out_of_inventory():
    return error_response(422, "product", "out-of-inventory", "Le produit demandé n'est pas en inventaire")

def already_paid():
    return error_response(422, "order", "already-paid", "La commande a déjà été payée.")

def not_found():
    return "", 404
