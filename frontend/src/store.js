import { applyNodeChanges, applyEdgeChanges } from "reactflow";
import { nanoid } from "nanoid";

import { createWithEqualityFn } from "zustand/traditional";
import { shallow } from "zustand/shallow";

import {
  FUNCTION_NODE_ATTR,
  FUNCTION_NODE_DATA,
  RESOURCE_NODE_ATTR,
  RESOURCE_NODE_DATA,
  PRODUCT_NODE_ATTR,
  PRODUCT_NODE_DATA,
  COMMUNICATION_EDGE_ATTR,
  COMMUNICATION_EDGE_DATA,
  ASSIGNMENT_EDGE_ATTR,
  ASSIGNMENT_EDGE_DATA,
  PRODUCTFLOW_EDGE_ATTR,
  PRODUCTFLOW_EDGE_DATA,
  FUNCTIONTYPS,
  TECHNICALRESOURCESTYPS,
  COMMUNICATIONTYPS,
} from "./defaultElementsConfig";

import {
  connectionValidator,
  connectionClassifier,
} from "./utils/connectionUtils";

import { syncModelToOntology } from "./utils/annotationUtils";

const idLength = 6;

// Debounce tracking to prevent duplicate syncs
let syncInProgress = false;
let pendingSync = null;

/**
 * Synchronize model to ontology with debouncing to prevent race conditions.
 * Only called for structural changes (create/delete/update data).
 * NOT called for cosmetic changes (position, selection).
 */
async function syncToOntology(nodes, edges) {
  // If a sync is already in progress, queue this request
  if (syncInProgress) {
    console.log('⏸️ Sync already in progress, queuing...');
    pendingSync = { nodes, edges };
    return;
  }

  try {
    syncInProgress = true;
    console.log('🔄 Syncing to ontology...');
    await syncModelToOntology(nodes, edges);
    console.log('✅ Sync completed');
  } catch (error) {
    console.error('❌ Failed to sync model:', error);
    // Don't throw - sync failures shouldn't break the UI
  } finally {
    syncInProgress = false;

    // If there's a pending sync, execute it now
    if (pendingSync) {
      const { nodes: pendingNodes, edges: pendingEdges } = pendingSync;
      pendingSync = null;
      console.log('▶️ Executing queued sync...');
      syncToOntology(pendingNodes, pendingEdges);
    }
  }
}

/**
 * Create 4 fixed handles for a node (top, right, bottom, left).
 * Each handle is both source and target (type="source" allows both in ReactFlow).
 */
function createFixedHandles(nodeId) {
  return [
    {
      nodeId: nodeId,
      id: `${nodeId}-top`,
      type: "source",
      position: "top",
      isConnectable: true,
    },
    {
      nodeId: nodeId,
      id: `${nodeId}-right`,
      type: "source",
      position: "right",
      isConnectable: true,
    },
    {
      nodeId: nodeId,
      id: `${nodeId}-bottom`,
      type: "source",
      position: "bottom",
      isConnectable: true,
    },
    {
      nodeId: nodeId,
      id: `${nodeId}-left`,
      type: "source",
      position: "left",
      isConnectable: true,
    },
  ];
}

