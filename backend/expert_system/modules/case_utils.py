# expert_system/modules/graph_similarity.py
from rdflib import Graph


#####################################################

def get_class_instance_summary(graph: Graph) -> list[dict]:
    """
    Gibt eine Liste aller OWL-Klassen mit mindestens einer Instanz in der Ontologie zurück.
    Für jede Klasse: Anzahl Instanzen + Liste der URIs.
    """
    query = """
    SELECT ?class (COUNT(?instance) AS ?count)
    WHERE {
        ?instance a ?class .
        FILTER(isIRI(?class))
    }
    GROUP BY ?class
    ORDER BY DESC(?count)
    """

    summary = []

    try:
        results = graph.query(query)

        for row in results:
            class_uri = str(row[0])
            count = int(row[1])

            # Nur wenn es wirklich Instanzen gibt
            if count > 0:
                instance_query = f"""
                SELECT ?instance WHERE {{
                    ?instance a <{class_uri}> .
                }}
                """
                instances = [
                    str(r[0]) for r in graph.query(instance_query)
                ]

                summary.append({
                    "class": class_uri,
                    "count": count,
                    "instances": instances
                })

        if summary:            
            for entry in summary:
                print(f"📦 Klasse: {entry['class']}")
                print(f"🔢 Anzahl Instanzen: {entry['count']}")
                for inst in entry['instances']:
                    print(f"  🔹 {inst}")
                print("-" * 30)

    except Exception as e:
        print(f"❌ Fehler bei SPARQL-Abfrage: {e}")

    return summary

def query_instances_of(graph, class_uri):
    query = f"""
    SELECT ?instance WHERE {{
        ?instance a <{class_uri}> .
    }}
    """
    return [str(row.instance) for row in graph.query(query)]

def query_relations(graph, subject_class, predicate_uri, object_class):
    query = f"""
    SELECT ?subject ?object WHERE {{
        ?subject a <{subject_class}> .
        ?object a <{object_class}> .
        ?subject <{predicate_uri}> ?object .
    }}
    """
    return [{"subject": str(row.subject), "object": str(row.object)} for row in graph.query(query)]

def compare_class_counts(graph1, graph2, class_uri):
    """Vergleicht, ob zwei Graphen die gleiche Anzahl an Instanzen haben"""

    count1 = len(query_instances_of(graph1, class_uri))
    count2 = len(query_instances_of(graph2, class_uri))

    if count1 > 0 and count2 > 0:
        quotient = count1 / count2
        return {
            "comparement": compare_class_counts.__doc__,
            "class_uri": class_uri,
            "eq_value": quotient,
            "count1": count1,
            "count2": count2,
        }
    else:
        return {
            "comparement": compare_class_counts.__doc__,
            "class_uri": class_uri,
            "eq_value": "undefined",
            "count1": count1,
            "count2": count2,
        }