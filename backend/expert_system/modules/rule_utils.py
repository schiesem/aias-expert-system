from typing import List, Dict
import re

def load_swrl_rules_from_file(file_path):
    """Lädt SWRL-Regeln aus einer Textdatei."""
    with open(file_path, 'r') as file:
        return file.readlines()
    
def parse_reasoner_output(output_log: List[str]) -> Dict[str, List[str] | float]:
    parsed_output = {
        "AddRelation": [],
        "Reparenting": [],
        "Equivalenting": [],
        "ReasonningTime": None,
        "Further": []  # Alles, was nicht zugeordnet werden kann
    }

    for entry in output_log:
        if entry.startswith("Equivalenting:"):
            parsed_output["Equivalenting"].append(entry[len("Equivalenting:"):].strip())
        elif entry.startswith("Reparenting:"):
            parsed_output["Reparenting"].append(entry[len("Reparenting:"):].strip())
        elif entry.startswith("AddRelation:"):
            parsed_output["AddRelation"].append(entry[len("AddRelation:"):].strip())
        elif "Pellet Reasonner took" in entry:
            try:
                time_str = entry.split("Pellet Reasonner took")[1].split("seconds")[0].strip()
                parsed_output["ReasonningTime"] = float(time_str)
            except (IndexError, ValueError):
                parsed_output["Further"].append(entry)
        else:
            parsed_output["Further"].append(entry)

    return parsed_output

def expand_swrl_rules(swrl_rules, namespaces):
    expanded_rules = []

    # Regex sucht nach Prefix:Element
    pattern = re.compile(r'(\b\w+):([\w\d]+)')

    for rule in swrl_rules:
        # Cleanup von Anführungszeichen und überflüssigem Whitespace
        cleaned_rule = rule.strip().strip('"').strip()

        def replace_prefix(match):
            prefix = match.group(1)
            local_name = match.group(2)
            if prefix in namespaces:
                return f"{namespaces[prefix]}{local_name}"
            else:
                return match.group(0)  # keine Änderung, wenn Prefix nicht gefunden

        # Regel umschreiben
        expanded = pattern.sub(replace_prefix, cleaned_rule)
        expanded_rules.append(expanded)

    return expanded_rules

def build_swrl_namespace_dict(namespaces):
    ns_dict = {}

    for ns in namespaces:
        if ns.endswith('.owl#') or ns.endswith('.owl'):
            # Datei abschneiden
            workdir = ns.rsplit('\\', 1)[0]
            ns_dict["LOCAL"] = workdir
            continue  # nicht in den Rest übernehmen

        key = ns.rstrip('#').split('/')[-1]
        if not key:  # z. B. 'http://anonymous/'
            key = 'anonymous'

        # stelle sicher, dass # am Ende hängt
        if not ns.endswith('#'):
            ns += '#'

        ns_dict[key] = ns

    return ns_dict