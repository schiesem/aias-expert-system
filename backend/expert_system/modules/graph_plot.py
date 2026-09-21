import os
import json
from pyvis.network import Network
from . import path_utils

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = path_utils.get_relative_path(BASE_DIR, "..", "..", "templates")

def import_test(text):
    print(text)
    print("Hallo, Welt! Der Import des Pakets hat geklappt!")

def save_class_hierarchy_to_json(dict, file_path: str, file_name : str):
    """Speichert die Klassenhierarchie der Ontologie als JSON-Datei."""

    file_abs = os.path.join(file_path, file_name)

    try:
        with open(file_abs, 'w', encoding='utf-8') as f:
            json.dump(dict, f, indent=4, ensure_ascii=False)
        print(f"Klassenhierarchie erfolgreich in {file_path} {file_name} gespeichert.")
    except Exception as e:
        print(f"Fehler beim Speichern der JSON-Datei: {e}")

def create_pyviy_network_plot(ontology, templates_path : str = TEMPLATES_DIR, graph_type: str = 'instance'):
    import os
    from pyvis.network import Network

    if ontology is None:
        print("❌ Fehler: Ontologie ist None, Abbruch.")
        return

    net = Network(height="100%", width="100%", directed=True)
    net.toggle_physics(True)

    # Alle Knoten aus der Ontologie hinzufügen
    nodes = set()
    try:
        individuals = list(ontology.individuals())
        if not individuals:
            print("❌ Fehler: Keine Individuen in der Ontologie vorhanden!")
            return

        for indiv in individuals:
            try:
                # Get the class name (type) of the individual
                class_name = ""
                if indiv.is_a:
                    # Get all direct classes (excluding Thing)
                    direct_classes = [cls.name for cls in indiv.is_a if hasattr(cls, 'name') and cls.name != 'Thing']
                    if direct_classes:
                        if graph_type == 'inferred':
                            class_name = " | ".join(direct_classes)
                        else:
                            class_name = direct_classes[0]

                # Create multi-line label: ID on first line, class name on second line
                label = f"{indiv.name}\n{class_name}" if class_name else indiv.name

                # Add datatype properties to label (like hasName)
                datatype_props = []
                for prop in indiv.get_properties():
                    for value in prop[indiv]:
                        # Check if it's a datatype property (not an individual)
                        if not hasattr(value, 'name'):
                            # It's a literal value (string, number, etc.)
                            prop_name = prop.name
                            # Format the value nicely
                            if isinstance(value, str):
                                datatype_props.append(f"{prop_name}: {value}")
                            elif isinstance(value, (int, float)):
                                datatype_props.append(f"{prop_name}: {value}")

                # Append datatype properties to label
                if datatype_props:
                    label += "\n" + "\n".join(datatype_props)

                net.add_node(indiv.name, label=label)
                nodes.add(indiv.name)
            except Exception as e:
                print(f"⚠️ Fehler beim Hinzufügen des Knotens '{indiv.name}': {e}")
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der Individuen aus der Ontologie: {e}")
        return

    # Edges hinzufügen
    try:
        for indiv in individuals:
            for prop in indiv.get_properties():
                for value in prop[indiv]:
                    try:
                        # Check if value is an individual (has .name attribute) or a literal (string/number)
                        if hasattr(value, 'name'):
                            # It's an individual - create edge
                            if value.name in nodes:
                                net.add_edge(indiv.name, value.name, label=prop.name)
                            else:
                                print(f"⚠️ Warnung: Zielknoten '{value.name}' existiert nicht, Kante übersprungen.")
                        # else: It's a datatype property value (string, int, etc.) - skip
                    except Exception as e:
                        print(f"⚠️ Fehler beim Hinzufügen der Kante '{indiv.name}': {e}")
    except Exception as e:
        print(f"❌ Fehler beim Verarbeiten der Kanten: {e}")
        return

    # Sicherstellen, dass der Pfad existiert
    try:
        os.makedirs(templates_path, exist_ok=True)
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Ausgabeordners: {e}")
        return

    # Choose output file and title based on graph type
    if graph_type == 'instance':
        output_filename = "ontology_graph_instance.html"
        title = "Ontology Graph (User Model)"
    else:  # 'inferred'
        output_filename = "ontology_graph_inferred.html"
        title = "Ontology Graph (With Reasoning)"

    # Graph speichern mit benutzerdefiniertem Template
    output_path = os.path.join(templates_path, output_filename)
    try:
        # Generiere HTML mit pyvis in temporärer Datei
        temp_path = os.path.join(templates_path, "temp_graph.html")
        net.write_html(temp_path)

        # Lese die generierte HTML, um nodes und edges zu extrahieren
        with open(temp_path, 'r', encoding='utf-8') as f:
            temp_html = f.read()

        # Extrahiere nodes und edges aus dem generierten HTML
        import re
        nodes_match = re.search(r'nodes = new vis\.DataSet\((.*?)\);', temp_html, re.DOTALL)
        edges_match = re.search(r'edges = new vis\.DataSet\((.*?)\);', temp_html, re.DOTALL)
        options_match = re.search(r'var options = ({.*?});', temp_html, re.DOTALL)

        nodes_data = nodes_match.group(1) if nodes_match else '[]'
        edges_data = edges_match.group(1) if edges_match else '[]'
        options_data = options_match.group(1) if options_match else '{}'

        # Set title based on graph type (no toggle button needed - handled by modal)
        if graph_type == 'instance':
            title = 'Ontology Graph (Instance)'
        else:  # 'inferred'
            title = 'Ontology Graph (Inferred)'

        # Erstelle benutzerdefiniertes HTML mit Reload-Button und Toggle
        custom_html = f"""<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">

            <!-- <script src="lib/bindings/utils.js"></script> -->
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/dist/vis-network.min.css" integrity="sha512-WgxfT5LWjfszlPHXRmBWHkV2eceiWTOBvrKCNbdgDYTHrT2AeLCGbF4sZlZw3UMN3WtL0tGUoIAKsu8mllg/XA==" crossorigin="anonymous" referrerpolicy="no-referrer" />
            <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js" integrity="sha512-LnvoEWDFrqGHlHmDD2101OrLcbsfkrzoSpvtSQtxK3RMnRV0eOkhhBN2dXHKRrUU8p2DGRTk35n4O8nWSVe1mQ==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>


<center>
<h1></h1>
</center>

<!-- <link rel="stylesheet" href="../node_modules/vis/dist/vis.min.css" type="text/css" />
<script type="text/javascript" src="../node_modules/vis/dist/vis.js"> </script>-->
        <link
          href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/css/bootstrap.min.css"
          rel="stylesheet"
          integrity="sha384-eOJMYsd53ii+scO/bJGFsiCZc+5NDVN2yr8+0RDqr0Ql0h+rP48ckxlpbzKgwra6"
          crossorigin="anonymous"
        />
        <script
          src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/js/bootstrap.bundle.min.js"
          integrity="sha384-JEW9xMcG8R+pH31jmWH6WWP0WintQrMb4s7ZOdauHnUtxwoG2vI5DkLtS3qm9Ekf"
          crossorigin="anonymous"
        ></script>


        <center>
          <h1></h1>
        </center>
        <style type="text/css">
             html, body {{
                 height: 100%;
                 margin: 0;
                 padding: 0;
                 overflow: hidden;
             }}

             #mynetwork {{
                 width: 100%;
                 height: calc(100vh - 60px);
                 background-color: #ffffff;
                 border: 1px solid lightgray;
                 position: relative;
                 float: left;
             }}






        </style>
    </head>


    <body>
        <div class="card" style="width: 100%">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">{title}</h5>
                <div>
                    <button onclick="location.reload()" class="btn btn-primary btn-sm">
                        Reload Graph
                    </button>
                </div>
            </div>
            <div id="mynetwork" class="card-body"></div>
        </div>




        <script type="text/javascript">

              // initialize global variables.
              var edges;
              var nodes;
              var allNodes;
              var allEdges;
              var nodeColors;
              var originalNodes;
              var network;
              var container;
              var options, data;
              var filter = {{
                  item : '',
                  property : '',
                  value : []
              }};





              // This method is responsible for drawing the graph, returns the drawn network
              function drawGraph() {{
                  var container = document.getElementById('mynetwork');



                  // parsing and collecting nodes and edges from the python
                  nodes = new vis.DataSet({nodes_data});
                  edges = new vis.DataSet({edges_data});

                  nodeColors = {{}};
                  allNodes = nodes.get({{ returnType: "Object" }});
                  for (nodeId in allNodes) {{
                    nodeColors[nodeId] = allNodes[nodeId].color;
                  }}
                  allEdges = edges.get({{ returnType: "Object" }});
                  // adding nodes and edges to the graph
                  data = {{nodes: nodes, edges: edges}};

                  var options = {options_data};

                  // Override physics settings to increase node spacing
                  options.physics = {{
                      enabled: true,
                      barnesHut: {{
                          gravitationalConstant: -8000,
                          centralGravity: 0.3,
                          springLength: 180,
                          springConstant: 0.04,
                          damping: 0.09,
                          avoidOverlap: 0.5
                      }},
                      stabilization: {{
                          iterations: 200
                      }}
                  }};






                  network = new vis.Network(container, data, options);










                  return network;

              }}
              drawGraph();
        </script>
    </body>
</html>
"""

        # Schreibe die benutzerdefinierte HTML-Datei
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(custom_html)

        # Lösche temporäre Datei
        os.remove(temp_path)

        print(f"Graph wurde gespeichert unter: {output_path}")
    except Exception as e:
        print(f"❌ Fehler beim Schreiben der HTML-Datei: {e}")

