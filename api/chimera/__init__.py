from flask import Blueprint

chimera_bp = Blueprint('chimera_bp', __name__)
from . import views