export const useStore = createWithEqualityFn(
  (set, get) => ({
      // Frontend Storage Handling
      nodes: [],
      edges: [],
      handles: [],
      // Annotation Window State
      annotationElement: null,
      annotationRefreshCounter: 0, // Incremented whenever annotations are created/deleted
      // Further Storage Handling
      serverURL: "http://127.0.0.1:5000/configData",
      routes: null,
      serverConfig: null,
      ontoConfig: null,
      caseData: null,
      ruleData: null,
      ontoData: null,
      consistencyData: {},
      notesData: {},
      functionTyps: FUNCTIONTYPS,
      resourceTyps: TECHNICALRESOURCESTYPS,
      communicationTyps: COMMUNICATIONTYPS,
      // Canvas Settings
      showEdgeLabels: true,
      showNodeId: true,
      showNodeType: true,
      showMiniMap: true,
      showAnchorPoints: true,
      showClassDefinitions: true,

      updateStore(key, value) {
        set({ [key]: value });
      },

      toggleEdgeLabels() {
        set((state) => ({ showEdgeLabels: !state.showEdgeLabels }));
      },

      toggleNodeId() {
        set((state) => ({ showNodeId: !state.showNodeId }));
      },

      toggleNodeType() {
        set((state) => ({ showNodeType: !state.showNodeType }));
      },

      toggleMiniMap() {
        set((state) => ({ showMiniMap: !state.showMiniMap }));
      },

      toggleAnchorPoints() {
        set((state) => ({ showAnchorPoints: !state.showAnchorPoints }));
      },

      toggleClassDefinitions() {
        set((state) => ({ showClassDefinitions: !state.showClassDefinitions }));
      },

      setServerConfig(data) {
        set({ serverConfig: data });
      },

      setOntoConfig(data) {
        set({ ontoConfig: data });
      },

      // Annotation Window Functions
      openAnnotationWindow(element) {
        set({ annotationElement: element });
      },

      closeAnnotationWindow() {
        set({ annotationElement: null });
      },
      // Trigger annotation count refresh in all nodes
      refreshAnnotationCounts() {
        set((state) => ({ annotationRefreshCounter: state.annotationRefreshCounter + 1 }));
      },

      // Create Server Routes
      createBackendRoutes: async () => {
        try {
          const { serverConfig } = get(); // serverConfig aus dem Zustand holen

          if (!serverConfig) {
            throw new Error("Server Config ist nicht verfügbar!");
          }

          const BASE_URL = `http://${serverConfig.ips.backend}:${serverConfig.ports.backend}`;

          const ROUTES = Object.freeze(
            Object.fromEntries(
              Object.entries(serverConfig.routes).map(([key, value]) => [
                key,
                `${BASE_URL}${value}`, // BASE_URL vor den relativen Pfad setzen
              ])
            )
          );

          return ROUTES; // Falls du die Routes später nutzen willst
        } catch (error) {
          console.error("Fehler beim Setzen der Backend Routes:", error);
          throw error; // Fehler weiterwerfen, falls nötig
        }
      },

      // Ontology Config Functions

      //node functions
      onNodesChange(changes) {
        // Check if any nodes are being removed (structural change)
        const removedNodeIds = changes
          .filter(change => change.type === 'remove')
          .map(change => change.id);

        const hasRemovals = removedNodeIds.length > 0;

        // Apply changes first to get updated nodes
        const updatedNodes = applyNodeChanges(changes, get().nodes);

        set({
          nodes: updatedNodes,
        });

        // Sync ONLY if nodes were removed (structural change)
        // Don't sync for position/selection changes
        if (hasRemovals) {
          console.log(`🗑️ Node(s) removed: ${removedNodeIds.join(', ')}`);

          // Filter out edges connected to removed nodes
          // (ReactFlow will remove them, but we need to sync before that happens)
          const cleanedEdges = get().edges.filter(edge =>
            !removedNodeIds.includes(edge.source) &&
            !removedNodeIds.includes(edge.target)
          );

          console.log(`   Also removing ${get().edges.length - cleanedEdges.length} connected edge(s)`);

          // IMPORTANT: Use updatedNodes (not get().nodes) to ensure we're syncing the latest state
          syncToOntology(updatedNodes, cleanedEdges);
        }
      },

      updateNode(id, data) {
        set({
          nodes: get().nodes.map((node) =>
            node.id === id ? { ...node, data: { ...node.data, ...data } } : node
          ),
        });
        // Sync to ontology after node data update (this is a structural change)
        syncToOntology(get().nodes, get().edges);
      },

      createNode(type) {
        const id = nanoid(idLength);
        const newHandles = createFixedHandles(id);

        switch (type) {
          case "FunctionNode": {
            const data = { ...FUNCTION_NODE_DATA };
            const position = { x: 0, y: 0 };
            set({
              nodes: [
                ...get().nodes,
                { id, ...FUNCTION_NODE_ATTR, data, position },
              ],
              handles: [...get().handles, ...newHandles],
            });
            break;
          }
          case "ProductNode": {
            const data = { ...PRODUCT_NODE_DATA };
            const position = { x: 0, y: 0 };
            set({
              nodes: [
                ...get().nodes,
                { id, ...PRODUCT_NODE_ATTR, data, position },
              ],
              handles: [...get().handles, ...newHandles],
            });
            break;
          }
          case "ResourceNode": {
            const data = { ...RESOURCE_NODE_DATA };
            const position = { x: 0, y: 0 };
            set({
              nodes: [
                ...get().nodes,
                { id, ...RESOURCE_NODE_ATTR, data, position },
              ],
              handles: [...get().handles, ...newHandles],
            });
            break;
          }
        }
        console.log(`✅ Created node ${id} with 4 fixed handles (top, right, bottom, left)`);
        // Sync to ontology after node creation (structural change)
        syncToOntology(get().nodes, get().edges);
      },

      //handles functions
      createHandle(nodeId, handleSide, type) {
        const handles = get().handles;

        // Überprüfen, ob die Node bereits einen Handle mit der gewünschten Position hat
        const handleExists = handles.some(
          (handle) => handle.nodeId === nodeId && handle.position === handleSide
        );

        if (handleExists) {
          console.log(
            `Ein Handle für ${handleSide} existiert bereits bei Node ${nodeId}`
          );
          return;
        }
        const handleId = nanoid(idLength);
        const createHandle = {
          nodeId: nodeId,
          id: handleId,
          type: type,
          position: handleSide,
          isConnectable: true,
        };

        set({
          handles: [createHandle, ...get().handles],
        });
      },

      onDeleteHandle(changes) {
        changes.forEach((change) => {
          let filteredHandles = get().handles.filter(
            (handle) => handle.nodeId !== change.id
          );
          set({ handles: [...filteredHandles] });
        });
      },

      updateHandlePos(handleId, pos) {
        set({
          handles: get().handles.map((handle) =>
            handle.id === handleId ? { ...handle, position: pos } : edge
          ),
        });
      },

      //edge functions
      onEdgesChange(changes) {
        // Check if any edges are being removed (structural change)
        const hasRemovals = changes.some(change => change.type === 'remove');

        set({
          edges: applyEdgeChanges(changes, get().edges),
        });

        // Sync ONLY if edges were removed (structural change)
        // Don't sync for selection changes
        if (hasRemovals) {
          console.log('🗑️ Edge(s) removed, syncing to ontology...');
          syncToOntology(get().nodes, get().edges);
        }
      },

      updateEdge(id, updates) {
        set({
          edges: get().edges.map((edge) => {
            if (edge.id === id) {
              // Separate handle updates from data updates
              const { sourceHandle, targetHandle, ...dataUpdates } = updates;

              const updatedEdge = { ...edge };

              // Apply handle updates at top level
              if (sourceHandle !== undefined) {
                updatedEdge.sourceHandle = sourceHandle;
              }
              if (targetHandle !== undefined) {
                updatedEdge.targetHandle = targetHandle;
              }

              // Apply all other updates to data
              if (Object.keys(dataUpdates).length > 0) {
                updatedEdge.data = { ...edge.data, ...dataUpdates };
              }

              return updatedEdge;
            }
            return edge;
          }),
        });
        // Sync to ontology after edge update (this is a structural change)
        syncToOntology(get().nodes, get().edges);
      },

      createEdge(changes) {
        const id = nanoid(idLength);
        // getting target and source nodeIds and classes
        const targetNodeId = changes.target;
        const sourceNodeId = changes.source;
        const targetNodeType = get().nodes.find(
          (node) => node.id === targetNodeId
        ).type;
        const sourceNodeType = get().nodes.find(
          (node) => node.id === sourceNodeId
        ).type;
        // getting connection type
        const type = connectionClassifier(sourceNodeType, targetNodeType);
        let data = {};
        let attr = {};

        switch (type) {
          case "CommunicationEdge":
            data = { ...COMMUNICATION_EDGE_DATA };
            attr = { ...COMMUNICATION_EDGE_ATTR };
            break;
          case "AssignmentEdge":
            attr = { ...ASSIGNMENT_EDGE_ATTR };
            data = { ...ASSIGNMENT_EDGE_DATA };
            break;
          case "FlowEdge":
            attr = { ...PRODUCTFLOW_EDGE_ATTR };
            data = { ...PRODUCTFLOW_EDGE_DATA };
            break;
          default:
            console.log("No known Type fore Creating an Edge");
        }

        // creating data object
        const createdEdge = {
          id,
          ...attr,
          ...changes,
          data,
          zIndex: 1000, // Edges appear above nodes (nodes default to zIndex 1)
        };
        // creating the new edge
        set({
          edges: [createdEdge, ...get().edges],
        });
        // Sync to ontology after edge creation (structural change)
        syncToOntology(get().nodes, get().edges);
      },

      onValidConnection(connection) {
        const targetNodeId = connection.target;
        const sourceNodeId = connection.source;
        const targetNodeType = get().nodes.find(
          (node) => node.id === targetNodeId
        ).type;
        const sourceNodeType = get().nodes.find(
          (node) => node.id === sourceNodeId
        ).type;

        return connectionValidator(targetNodeType, sourceNodeType);
      },

      //general element functions
      getActiveElementId() {
        const elements = [...get().edges, ...get().nodes];
        const activeElement = elements.find(
          (element) => element.selected === true
        );
        return activeElement ? activeElement.id : undefined;
      },

      getElementDataById(id) {
        const elements = [...get().edges, ...get().nodes];
        const elementData = elements.find((element) => element.id === id);
        return elementData;
      },

      exportStore() {
        const state = get();
        const saveData = JSON.stringify({
          nodes: state.nodes,
          edges: state.edges,
          handles: state.handles,
          serverConfig: state.serverConfig,
          ontoConfig: state.ontoConfig,
          functionTyps: state.functionTyps,
          resourceTyps: state.resourceTyps,
          communicationTyps: state.communicationTyps,
        });

        const blob = new Blob([saveData], { type: "application/json" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "diagram.json";
        link.click();
      },

      importStore(file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          const parsedData = JSON.parse(event.target.result);
          set({
            nodes: parsedData.nodes || [],
            edges: parsedData.edges || [],
            handles: parsedData.handles || [],
            serverConfig: parsedData.serverConfig || [],
            ontoConfig: parsedData.ontoConfig || [],
            functionTyps: parsedData.functionTyps || [],
            resourceTyps: parsedData.resourceTyps || [],
            communicationTyps: parsedData.communicationTyps || [],
          });
          console.log("Store aus Datei geladen!");
        };
        reader.readAsText(file);
      },

      // Initialize store from backend (load model on mount)
      initializeFromBackend: async () => {
        try {
          const { loadModelFromBackend } = await import('./utils/annotationUtils');
          const model = await loadModelFromBackend();

          console.log('📦 Received from backend:', {
            nodes: model.nodes?.length,
            edges: model.edges?.length
          });

          // With floating handles, we can set nodes and edges together
          // No timing issues since handles are not position-specific
          set({
            nodes: model.nodes || [],
            edges: model.edges || []
          });
          console.log('✅ Nodes and edges set (using floating handles)');

          console.log('✅ Store initialized from backend');
          return model;
        } catch (error) {
          console.error('❌ Failed to initialize from backend:', error);
          // Don't throw - allow empty initialization
          return null;
        }
      },
    }),
  shallow
);
