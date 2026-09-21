# data_store.py
class DataStore:
    def __init__(self):
        self._data = {}
    
    def update(self, new_data):
        if not isinstance(new_data, dict):
            raise ValueError("Fehler: Erwartetes Format ist ein Dictionary!")
        self._data.update(new_data)

    def append(self, key, value):
        if key not in self._data:
            self._data[key] = []
        if not isinstance(self._data[key], list):
            raise ValueError(f"Fehler: {key} ist keine Liste!")
        self._data[key].append(value)

    def get(self):
        return self._data.copy()

    def clear(self):
        self._data = {}

# Globale Stores
data_store = DataStore()
onto_config_store = DataStore()
rule_store = DataStore()
cases_store = DataStore()