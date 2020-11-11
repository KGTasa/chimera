from flask import Blueprint

grab_bp = Blueprint('grab_bp', __name__)
from . import views