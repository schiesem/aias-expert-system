# Route zum Erhalt der Ontology Configuration
# Imports
import json, os, sys

# Konsolenkodierung unter Windows auf UTF-8 setzen, damit die Statusausgaben
# auch in Konsolen mit cp1252 als Standardkodierung dargestellt werden koennen.
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

from flask import Flask
from flask_cors import CORS
from routes import register_blueprints

BASE_DIR = os.path.dirname(__file__)

#Laden der Configurationsdatei für den Webserver
CONFIGDATA_PATH = os.path.abspath(os.path.join(BASE_DIR, 'configData.json'))
with open(CONFIGDATA_PATH) as file:
    configData_dict = json.load(file)

# --- Beginn des Webserbers --- #
app = Flask(__name__)
## CORS erlaube für alle Domains
CORS(app)

# Registriere alle Routen über Blueprints
register_blueprints(app)

# Initialize: Initialize global singleton on startup
print("\n" + "="*60)
print("🚀 INITIALIZING BACKEND SERVER")
print("="*60)
try:
    from app_globals import get_ontology_manager

    # Initialize global singleton (loads from existing working copy if it exists)
    manager = get_ontology_manager()

    # Clear old graph visualizations
    manager.clear_graph_visualizations()

    # Report status
    individuals_count = len(list(manager.ontology.individuals())) if manager.ontology else 0
    print("✅ Server initialization complete")
    print(f"   Ontology loaded: {manager.ontology is not None}")
    print(f"   Individuals count: {individuals_count}")

except Exception as e:
    print(f"⚠️ Warning: Initialization error: {e}")
    import traceback
    traceback.print_exc()
print("="*60 + "\n")

# Starten der Hauptapplikation
if __name__ == "__main__":
    # Der Reloader wird bewusst abgeschaltet: Er startet einen zweiten Prozess,
    # der die Ontologie ein weiteres Mal laedt. Beide Prozesse lauschen auf
    # demselben Port und beantworten Anfragen abwechselnd, was zu
    # widerspruechlichen Klassennamen und fehlenden Beziehungen fuehrt.
    app.run(
        host=configData_dict["ips"]["backend"],
        port=configData_dict["ports"]["backend"],
        debug=True,
        use_reloader=False)