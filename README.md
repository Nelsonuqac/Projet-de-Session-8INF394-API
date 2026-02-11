# *Description du projet*

Ce projet est une API REST développée avec Flask permettant :

de consulter une liste de produits,

de créer une commande,

d’ajouter des informations client,

d’effectuer un paiement via un service externe,

de gérer les erreurs métiers (produit invalide, paiement déjà effectué, carte refusée, etc.).
L’API est conçue pour être testée via curl, Postman, ou des scripts automatisés.

*A-Avant l'execution, vous devez:*
creer l'environnement virtuel avec:
python -m venv .venv
.\.venv\Scripts\Activate.ps1

*B-Installer les dependances:*
pip install -r requirements.txt
si requierement.txt est vide, pip install flask peewee

*C-Configuration:*
Les URLs doivent être correctes (HTTPS obligatoire pour le paiement) :

PAYMENT_URL = "https://dimensweb.uqac.ca/~jgnault/shops/pay/"

 Vérifier le chemin de la base
python -c "from config import Config; print(Config.DB_PATH)"

*D- Initialisation de la base de donnees*
A faire avant le 1er Lancement:

$env:FLASK_APP="inf349:app"
$env:FLASK_DEBUG="True"

flask init-db
*ceci cree automatiquement la base db.sqlite3; les tables product et order*.

*E- Lancer le serveur:*
flask run
par defaut http://127.0.0.1:5000

*F-Utilisation de l'API pendant l'execution:*
pour recuperer les produits
curl.exe http://127.0.0.1:5000

*F- Creer une commande:*
'{ "product": { "id": 1, "quantity": 2 } }' | Set-Content order.json

curl.exe -i -X POST http://127.0.0.1:5000/order `
  -H "Content-Type: application/json" `
  --data-binary "@order.json"
*Récupérer l’ID dans le header Location*

*Ajouter les informations client*:
'{ 
  "order": {
    "email": "test@test.com",
    "shipping_information": {
      "country": "Canada",
      "address": "201, rue Président-Kennedy",
      "postal_code": "G7X 3Y7",
      "city": "Chicoutimi",
      "province": "QC"
    }
  }
}' | Set-Content client.json

curl.exe -X PUT http://127.0.0.1:5000/order/ID `
  -H "Content-Type: application/json" `
  --data-binary "@client.json"

*Effectuer le paiement:*
curl.exe -X PUT http://127.0.0.1:5000/order/ID `
  -H "Content-Type: application/json" `
  -d '{ 
    "credit_card": {
      "name": "John Doe",
      "number": "4242 4242 4242 4242",
      "expiration_year": 2030,
      "expiration_month": 12,
      "cvv": "123"
    }
  }'
*La commande passe à paid: true*

*G- Cas d'erreurs gérés:*

# Produit invalide → 422 missing-fields 

# Produit hors stock → 422 out-of-inventory 

# Paiement sans infos client → 422 missing-fields

# Paiement deux fois → 422 already-paid

# Carte expirée/refusée → erreur du service externe relayée
 
 *H-Arrêter l’application (après l’exécution)*
 CTRL + C
⚠️ Toujours arrêter Flask avant de supprimer db.sqlite3.

*I-Supprimer la base:* Remove-Item .\db.sqlite3.

## Base de données

Le fichier `schema.sql` est volontairement vide.
Les tables sont créées dynamiquement via Peewee lors de la commande `flask init-db`.
