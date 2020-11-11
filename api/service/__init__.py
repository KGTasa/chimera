from flask import Blueprint

service_bp = Blueprint('service_bp', __name__)
from . import views