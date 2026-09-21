# Frontend

React-Oberfläche des AIAS-Modellierungswerkzeugs. Die Modellierungsfläche ist
mit ReactFlow umgesetzt, die Zustandsverwaltung mit Zustand.

Installation und Start sind im [README des Projekts](../README.md#installation)
beschrieben. Kurzfassung:

```bash
npm install
npm run dev
```

Die Anwendung läuft dann auf `http://127.0.0.1:5173` und erwartet das Backend
auf `http://127.0.0.1:5000`.

## Aufbau

```
src/
  App.jsx                 Wurzelkomponente, lädt Klassendefinitionen vom Backend
  store.js                Zustand-Store für Knoten, Kanten und Auswahl
  defaultElementsConfig.js  Vorgaben für die Elementtypen
  components/
    nodes/                Function-, Product- und Resource-Knoten
    edges/                Assignment-, Flow- und Communication-Kanten
    panels/               Bedienpanels (Erstellen, Konfigurieren, Welten,
                          Expertensystem, Annotationen)
    modals/               Graphansicht
    ui/                   Wiederverwendbare Bedienelemente
  utils/                  API-Aufrufe, Verbindungsprüfung, Kantengeometrie
```
