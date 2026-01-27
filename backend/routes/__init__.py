from flask import Blueprint

# Create blueprints
campaigns_bp = Blueprint('campaigns', __name__, url_prefix='/api/campaigns')
contributions_bp = Blueprint('contributions', __name__, url_prefix='/api/contributions')
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
payments_bp = Blueprint('payments', __name__, url_prefix='/api')

# Import routes to register them
from . import campaigns, contributions, auth, payments


__all__ = ['campaigns_bp', 'contributions_bp', 'auth_bp', 'payments_bp']
