from flask import Blueprint, request
from app.controllers.handlers import handle_command

# Create a Blueprint object
app = Blueprint('app', __name__)

# Define routes using the blueprint
@app.route('/message', methods=["POST"])
def message():
    data = request.get_json()  # Get the incoming data
    return handle_command(data)  # Call the handler for the command
