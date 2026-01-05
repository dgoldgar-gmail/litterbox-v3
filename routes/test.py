import logging
from flask import Blueprint, render_template, current_app

logger = logging.getLogger(__name__)
logger.propagate = True

test_bp = Blueprint('test', __name__, template_folder='../../templates')

@test_bp.route('/')
def test_home():
    print("Here i am")
    logger.info("test route")
    return render_template('test/test.html', message="Hello from the test route!")
