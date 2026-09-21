# routes/graph_view.py

from flask import Blueprint, render_template, jsonify
from app_globals import get_annotation_manager

graph_bp = Blueprint("graph_bp", __name__, template_folder="../templates")


@graph_bp.route("/", methods=['GET', 'OPTIONS'], strict_slashes=False)
def graph_page():
    """Serve the default graph visualization page (instance ontology)."""
    import os
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "ontology_graph_instance.html")

    if not os.path.exists(template_path):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Instance Graph Not Available</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    background-color: #f5f5f5;
                }
                .message-card {
                    max-width: 600px;
                    text-align: center;
                    padding: 2rem;
                }
            </style>
        </head>
        <body>
            <div class="card message-card">
                <div class="card-body">
                    <h3 class="card-title mb-4">📊 No Model Data Available</h3>
                    <p class="card-text mb-4">
                        The instance ontology graph doesn't exist yet.
                        Please create some elements in the frontend first.
                    </p>
                    <div class="d-grid gap-2">
                        <a href="/" class="btn btn-primary">
                            Back to Main Page
                        </a>
                    </div>
                    <hr class="my-4">
                    <small class="text-muted">
                        Create nodes and edges in the frontend, then the graph will be generated automatically.
                    </small>
                </div>
            </div>
        </body>
        </html>
        """, 200

    return render_template("ontology_graph_instance.html")


@graph_bp.route("/instance", methods=['GET', 'OPTIONS'], strict_slashes=False)
def graph_instance():
    """Serve the instance ontology graph visualization (user model only)."""
    import os
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "ontology_graph_instance.html")

    if not os.path.exists(template_path):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Instance Graph Not Available</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    background-color: #f5f5f5;
                }
                .message-card {
                    max-width: 600px;
                    text-align: center;
                    padding: 2rem;
                }
            </style>
        </head>
        <body>
            <div class="card message-card">
                <div class="card-body">
                    <h3 class="card-title mb-4">📊 No Model Data Available</h3>
                    <p class="card-text mb-4">
                        The instance ontology graph doesn't exist yet.
                        Please create some elements in the frontend first.
                    </p>
                    <div class="d-grid gap-2">
                        <a href="/" class="btn btn-primary">
                            Back to Main Page
                        </a>
                    </div>
                    <hr class="my-4">
                    <small class="text-muted">
                        Create nodes and edges in the frontend, then the graph will be generated automatically.
                    </small>
                </div>
            </div>
        </body>
        </html>
        """, 200

    return render_template("ontology_graph_instance.html")


@graph_bp.route("/inferred", methods=['GET', 'OPTIONS'], strict_slashes=False)
def graph_inferred():
    """Serve the inferred ontology graph visualization (with reasoning results)."""
    import os
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "ontology_graph_inferred.html")

    # Check if inferred graph exists
    if not os.path.exists(template_path):
        # Return a helpful message if reasoning hasn't been run yet
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Inferred Graph Not Available</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    background-color: #f5f5f5;
                }
                .message-card {
                    max-width: 600px;
                    text-align: center;
                    padding: 2rem;
                }
            </style>
        </head>
        <body>
            <div class="card message-card">
                <div class="card-body">
                    <h3 class="card-title mb-4">⚠️ No Reasoning Results Available</h3>
                    <p class="card-text mb-4">
                        The inferred ontology graph doesn't exist yet.
                        Please run reasoning first to generate the inferred graph.
                    </p>
                    <div class="d-grid gap-2">
                        <a href="/graph/instance" class="btn btn-primary">
                            View User Model Graph
                        </a>
                        <a href="/" class="btn btn-secondary">
                            Back to Main Page
                        </a>
                    </div>
                    <hr class="my-4">
                    <small class="text-muted">
                        To generate the inferred graph, click "Run Reasoning" in the Expert System panel.
                    </small>
                </div>
            </div>
        </body>
        </html>
        """, 200

    return render_template("ontology_graph_inferred.html")


@graph_bp.route("/data", methods=['GET'], strict_slashes=False)
def graph_data():
    """
    Get the current ontology instance graph data for visualization.

    Returns nodes and edges representing all individuals and their relationships.
    """
    try:
        # Use the global annotation ontology manager if available
        # If not initialized, try to initialize it
        try:
            manager = get_annotation_manager()
            onto = manager.onto_manager.ontology
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Could not load ontology: {str(e)}',
                'nodes': [],
                'edges': []
            }), 200

        nodes = []
        edges = []

        # Get all individuals
        for individual in onto.individuals():
            # Get the individual's class
            individual_class = individual.__class__.__name__

            # Determine color based on class
            color = _get_color_for_class(individual_class)

            nodes.append({
                'id': individual.name,
                'label': f"{individual_class}\n{individual.name}",  # Show class and identifier
                'title': f"{individual_class}: {individual.name}",  # Tooltip
                'shape': 'dot',
                'color': color,
                'class': individual_class
            })

            # Get all object property relations
            for prop in individual.get_properties():
                from owlready2 import ObjectPropertyClass
                if isinstance(prop, ObjectPropertyClass):
                    values = getattr(individual, prop.name, [])
                    if not isinstance(values, list):
                        values = [values] if values else []

                    for target in values:
                        if target:
                            edges.append({
                                'from': individual.name,
                                'to': target.name,
                                'label': prop.name,
                                'arrows': 'to',
                                'title': prop.name  # Tooltip
                            })

        print(f"📊 Graph data: {len(nodes)} nodes, {len(edges)} edges")

        return jsonify({
            'success': True,
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'node_count': len(nodes),
                'edge_count': len(edges)
            }
        }), 200

    except Exception as e:
        print(f"❌ Error generating graph data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'nodes': [],
            'edges': []
        }), 500


def _get_color_for_class(class_name):
    """Get a color for a given class name."""
    # Color mapping for common classes
    color_map = {
        'Acquisition': '#FFB6C1',  # Light pink
        'DataSource': '#87CEEB',   # Sky blue
        'Model': '#90EE90',         # Light green
        'Training': '#DDA0DD',      # Plum
        'Inference': '#F0E68C',     # Khaki
        'ModelParameter': '#FFA07A', # Light salmon
    }

    return color_map.get(class_name, '#97c2fc')  # Default blue 