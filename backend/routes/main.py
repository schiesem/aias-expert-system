# routes/graph_view.py

from flask import Blueprint, render_template

main_bp = Blueprint("main_bp", __name__, template_folder="../templates")

# Main Route
@main_bp.route("/", methods=["GET"], strict_slashes=False)
def mainPage():
    return render_template('index.html')