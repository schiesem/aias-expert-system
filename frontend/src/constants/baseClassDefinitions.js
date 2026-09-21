/**
 * baseClassDefinitions.js
 *
 * Definitions for the base AIAS classes from the ontologies.
 * These are displayed under the "Type" label in Element Config Panels.
 */

export const BASE_CLASS_DEFINITIONS = {
  // AIAS:Function - for FunctionNode
  function: `Eine Function beschreibt das Verhalten eines Systems oder einer Komponente, also was das System tut oder leisten soll, unabhängig von seiner konkreten Realisierung.

**Quelle:** Haberfellner, Systems Engineering`,

  // AIAS:Resource (equivalent to VDI3682:TechnicalRessource) - for ResourceNode
  resource: `Eine Resource ist eine technische Komponente, die physische oder virtuelle Mittel zur Ausführung von Funktionen bereitstellt. Sie ist äquivalent zur TechnicalRessource aus VDI 3682.

**Quelle:** Dissertation Schieseck`,

  // VDI3682:Product - for ProductNode
  product: `Ein Product sind Dinge der realen Welt, die im Rahmen eines technischen Prozesses umgewandelt werden.

**Quelle (Norm):** VDI 3682, Kapitel 4.1, Seite 8`,

  // ISO7489:Communication - for CommunicationEdge
  communication: `Eine Communication ist eine Verbindung zwischen mindestens zwei Systemkomponenten, die den gerichteten Austausch von Daten beschreibt.

**Quelle (Norm):** ISO/IEC 7498, Definition 4.2.10`,

  // VDI3682:Assignment - for AssignmentEdge
  assignment: `Ein Assignment ist eine strukturelle Verbindung zwischen Prozessoperator und technischer Ressource, über die einer Ressource die Ausführung eines Prozessoperators zugewiesen wird.

**Quelle (Norm):** VDI 3682, Kapitel 4.2`,

  // VDI3682:Flow - for ProductFlowEdge
  flow: `Ein Flow ist eine gerichtete Verbindung von Produkten zwischen Prozessoperatoren.

**Quelle (Norm):** VDI 3682, Kapitel 4.1, Seite 8`,
};

export default BASE_CLASS_DEFINITIONS;
