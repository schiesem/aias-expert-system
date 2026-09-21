import os, io, shutil, json
from rdflib import Graph
from owlready2 import get_ontology, onto_path, destroy_entity, World
from . import path_utils

# Nur Verzeichnis   -> _dir
# Nur Nur Dateiname -> _file
# Kompletter Pfad   -> _path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ONTO_DIR = path_utils.get_relative_path(BASE_DIR, "ontologies")
ODP_DIR = path_utils.get_relative_path(ONTO_DIR, "odps")

# AIAS.owl - Read-only schema ontology (never modified)
BASE_ONTO_FILE = "AIAS.owl"
BASE_ONTO_PATH = path_utils.get_relative_path(ONTO_DIR, "AIAS.owl")

# AIAS-instance.owl - Working copy with instances (modified during runtime)
INSTANCE_ONTO_FILE = "AIAS-instance.owl"
INSTANCE_ONTO_PATH = path_utils.get_relative_path(ONTO_DIR, "AIAS-instance.owl")

# AIAS-inferred.owl - Reasoning results ontology (created when reasoning is run)
INFERRED_ONTO_FILE = "AIAS-inferred.owl"
INFERRED_ONTO_PATH = path_utils.get_relative_path(ONTO_DIR, "AIAS-inferred.owl")

