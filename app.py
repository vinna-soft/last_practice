from flask import Flask
from routes.auth_routes import auth
from routes.home_routes import home
from routes.customer_routes import customer
from routes.provider_route import provider
from routes.admin_route import admin
from routes.super_admin_route import super_admin

app = Flask(__name__)

#session secret key
app.secret_key = "my_secret_key_1121"

app.register_blueprint(auth)
app.register_blueprint(home)
app.register_blueprint(customer)
app.register_blueprint(provider)
app.register_blueprint(admin)
app.register_blueprint(super_admin)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug = True)