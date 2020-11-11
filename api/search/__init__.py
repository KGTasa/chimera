from flask import Blueprint

search_bp = Blueprint('search_bp', __name__)
from . import views