class OntologyManager:
    def __init__(self, file_path: str = BASE_ONTO_PATH, folder_path: str = ONTO_DIR, odp_path: str = ODP_DIR, world_dir: str = None):
        """
        Initialisiert die Ontologie aus einer lokalen Datei.

        Args:
            file_path: Path to base ontology schema
            folder_path: Folder for ontology files
            odp_path: Path to ODP ontologies
            world_dir: Optional world-specific directory (overrides folder_path)
        """
        # Pfade
        self.file_path = file_path
        self.folder_path = folder_path
        self.odp_path = odp_path

        # World-specific paths (if provided)
        self.world_dir = world_dir
        if world_dir:
            self.instance_path = os.path.join(world_dir, "AIAS-instance.owl")
            self.inferred_path = os.path.join(world_dir, "AIAS-inferred.owl")
        else:
            self.instance_path = INSTANCE_ONTO_PATH
            self.inferred_path = INFERRED_ONTO_PATH

        # World- und Selfontologie
        self.world = None
        self.ontology = None

        # Namespaces
        self.ontology_namespaces = None

    def load_ontologie(self, default_inferenz: bool = False, name: str = "AIAS", format: str = "owl", case_path:str = None, case_name:str=None, case_format:str=None):
        """
        Lädt die Hauptontologie (z.B. AIAS) in einer isolierten owlready2.World, um Konflikte mit Fallontologien zu vermeiden.

        IMPORTANT: Creates a fresh working copy (AIAS-instance.owl) from the schema (AIAS.owl) to ensure clean state.
        """
        try:
            onto_path.clear()  # Setze die `onto_path` zurück, um mögliche Konflikte zu vermeiden
            onto_path.append(self.odp_path)  # Pfad für ODPs

            # Determine which ontology to load
            schema_file_path = os.path.join(self.folder_path, f"{name}.{format}")

            # If loading AIAS (main ontology), create fresh working copy
            if name == "AIAS":
                instance_file_path = self.instance_path

                # Create fresh copy from schema
                print(f"📋 Creating fresh working copy: {INSTANCE_ONTO_FILE}")
                shutil.copy2(schema_file_path, instance_file_path)
                print(f"✅ Fresh copy created from {BASE_ONTO_FILE}")

                # Load the working copy (not the schema!)
                base_file_path = instance_file_path
            else:
                # For other ontologies (e.g., case ontologies), load directly
                base_file_path = schema_file_path

            # Neue isolierte World für diese Ontologie
            self.world = World()
            self.ontology = self.world.get_ontology(base_file_path).load()

            # Optional: Inferenz aktivieren
            self.world.infered = default_inferenz

            print(f"✅ Ontologie '{name}' erfolgreich isoliert geladen von: {base_file_path}\n")

            # Zeige alle Ontologien innerhalb dieser World
            print("📦 Enthaltene Ontologien in dieser World:")
            for onto in self.world.ontologies.values():
                print(f"- {onto.base_iri}")

            # Namespaces merken
            self.ontology_namespaces = self.world.ontologies.keys()
            print(f"🌐 Importierte Namespaces: {self.ontology_namespaces}")

            #Case-ontologie laden, wenn angegeben
            if case_path and case_name and case_format:
                case_file_path = os.path.join(case_path, f"{case_name}.{case_format}")
                self.ontology = self.world.get_ontology(case_file_path).load()

        except Exception as e:
            print(f"❌ Fehler beim Laden der Ontologie: {e}")

    def load_from_working_copy(self):
        """
        Load existing AIAS-instance.owl WITHOUT overwriting.

        This is the DEFAULT method for normal operations. It loads the existing
        working copy which contains:
        - Graphical elements (nodes/edges)
        - Annotations
        - Graphical state (positions, viewport)

        If no working copy exists, creates a fresh one from schema.

        IMPORTANT: This method NEVER overwrites existing data.
        """
        try:
            if not os.path.exists(self.instance_path):
                print("⚠️ No working copy exists, initializing fresh...")
                return self.initialize_fresh()

            print(f"📖 Loading existing working copy: {INSTANCE_ONTO_FILE}")

            # Prepare ontology path
            onto_path.clear()
            onto_path.append(self.odp_path)

            # Create World and load existing file
            self.world = World()
            self.ontology = self.world.get_ontology(self.instance_path).load()
            self.world.infered = False

            # Store namespaces
            self.ontology_namespaces = self.world.ontologies.keys()

            individuals_count = len(list(self.ontology.individuals()))
            print(f"✅ Loaded working copy with {individuals_count} individuals")
            print(f"🌐 Imported namespaces: {self.ontology_namespaces}")

        except Exception as e:
            print(f"❌ Error loading working copy: {e}")
            import traceback
            traceback.print_exc()

    def initialize_fresh(self):
        """
        Create fresh working copy from schema.

        ONLY call this when starting a NEW modeling session.
        This will:
        - Copy AIAS.owl → AIAS-instance.owl (OVERWRITES existing!)
        - Delete all existing data
        - Start with clean schema
        - Create default AISystem individual for this world

        WARNING: This deletes all annotations and model data!
        """
        try:
            schema_file_path = os.path.join(self.folder_path, BASE_ONTO_FILE)

            print(f"📋 Creating fresh working copy from schema...")
            print(f"⚠️  WARNING: This will overwrite {INSTANCE_ONTO_FILE}")

            # Create fresh copy from schema
            shutil.copy2(schema_file_path, self.instance_path)
            print(f"✅ Fresh copy created from {BASE_ONTO_FILE}")

            # Load the fresh working copy
            onto_path.clear()
            onto_path.append(self.odp_path)

            self.world = World()
            self.ontology = self.world.get_ontology(self.instance_path).load()
            self.world.infered = False

            # Store namespaces
            self.ontology_namespaces = self.world.ontologies.keys()

            print(f"✅ Fresh ontology initialized")
            print(f"🌐 Imported namespaces: {self.ontology_namespaces}")

            # Create default AISystem individual for this world
            self._create_default_ai_system()

        except Exception as e:
            print(f"❌ Error initializing fresh ontology: {e}")
            import traceback
            traceback.print_exc()

    def _create_default_ai_system(self):
        """
        Create default AISystem individual for a new world.

        This creates an ISO22989:AISystem individual with:
        - Individual name: world UUID (e.g., "world_39519ab06fb4254b")
        - hasName property: human-readable world name from metadata.json

        This is automatically called when initializing a fresh ontology.
        """
        try:
            # Extract world info from world_dir
            if not self.world_dir:
                print("⚠️ No world_dir set, skipping AISystem creation")
                return

            # Get world ID from folder name (e.g., "world_39519ab06fb4254b")
            world_folder_name = os.path.basename(self.world_dir)

            # Read metadata to get human-readable name
            metadata_path = os.path.join(self.world_dir, "metadata.json")
            if not os.path.exists(metadata_path):
                print(f"⚠️ No metadata.json found at {metadata_path}, skipping AISystem creation")
                return

            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            human_readable_name = metadata.get('name', world_folder_name)

            print(f"🤖 Creating default AISystem individual for world...")
            print(f"   Individual ID: {world_folder_name}")
            print(f"   hasName: {human_readable_name}")

            # Create AISystem individual
            # Use ISO22989:AISystem class
            ai_system = self.create_individual_object("ISO22989.AISystem", world_folder_name)

            if ai_system:
                # Set hasName property with human-readable name
                ai_system.hasName = [human_readable_name]
                print(f"✅ Created AISystem individual: {world_folder_name}")
                print(f"   hasName property set to: {human_readable_name}")

                # Create SystemDesign individual and link to AISystem via hasDesign
                # This is required for SWRL deployment pattern classification rules
                design_id = f"{world_folder_name}_design"
                system_design = self.create_individual_object("ISO22989.SystemDesign", design_id)
                if system_design:
                    ai_system.hasDesign = [system_design]
                    print(f"✅ Created SystemDesign individual: {design_id}")
                    print(f"   hasDesign linked: {world_folder_name} → {design_id}")
                else:
                    print(f"⚠️ Failed to create SystemDesign individual")

                # Save the ontology to persist the new individual
                self.save_ontology()
            else:
                print(f"❌ Failed to create AISystem individual")

        except Exception as e:
            print(f"❌ Error creating default AISystem: {e}")
            import traceback
            traceback.print_exc()

    def unload_ontologie(self):
        """Entfernt die aktuell geladene Ontologie aus der World, ohne die World selbst zu löschen."""
        try:
            if self.world and self.ontology:
                print("🧹 Entlade Ontologie...")

                # Entferne alle Entitäten (Klassen, Eigenschaften, Individuen)
                for entity in list(self.ontology.classes()) + list(self.ontology.properties()) + list(self.ontology.individuals()):
                    destroy_entity(entity)

                # Entferne die Ontologie aus der World
                if self.ontology in self.world.ontologies:
                    self.world.ontologies.remove(self.ontology)
                    print("✅ Ontologie aus der World entfernt.")

                # Lösche Referenz auf Ontologie
                self.ontology.destroy()
                self.ontology = None

                print("🗑️  Ontologie erfolgreich entfernt.")
            else:
                print("⚠️ Keine Ontologie geladen, die entfernt werden könnte.")

        except Exception as e:
            print(f"❌ Fehler beim Entladen der Ontologie: {e}")

    def unload_and_destroy_self(self):
        """
        Entfernt alle Ontologien und zerstört die World. Gibt alle Ressourcen frei.
        Bereitet die Instanz zur vollständigen Löschung vor.
        """
        try:
            if not self.world:
                print("⚠️ Keine aktive World vorhanden.")
            else:
                print("🌍 Entlade gesamte World mit allen Ontologien...")

                for iri, onto in list(self.world.ontologies.items()):
                    print(f"🧹 Entferne Ontologie: {iri}")
                    try:
                        for entity in list(onto.classes()) + list(onto.properties()) + list(onto.individuals()):
                            destroy_entity(entity)
                        onto.destroy()
                    except Exception as e:
                        print(f"⚠️ Fehler beim Entfernen der Ontologie {iri}: {e}")

            # Alles intern freigeben
            self.ontology = None
            self.main_ontology = None
            self.case_ontology = None
            self.world = None
            self.ontology_namespaces = None

            print("✅ Ressourcen wurden freigegeben. Instanz ist nun löschbar.")

        except Exception as e:
            print(f"❌ Fehler beim Entladen der World: {e}")



    def save_ontology_byteStream(self, format: str = "rdfxml"):
        """Speichert die aktuelle Ontologie in einen ByteStream.

        Args:
            format (str, optional): Das Speicherformat. Standard ist 'rdfxml'.
                                    Andere mögliche Formate: 'ntriples', 'turtle', 'json-ld'.
        """
        if self.ontology is None:
            print("Fehler: Keine Ontologie geladen.")
            return None
        
        try:
            # Erstelle einen BytesIO-Stream, um die Ontologie in den Arbeitsspeicher zu speichern
            byte_stream = io.BytesIO()

            # Speichere die Ontologie in den ByteStream
            self.ontology.save(byte_stream, format=format)
            
            # Setze den Pointer des Streams zurück, damit er beim Parsen richtig gelesen wird
            byte_stream.seek(0)
            
            print(f"Ontologie erfolgreich in den Arbeitsspeicher im Format '{format}' gespeichert.")
            
            return byte_stream  # Rückgabe des ByteStreams

        except Exception as e:
            print(f"Fehler beim Speichern der Ontologie im ByteStream: {e}")
            return None
        
    def convert_to_rdflib(self, report: bool = False):
        g = Graph()
        onto_graph = self.ontology.world.as_rdflib_graph()
        for triple in onto_graph.triples((None, None, None)):
            g.add(triple)

        if report:
            for s, p, o in g.triples((None, None, None)):
                    print(f"{s} -- {p} --> {o}")
            
        return g


    def list_imported_classes(self):
        """Listet alle Klassen der Hauptontologie und ihrer Importe auf."""
        if self.ontology is None:
            print("Fehler: Keine Ontologie geladen.")
            return

        print(f" Hauptontologie: {self.ontology.base_iri}")
        print(" Enthaltene Klassen:")
        for cls in self.ontology.classes():
            print(f"  - {cls} (Namespace: {cls.namespace.base_iri})")

        # Alle importierten Ontologien durchgehen
        for imported_onto in self.ontology.imported_ontologies:
            print(f"\n Importierte Ontologie: {imported_onto.base_iri}")
            print("Enthaltene Klassen:")
            for cls in imported_onto.classes():
                print(f"  - {cls} (Namespace: {cls.namespace.base_iri})")

    def list_imported_object_properties(self):
        """Listet alle ObjectProperties der Hauptontologie und ihrer Importe auf."""
        if self.ontology is None:
            print("Fehler: Keine Ontologie geladen.")
            return

        print(f"Hauptontologie: {self.ontology.base_iri}")
        print("Enthaltene ObjectProperties:")
        for prop in self.ontology.object_properties():
            print(f"  - {prop} (Domain: {prop.domain}, Range: {prop.range})")

        # Alle importierten Ontologien durchgehen
        for imported_onto in self.ontology.imported_ontologies:
            print(f"\nImportierte Ontologie: {imported_onto.base_iri}")
            print("Enthaltene ObjectProperties:")
            for prop in imported_onto.object_properties():
                print(f"  - {prop} (Domain: {prop.domain}, Range: {prop.range})")

    def get_class_hierarchy(self):
        """Erstellt ein verschachteltes Dictionary aller Klassen und ihrer Subklassen, ohne doppelte Einträge."""
        if self.ontology is None:
            print("Fehler: Keine Ontologie geladen.")
            return None

        def build_hierarchy(cls, visited):
            """Rekursiv die Subklassen-Struktur aufbauen, ohne Duplikate."""
            if cls in visited:
                return {}  # Klasse wurde bereits hinzugefügt
            visited.add(cls)  # Klasse als besucht markieren

            sub_hierarchy = {}
            for sub in cls.subclasses():
                sub_hierarchy[sub.name] = build_hierarchy(sub, visited)
            return sub_hierarchy

        # Nur direkte Unterklassen von owl:Thing in die Hierarchie aufnehmen
        hierarchy = {}
        visited = set()

        for cls in self.ontology.classes():
            if not any(parent in self.ontology.classes() for parent in cls.is_a):  # Prüft, ob die Klasse keine Eltern hat
                hierarchy[cls.name] = build_hierarchy(cls, visited)

        return hierarchy
    
    def get_ontology(self):
        """Gibt die geladene Ontologie zurück."""
        if self.ontology is None:
            print("Warnung: Die Ontologie wurde noch nicht geladen.")
        return self.ontology
    
    def find_individual(self, individual_name: str):
        """Sucht ein Individuum mit dem angegebenen Namen und gibt es zurück."""
        if self.ontology is None:
            print("Fehler: Keine Ontologie geladen.")
            return None

        # First try to find in main ontology
        result = next((ind for ind in self.ontology.individuals() if ind.name == individual_name), None)
        if result:
            return result

        # If not found, search across all ontologies in the world
        for onto in self.world.ontologies.values():
            result = next((ind for ind in onto.individuals() if ind.name == individual_name), None)
            if result:
                return result

        return None
    
    def create_individual_object(self, class_name: str, individual_name: str):
        """Erstellt eine individuelle Instanz einer Klasse in der Ontologie, wenn die exakte Klasse existiert.

        Falls das Individuum bereits existiert, prüft ob Klassenänderung nötig ist und gibt es zurück.
        Dies ermöglicht das Aktualisieren von hasName, Klasse und anderen Properties ohne Neuanlage.

        Args:
            class_name: Can be either simple name (e.g., "Training") or namespace-qualified (e.g., "ISO22989.Training")
            individual_name: The name for the individual instance
        """
        if self.ontology is None:
            print("Fehler: Keine Ontologie geladen.")
            return None

        # Use get_class_by_name which handles both simple and namespace-qualified names
        # This ensures consistency with annotation mechanism
        ontology_class = self.get_class_by_name(class_name)

        if ontology_class is None:
            print(f"Fehler: Die Klasse '{class_name}' existiert nicht in der Ontologie.")
            return None

        # Prüfen, ob das Individuum bereits existiert
        existing_individual = self.find_individual(individual_name)
        if existing_individual is not None:
            # Check if class change is needed
            current_class_name = existing_individual.__class__.name
            target_class_name = ontology_class.name

            if current_class_name != target_class_name:
                print(f"🔄 Individual '{individual_name}' exists but class changed: {current_class_name} → {target_class_name}")

                # Change the individual's class by modifying is_a
                # Keep only Thing and restrictions, remove old class
                new_is_a = []
                for item in existing_individual.is_a:
                    # Keep Thing and any restrictions
                    if item == self.ontology.Thing or not hasattr(item, 'name'):
                        new_is_a.append(item)

                # Add new class
                new_is_a.append(ontology_class)
                existing_individual.is_a = new_is_a

                print(f"✅ Changed class of '{individual_name}' to {target_class_name}")
            else:
                print(f"ℹ️ Individual '{individual_name}' already exists with correct class")

            return existing_individual

        # Individuum erstellen
        # IMPORTANT: Create individual in AIAS namespace, not in the class's namespace
        # This ensures all individuals are saved when we save AIAS-instance.owl
        individual = ontology_class(individual_name, namespace=self.ontology)
        print(f"Individuum '{individual_name}' der Klasse '{ontology_class.name}' wurde erstellt.")
        return individual
    
    def delete_individual_object(self, individual_name: str):
        """Löscht ein Individuum mit dem angegebenen Namen aus der Ontologie."""
        individual = self.find_individual(individual_name)
        
        if individual is None:
            print(f"Fehler: Individuum '{individual_name}' existiert nicht in der Ontologie.")
            return
        
        destroy_entity(individual)
        print(f"Individuum '{individual_name}' wurde erfolgreich gelöscht.")

    def remove_individual_property(self, source_name: str, property_name: str, target_name: str):
        """Entfernt eine ObjectProperty zwischen zwei bestehenden Individuen."""
        if self.ontology is None:
            print("Fehler: Keine Ontologie geladen.")
            return

        source = self.find_individual(source_name)
        target = self.find_individual(target_name)

        if not source or not target:
            return  # Silently ignore if individuals don't exist

        try:
            if hasattr(source, property_name):
                current_value = getattr(source, property_name, None)
                if isinstance(current_value, list) and target in current_value:
                    current_value.remove(target)
                    print(f"🗑️ Removed '{property_name}' from {source_name} to {target_name}")
                elif current_value == target:
                    setattr(source, property_name, [])
                    print(f"🗑️ Cleared '{property_name}' from {source_name} to {target_name}")
        except Exception as e:
            print(f"⚠️ Error removing property '{property_name}': {e}")

    def create_individual_property(self, source_name: str, property_name: str, target_name: str):
        """Erstellt eine ObjectProperty zwischen zwei bestehenden Individuen."""
        if self.ontology is None:
            print("Fehler: Keine Ontologie geladen.")
            return

        source = self.find_individual(source_name)
        target = self.find_individual(target_name)

        if not source:
            print(f"Fehler: Quelle-Instanz '{source_name}' nicht gefunden.")
            return
        if not target:
            print(f"Fehler: Ziel-Instanz '{target_name}' nicht gefunden.")
            return

        try:
            # In owlready2, properties can be inherited from parent classes
            # We need to check if the property exists in the ontology
            # Find the property in the world
            property_obj = None
            for onto in self.world.ontologies.values():
                for prop in onto.properties():
                    if prop.name == property_name:
                        property_obj = prop
                        break
                if property_obj:
                    break

            if not property_obj:
                print(f"❌ Property '{property_name}' existiert nicht in der Ontologie.")
                return

            print(f"🔗 Setze Property '{property_name}' für {source.__class__.__name__} → {target.__class__.__name__}")

            # Get current property value (might be empty list or None)
            current_value = getattr(source, property_name, None)

            # If current value is a list, append
            if isinstance(current_value, list):
                if target not in current_value:  # Avoid duplicates
                    current_value.append(target)
                    print(f"   ✅ Added to existing list (now {len(current_value)} items)")
            elif current_value is None:
                # Property is empty, set as list with single item
                setattr(source, property_name, [target])
                print(f"   ✅ Created new list with 1 item")
            else:
                # Property has single value, convert to list or replace
                if current_value != target:  # Avoid duplicates
                    setattr(source, property_name, [current_value, target])
                    print(f"   ✅ Converted to list with 2 items")

            print(f"✅ Property '{property_name}' zwischen '{source_name}' und '{target_name}' erfolgreich gesetzt.")

        except Exception as e:
            print(f"❌ Fehler beim Setzen der Property '{property_name}': {e}")
            import traceback
            traceback.print_exc()
    
    def instantiate_nodes(self, json_data: dict, node_name_convention: str = None,  edge_name_convention: str = None):
        """Erstellt Instanzen in der Ontologie basierend auf den Knoten im JSON."""
        if self.ontology is None:
            print("Fehler: Keine Ontologie geladen.")
            return {}, {}  # Return empty dicts instead of None

        # Sammelt Elemente, die nicht in die Ontologie uebernommen werden konnten.
        # Die Aufrufer lesen diese Liste aus, um den Nutzer zu warnen: sonst
        # weicht das grafische Modell unbemerkt von der Ontologie ab.
        self.last_sync_warnings = []

        #ab hier werden nodes erstellt
        node_instances = {}  # Speichert die erstellten Individuen nach ID
        
        for node in json_data.get("nodes", []):
            node_id = node.get("id")
            node_type = node.get("type")
            node_name = node.get("name")
            
            # Weitere Node-Typen
            node_data = node.get("data", {})
            node_resourceType = node_data.get("resourceType")
            node_functionType = node_data.get("functionType")
            node_productType = node_data.get("productType")
            #print(f"{node_resourceType}, {node_functionType}, {node_productType}")

            # Namenskonvention
            match node_name_convention:
                case "type_name_id":
                    new_node_name = f"{node_type}_{node_name}_{node_id}"
                case "name":
                    new_node_name = f"{node_name}"
                case "type_name":
                    new_node_name = f"{node_type}_{node_name}"
                case "id_name":
                    new_node_name = f"{node_id}_{node_name}"
                case _:  # Standard-Fall
                    new_node_name = f"{node_id}"  
                    
            # Mapping von Node-Typ zu Ontologie-Klasse
            class_mapping = {
                "FunctionNode": "Function",
                "ProductNode": "Product",
                "ResourceNode": "Resource"
            }

            # Überprüfe alle Typen und wähle den ersten gültigen Wert
            ontology_class = None
            for possible_type in [node_resourceType, node_functionType, node_productType]:
                if possible_type is not None and possible_type != "undefined":
                    ontology_class = possible_type
                    break  # Sobald ein gültiger Wert gefunden wurde, abbrechen

            # Falls kein gültiger Wert gefunden wurde, Fallback auf Mapping
            if ontology_class is None:
                ontology_class = class_mapping.get(node_type, "Unknown")

            # Erstellung des Individuums in der Ontologie
            individual = self.create_individual_object(ontology_class, new_node_name)

            if individual:
                # Store the display name using hasName property
                display_name = node_data.get("name")
                if display_name:
                    individual.hasName = [display_name]

                node_instances[node_id] = individual
            else:
                print(f"Fehler beim Erstellen von {ontology_class}:{new_node_name}")
                self.last_sync_warnings.append({
                    "kind": "node",
                    "id": node_id,
                    "name": node_data.get("name") or node_id,
                    "ontology_class": ontology_class,
                    "message": (f"Der Knoten '{node_data.get('name') or node_id}' konnte nicht "
                                f"angelegt werden: Die Klasse '{ontology_class}' ist in der "
                                f"Ontologie nicht bekannt."),
                })

        ## ab hier werden edges nodes erstellt
        edge_node_instances = {}
        
        for edge in json_data.get("edges", []):
            edge_id = edge.get("id")
            edge_type = edge.get("type")

            # Weitere Edge Node-Typen
            edge_data = edge.get("data", {})
            edge_communicationType= edge_data.get("communicationType")

            match edge_name_convention:
                case "type_id":
                    new_edge_name = f"{edge_type}_{edge_id}"
                case _:  # Default-Fall (wenn name_convention nicht angegeben oder ungültig ist)
                    new_edge_name = f"{edge_id}"  # Standardmäßige Namenskonvention

            class_mapping = {
                "AssignmentEdge": "Assignment",
                "FlowEdge": "Flow",
                "CommunicationEdge": "Communication"
            }
            # Überprüfe alle Typen und wähle den ersten gültigen Wert
            ontology_class = None
            if edge_communicationType is not None and edge_communicationType != "undefined":
                ontology_class = edge_communicationType

            # Falls kein gültiger Wert gefunden wurde, Fallback auf Mapping
            if ontology_class is None:
                ontology_class = class_mapping.get(edge_type, "Unknown")

            # Erstellung des Individuums in der Ontologie
            individual = self.create_individual_object(ontology_class, new_edge_name)

            if individual:
                # Store the display name using hasName property
                edge_display_name = edge_data.get("name")
                if edge_display_name:
                    individual.hasName = [edge_display_name]

                edge_node_instances[edge_id] = individual
            else:
                print(f"Fehler beim Erstellen von {ontology_class}:{new_edge_name}")
                self.last_sync_warnings.append({
                    "kind": "edge",
                    "id": edge_id,
                    "name": edge_data.get("name") or edge_id,
                    "ontology_class": ontology_class,
                    "message": (f"Die Kante '{edge_id}' konnte nicht angelegt werden: Die Klasse "
                                f"'{ontology_class}' ist in der Ontologie nicht bekannt."),
                })

        return node_instances, edge_node_instances
    
    def instantiate_properties(self, json_data: dict, node_instances: dict, edge_instances: dict):
        """
        Erstellt die Beziehungen zwischen den Instanzen basierend auf den Kanten im JSON.

        Für Flow und Communication Kanten wird die Richtung (arrowForward/arrowBackward) berücksichtigt:

        Flow edges:
        - Bidirectional (both arrows): hasFlow (both directions)
        - Forward only: hasOutput (source) + hasInput (target)
        - Backward only: hasInput (source) + hasOutput (target)

        Communication edges:
        - Bidirectional (both arrows): hasCommunication (both directions)
        - Forward only: hasOutputCommunication (source) + hasInputCommunication (target)
        - Backward only: hasInputCommunication (source) + hasOutputCommunication (target)
        """
        if self.ontology is None:
            print("Fehler: Keine Ontologie geladen.")
            return

        # Wird normalerweise von instantiate_nodes gesetzt; hier nur absichern,
        # falls diese Methode einmal allein aufgerufen wird.
        if not hasattr(self, "last_sync_warnings"):
            self.last_sync_warnings = []

        properties_added = []  # Liste zum Speichern der hinzugefügten Properties

        for edge in json_data.get("edges", []):
            edge_id = edge.get("id")
            source_id = edge.get("source")
            target_id = edge.get("target")
            edge_data = edge.get("data", {})

            edge_instance_id = edge_instances.get(edge_id)
            source_instance = node_instances.get(source_id)
            target_instance = node_instances.get(target_id)

            if not edge_instance_id or not source_instance or not target_instance:
                print(f"Fehler: Quelle ({source_id}), Ziel ({target_id}) oder Kante ({edge_id}) nicht gefunden.")
                # Ohne diese Meldung bliebe die Verbindung nur im grafischen Modell
                # bestehen und fehlte in der Ontologie - der Unterschied faellt sonst
                # erst in der Graphansicht auf.
                fehlend = [bez for bez, inst in (("Quelle", source_instance),
                                                 ("Ziel", target_instance),
                                                 ("Kante", edge_instance_id)) if not inst]
                self.last_sync_warnings.append({
                    "kind": "relation",
                    "id": edge_id,
                    "source": source_id,
                    "target": target_id,
                    "message": (f"Die Verbindung '{edge_id}' wurde nicht in die Ontologie "
                                f"uebernommen, weil {' und '.join(fehlend)} nicht angelegt "
                                f"werden konnte(n)."),
                })
                continue

            edge_type = edge.get("type")

            # Handle Assignment edges (no direction concept)
            if edge_type == "AssignmentEdge":
                property_name = "isAssignedTo"
                self.create_individual_property(source_instance.name, property_name, edge_instance_id.name)
                self.create_individual_property(target_instance.name, property_name, edge_instance_id.name)
                properties_added.append((source_instance.name, property_name, edge_instance_id.name))
                properties_added.append((target_instance.name, property_name, edge_instance_id.name))
                print(f"Beziehung {property_name} zwischen {source_instance.name} und {target_instance.name} gesetzt.")

            # Handle Flow edges with direction
            elif edge_type == "FlowEdge":
                arrow_forward = edge_data.get("arrowForward", False)
                arrow_backward = edge_data.get("arrowBackward", True)  # Default: backward arrow

                # FIRST: Clear ALL existing directional properties for this edge
                for prop in ['hasFlow', 'hasInput', 'hasOutput']:
                    self.remove_individual_property(source_instance.name, prop, edge_instance_id.name)
                    self.remove_individual_property(target_instance.name, prop, edge_instance_id.name)

                # THEN: Set the correct properties based on arrow direction
                if arrow_forward and arrow_backward:
                    # Bidirectional: use hasFlow for both
                    self.create_individual_property(source_instance.name, "hasFlow", edge_instance_id.name)
                    self.create_individual_property(target_instance.name, "hasFlow", edge_instance_id.name)
                    properties_added.append((source_instance.name, "hasFlow", edge_instance_id.name))
                    properties_added.append((target_instance.name, "hasFlow", edge_instance_id.name))
                    print(f"Bidirektionaler Flow: {source_instance.name} <-hasFlow-> {edge_instance_id.name} <-hasFlow-> {target_instance.name}")

                elif arrow_forward and not arrow_backward:
                    # Forward only: source hasOutput, target hasInput
                    self.create_individual_property(source_instance.name, "hasOutput", edge_instance_id.name)
                    self.create_individual_property(target_instance.name, "hasInput", edge_instance_id.name)
                    properties_added.append((source_instance.name, "hasOutput", edge_instance_id.name))
                    properties_added.append((target_instance.name, "hasInput", edge_instance_id.name))
                    print(f"Unidirektionaler Flow (→): {source_instance.name} -hasOutput-> {edge_instance_id.name} <-hasInput- {target_instance.name}")

                elif arrow_backward and not arrow_forward:
                    # Backward only: source hasInput, target hasOutput
                    self.create_individual_property(source_instance.name, "hasInput", edge_instance_id.name)
                    self.create_individual_property(target_instance.name, "hasOutput", edge_instance_id.name)
                    properties_added.append((source_instance.name, "hasInput", edge_instance_id.name))
                    properties_added.append((target_instance.name, "hasOutput", edge_instance_id.name))
                    print(f"Unidirektionaler Flow (←): {source_instance.name} -hasInput-> {edge_instance_id.name} <-hasOutput- {target_instance.name}")

                else:
                    # No arrows (shouldn't happen, but fallback to bidirectional)
                    self.create_individual_property(source_instance.name, "hasFlow", edge_instance_id.name)
                    self.create_individual_property(target_instance.name, "hasFlow", edge_instance_id.name)
                    properties_added.append((source_instance.name, "hasFlow", edge_instance_id.name))
                    properties_added.append((target_instance.name, "hasFlow", edge_instance_id.name))
                    print(f"⚠️ Flow ohne Pfeile (Fallback bidirektional): {source_instance.name} <-hasFlow-> {edge_instance_id.name}")

            # Handle Communication edges with direction
            elif edge_type == "CommunicationEdge":
                arrow_forward = edge_data.get("arrowForward", False)
                arrow_backward = edge_data.get("arrowBackward", True)  # Default: backward arrow

                # FIRST: Clear ALL existing directional properties for this edge
                for prop in ['hasCommunication', 'hasInputCommunication', 'hasOutputCommunication']:
                    self.remove_individual_property(source_instance.name, prop, edge_instance_id.name)
                    self.remove_individual_property(target_instance.name, prop, edge_instance_id.name)

                # THEN: Set the correct properties based on arrow direction
                if arrow_forward and arrow_backward:
                    # Bidirectional: use hasCommunication for both
                    self.create_individual_property(source_instance.name, "hasCommunication", edge_instance_id.name)
                    self.create_individual_property(target_instance.name, "hasCommunication", edge_instance_id.name)
                    properties_added.append((source_instance.name, "hasCommunication", edge_instance_id.name))
                    properties_added.append((target_instance.name, "hasCommunication", edge_instance_id.name))
                    print(f"Bidirektionale Communication: {source_instance.name} <-hasCommunication-> {edge_instance_id.name} <-hasCommunication-> {target_instance.name}")

                elif arrow_forward and not arrow_backward:
                    # Forward only: source hasOutputCommunication, target hasInputCommunication
                    self.create_individual_property(source_instance.name, "hasOutputCommunication", edge_instance_id.name)
                    self.create_individual_property(target_instance.name, "hasInputCommunication", edge_instance_id.name)
                    properties_added.append((source_instance.name, "hasOutputCommunication", edge_instance_id.name))
                    properties_added.append((target_instance.name, "hasInputCommunication", edge_instance_id.name))
                    print(f"Unidirektionale Communication (→): {source_instance.name} -hasOutputCommunication-> {edge_instance_id.name} <-hasInputCommunication- {target_instance.name}")

                elif arrow_backward and not arrow_forward:
                    # Backward only: source hasInputCommunication, target hasOutputCommunication
                    self.create_individual_property(source_instance.name, "hasInputCommunication", edge_instance_id.name)
                    self.create_individual_property(target_instance.name, "hasOutputCommunication", edge_instance_id.name)
                    properties_added.append((source_instance.name, "hasInputCommunication", edge_instance_id.name))
                    properties_added.append((target_instance.name, "hasOutputCommunication", edge_instance_id.name))
                    print(f"Unidirektionale Communication (←): {source_instance.name} -hasInputCommunication-> {edge_instance_id.name} <-hasOutputCommunication- {target_instance.name}")

                else:
                    # No arrows (shouldn't happen, but fallback to bidirectional)
                    self.create_individual_property(source_instance.name, "hasCommunication", edge_instance_id.name)
                    self.create_individual_property(target_instance.name, "hasCommunication", edge_instance_id.name)
                    properties_added.append((source_instance.name, "hasCommunication", edge_instance_id.name))
                    properties_added.append((target_instance.name, "hasCommunication", edge_instance_id.name))
                    print(f"⚠️ Communication ohne Pfeile (Fallback bidirektional): {source_instance.name} <-hasCommunication-> {edge_instance_id.name}")

            else:
                print(f"Unbekannter Kanten-Typ: {edge_type}")

        return properties_added  # Rückgabe der hinzugefügten Properties

    # === Helper Methods for Annotation Manager === #

    def get_class_by_name(self, class_name: str):
        """
        Get OWL class by fully qualified name.

        Args:
            class_name: Name like "ISO22989.Training" or "Training"

        Returns:
            OWL class or None
        """
        if self.ontology is None:
            print("⚠️ Keine Ontologie geladen.")
            return None

        try:
            # Check if class_name contains a namespace
            if '.' in class_name:
                namespace_name, local_name = class_name.rsplit('.', 1)

                # Try to get the namespace from the world
                for onto_iri, onto in self.world.ontologies.items():
                    if onto.name == namespace_name or namespace_name in onto_iri:
                        # Search in this ontology
                        for cls in onto.classes():
                            if cls.name == local_name:
                                return cls

            # Try without namespace - search all classes
            for cls in self.ontology.classes():
                if cls.name == class_name:
                    return cls

            # Also search in world
            for onto in self.world.ontologies.values():
                for cls in onto.classes():
                    if cls.name == class_name:
                        return cls

        except Exception as e:
            print(f"❌ Error in get_class_by_name: {e}")

        return None

    def _get_class_full_name(self, owl_class) -> str:
        """
        Get the namespace-qualified name of an OWL class.

        Args:
            owl_class: OWL class object

        Returns:
            Namespace-qualified name like "ISO22989.Training" or just "Training" if no namespace
        """
        if not owl_class:
            return ""

        try:
            # Get the class name
            class_name = owl_class.name

            # Get the ontology this class belongs to
            if hasattr(owl_class, 'namespace') and owl_class.namespace:
                onto = owl_class.namespace.ontology

                # Get ontology name/prefix
                if hasattr(onto, 'name') and onto.name:
                    onto_name = onto.name

                    # Skip anonymous or instance ontology names
                    if onto_name and onto_name not in ['', 'AIAS-instance']:
                        # Check if it's one of our known ODPs
                        if onto_name in ['ISO22989', 'ISO7489', 'VDI3682']:
                            return f"{onto_name}.{class_name}"
                        # For AIAS base ontology
                        elif onto_name == 'AIAS':
                            return class_name

            # Fallback: just return the class name
            return class_name

        except Exception as e:
            print(f"⚠️ Error getting full class name: {e}")
            return owl_class.name if hasattr(owl_class, 'name') else ""

    def get_property_by_name(self, property_name: str):
        """
        Get OWL property by name.

        Args:
            property_name: Property name

        Returns:
            OWL property or None
        """
        if self.ontology is None:
            print("⚠️ Keine Ontologie geladen.")
            return None

        try:
            # Check object properties in world
            for prop in self.world.object_properties():
                if prop.name == property_name:
                    return prop

            # Check data properties in world
            for prop in self.world.data_properties():
                if prop.name == property_name:
                    return prop

        except Exception as e:
            print(f"❌ Error in get_property_by_name: {e}")

        return None

    def get_individual_by_name(self, individual_name: str):
        """
        Get OWL individual by name.

        Args:
            individual_name: Individual name

        Returns:
            OWL individual or None
        """
        if self.ontology is None:
            print("⚠️ Keine Ontologie geladen.")
            return None

        try:
            # Search in current ontology
            for individual in self.ontology.individuals():
                if individual.name == individual_name:
                    return individual

            # Also search in all ontologies in the world
            for onto in self.world.ontologies.values():
                for individual in onto.individuals():
                    if individual.name == individual_name:
                        return individual

        except Exception as e:
            print(f"❌ Error in get_individual_by_name: {e}")

        return None

    def save_ontology(self, file_path: str = None, name: str = None, format: str = "rdfxml"):
        """
        Save ontology to file.

        Default behavior (no parameters): Saves to AIAS-instance.owl (working copy).
        Custom export: Provide file_path and name for debugging/export purposes.

        IMPORTANT: Never saves to AIAS.owl (schema) - only to AIAS-instance.owl or custom paths.

        Args:
            file_path: Optional directory path for custom export (if None, saves to AIAS-instance.owl)
            name: Optional filename (without extension) for custom export
            format: File format (default: "rdfxml"). Options: 'rdfxml', 'ntriples', 'turtle', 'json-ld'
        """
        if self.ontology is None:
            print("⚠️ Keine Ontologie geladen.")
            return

        try:
            if file_path and name:
                # Custom export path provided (for debugging/export)
                full_path = os.path.join(file_path, f"{name}.{format}")
                self.ontology.save(file=full_path, format=format)
                print(f"✅ Ontologie gespeichert: {full_path}")
            elif file_path and not name:
                # Only file_path provided (assume it's a complete file path)
                self.ontology.save(file=file_path, format=format)
                print(f"✅ Ontologie gespeichert: {file_path}")
            else:
                # Default: Save to working copy (AIAS-instance.owl)
                self.ontology.save(file=self.instance_path, format="rdfxml")
                print(f"✅ Ontologie gespeichert: {INSTANCE_ONTO_FILE}")
        except Exception as e:
            print(f"❌ Error saving ontology: {e}")

    def clear_all_individuals(self):
        """
        Delete all individuals (instances) from the ontology.
        Keeps the class definitions, only removes instances.
        This is useful when starting a new modeling session.
        """
        if self.ontology is None:
            print("⚠️ Keine Ontologie geladen.")
            return 0

        try:
            from owlready2 import destroy_entity

            # Get all individuals before deletion
            individuals = list(self.ontology.individuals())
            count = len(individuals)

            print(f"🗑️ Deleting {count} individuals from ontology...")

            # Delete each individual
            with self.ontology:
                for individual in individuals:
                    print(f"   Deleting: {individual.name} ({individual.__class__.__name__})")
                    # In owlready2, use destroy_entity() to delete individuals
                    destroy_entity(individual)

            print(f"✅ Deleted {count} individuals")
            return count

        except Exception as e:
            print(f"❌ Error clearing individuals: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def clear_graphical_elements(self, keep_ids=None):
        """
        Delete graphical element individuals (nodes and edges) that are NOT in the keep list.

        Args:
            keep_ids: Set/list of individual IDs to preserve (from incoming model).
                     If None or empty, ALL graphical elements are deleted.

        Annotations are ALWAYS preserved (they're not graphical elements).
        This allows intentional deletion of nodes even if they have annotations.
        """
        if self.ontology is None:
            print("⚠️ Keine Ontologie geladen.")
            return 0

        # Convert to set for O(1) lookup
        keep_ids = set(keep_ids) if keep_ids else set()

        try:
            from owlready2 import destroy_entity

            # Define graphical element base class names
            # These are the classes that represent nodes and edges in the graphical model
            graphical_base_classes = {
                'Function', 'Product', 'Resource',  # Node types
                'Assignment', 'Flow', 'Communication',  # Edge types
            }

            # Get all individuals and check their direct class name
            individuals_to_delete = []
            individuals_to_preserve = []

            for individual in self.ontology.individuals():
                # Check if this individual's class (or any ancestor) matches a graphical base class
                # We check ancestors to catch specialized classes like Inference, Training, Controller, etc.
                is_graphical = False
                for ancestor in individual.__class__.ancestors():
                    if hasattr(ancestor, 'name') and ancestor.name in graphical_base_classes:
                        is_graphical = True
                        break

                if is_graphical:
                    # Check if this individual is in the keep list (from incoming model)
                    if individual.name in keep_ids:
                        individuals_to_preserve.append(individual)
                        # print(f"📌 Preserving: {individual.name} (in incoming model)")
                    else:
                        individuals_to_delete.append(individual)

            count = len(individuals_to_delete)
            preserved_count = len(individuals_to_preserve)

            if count > 0:
                print(f"🗑️ Clearing {count} graphical elements (preserving {preserved_count})...")

            # Delete graphical elements not in the keep list
            with self.ontology:
                for individual in individuals_to_delete:
                    print(f"   Deleting: {individual.name} ({individual.__class__.__name__})")
                    destroy_entity(individual)

            if count > 0 or preserved_count > 0:
                print(f"✅ Cleared {count} graphical elements ({preserved_count} preserved)")
            return count

        except Exception as e:
            print(f"❌ Error clearing graphical elements: {e}")
            import traceback
            traceback.print_exc()
            return 0

    # === Dual Ontology Management Methods === #

    def clear_graph_visualizations(self):
        """
        Delete all graph visualization HTML files.
        This is useful when starting a new session to ensure old graphs don't persist.

        Returns:
            int: Number of files deleted
        """
        try:
            from . import path_utils
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            TEMPLATES_DIR = path_utils.get_relative_path(BASE_DIR, "..", "..", "templates")

            graph_files = [
                "ontology_graph_instance.html",
                "ontology_graph_inferred.html",
                "ontology_graph.html"  # Old legacy file
            ]

            deleted_count = 0
            for filename in graph_files:
                filepath = os.path.join(TEMPLATES_DIR, filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"🗑️ Deleted graph visualization: {filename}")
                    deleted_count += 1

            if deleted_count > 0:
                print(f"✅ Cleared {deleted_count} graph visualization file(s)")
            else:
                print("ℹ️ No graph visualizations to clear")

            return deleted_count

        except Exception as e:
            print(f"❌ Error clearing graph visualizations: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def clear_inferred_ontology(self):
        """
        Delete the inferred ontology file (AIAS-inferred.owl) and its graph visualization.
        This is called when the user model changes, making reasoning results outdated.

        Returns:
            bool: True if file was deleted, False if file didn't exist
        """
        try:
            ontology_deleted = False
            if os.path.exists(self.inferred_path):
                os.remove(self.inferred_path)
                print(f"🗑️ Cleared inferred ontology: {INFERRED_ONTO_FILE}")
                ontology_deleted = True
            else:
                print(f"ℹ️ No inferred ontology to clear (file doesn't exist)")

            # Also delete the inferred graph HTML visualization
            from . import path_utils
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            TEMPLATES_DIR = path_utils.get_relative_path(BASE_DIR, "..", "..", "templates")
            inferred_graph_path = os.path.join(TEMPLATES_DIR, "ontology_graph_inferred.html")

            if os.path.exists(inferred_graph_path):
                os.remove(inferred_graph_path)
                print(f"🗑️ Cleared inferred graph visualization")

            return ontology_deleted

        except Exception as e:
            print(f"❌ Error clearing inferred ontology: {e}")
            import traceback
            traceback.print_exc()
            return False

    def prepare_for_reasoning(self):
        """
        Copy AIAS-instance.owl → AIAS-inferred.owl before running reasoning.
        This preserves the user model while allowing reasoning to add inferences.

        Returns:
            bool: True if copy was successful, False otherwise
        """
        try:
            if not os.path.exists(self.instance_path):
                print(f"❌ Cannot prepare for reasoning: {INSTANCE_ONTO_FILE} does not exist")
                return False

            print(f"📋 Copying {INSTANCE_ONTO_FILE} → {INFERRED_ONTO_FILE}")
            shutil.copy2(self.instance_path, self.inferred_path)
            print(f"✅ Inferred ontology prepared for reasoning")
            return True

        except Exception as e:
            print(f"❌ Error preparing for reasoning: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load_inferred_ontology(self):
        """
        Load the inferred ontology (AIAS-inferred.owl) for reasoning operations.
        Creates a new World and loads the inferred ontology into it.

        This replaces the current ontology in memory with the inferred version.

        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.inferred_path):
                print(f"⚠️ Inferred ontology does not exist: {INFERRED_ONTO_FILE}")
                return False

            # Clear existing ontology if loaded
            if self.ontology:
                self.unload_ontologie()

            # Setup paths
            onto_path.clear()
            onto_path.append(self.odp_path)  # Add ODP path

            # Create new World and load inferred ontology
            self.world = World()
            self.ontology = self.world.get_ontology(self.inferred_path).load()

            print(f"✅ Inferred ontology loaded: {INFERRED_ONTO_FILE}")

            # Show contained ontologies
            print("📦 Contained ontologies in this World:")
            for onto in self.world.ontologies.values():
                print(f"   - {onto.base_iri}")

            self.ontology_namespaces = self.world.ontologies.keys()
            print(f"🌐 Imported namespaces: {self.ontology_namespaces}")

            return True

        except Exception as e:
            print(f"❌ Error loading inferred ontology: {e}")
            import traceback
            traceback.print_exc()
            return False

    def save_inferred_ontology(self):
        """
        Save the current ontology to AIAS-inferred.owl.
        This should be called after reasoning to persist the inferences.

        Returns:
            bool: True if saved successfully, False otherwise
        """
        if self.ontology is None:
            print("⚠️ No ontology loaded to save")
            return False

        try:
            self.ontology.save(file=self.inferred_path, format="rdfxml")
            print(f"✅ Inferred ontology saved: {INFERRED_ONTO_FILE}")
            return True
        except Exception as e:
            print(f"❌ Error saving inferred ontology: {e}")
            import traceback
            traceback.print_exc()
            return False

    def inferred_ontology_exists(self):
        """
        Check if the inferred ontology file exists.

        Returns:
            bool: True if AIAS-inferred.owl exists, False otherwise
        """
        return os.path.exists(self.inferred_path)

