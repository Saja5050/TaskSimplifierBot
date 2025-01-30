from flask import Flask
from app.routes import app as bot_routes
import os

app = Flask(__name__)

# Register routes
app.register_blueprint(bot_routes)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(port=port)