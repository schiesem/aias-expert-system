import os

# Nur Verzeichnis             -> _dir
# Nur Nur Dateiname           -> _file
# Kompletter Pfad zur Datei   -> _path

def get_relative_path(BASE_DIR, *path_parts):
    """
    Erzeugt einen Pfad relativ zum Projekt-Basisverzeichnis.
    
    Beispiel:
        get_project_path("config", "settings.json")
        ➝ /dein/projekt/config/settings.json
    """
    return os.path.join(BASE_DIR, *path_parts)