import React, { useEffect, useState } from "react";
import ReactFlow, { Background, MiniMap, useReactFlow } from "reactflow";
import "reactflow/dist/style.css";
import "./App.css";

import { useStore } from "./store";

import FunctionNode from "./components/nodes/FunctionNode";
import ProductNode from "./components/nodes/ProductNode";
import ResourceNode from "./components/nodes/ResourceNode";

import AssignmentEdge from "./components/edges/AssignmentEdge";
import FlowEdge from "./components/edges/FlowEdge";
import CommunicationEdge from "./components/edges/CommunicationEdge";

import CreatePanel from "./components/panels/CreatePanel";
import ElementPanel from "./components/panels/ElementPanel";
import StoragePanel from "./components/panels/StoragePanel";
import ExpertSystemPanel from "./components/panels/ExpertSystemPanel";
import AnnotationWindow from "./components/panels/AnnotationWindow";
import GraphVisualizationModal from "./components/modals/GraphVisualizationModal";
import LoadingScreen from "./components/LoadingScreen";
import NavigationBar from "./components/NavigationBar";

import { syncModelToOntology } from "./utils/annotationUtils";

const selector = (store) => ({
  nodes: store.nodes,
  edges: store.edges,
  onNodesChange: store.onNodesChange,
  onEdgesChange: store.onEdgesChange,
  createEdge: store.createEdge,
  createNode: store.createNode,
  deleteHandle: store.onDeleteHandle,
  onValidConnection: store.onValidConnection,
  updateEdge: store.updateEdge,
  annotationElement: store.annotationElement,
  openAnnotationWindow: store.openAnnotationWindow,
  closeAnnotationWindow: store.closeAnnotationWindow,
  initializeFromBackend: store.initializeFromBackend,
  annotationRefreshCounter: store.annotationRefreshCounter,
  refreshAnnotationCounts: store.refreshAnnotationCounts,
  serverConfig: store.serverConfig,
  routes: store.routes,
  ontoConfig: store.ontoConfig,
  functionTyps: store.functionTyps,
  setServerConfig: store.setServerConfig,
  createBackendRoutes: store.createBackendRoutes,
  setOntoConfig: store.setOntoConfig,
  updateStore: store.updateStore,
  showMiniMap: store.showMiniMap,
});

const nodeTypes = {
  FunctionNode: FunctionNode,
  ProductNode: ProductNode,
  ResourceNode: ResourceNode,
};

const edgeTypes = {
  AssignmentEdge: AssignmentEdge,
  FlowEdge: FlowEdge,
  CommunicationEdge: CommunicationEdge,
};

function App() {
  const store = useStore(selector);
  const { setViewport, screenToFlowPosition } = useReactFlow();
  const [showGraphModal, setShowGraphModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [loadingMessage, setLoadingMessage] = useState("Initializing...");
  const [worldSelectorOpen, setWorldSelectorOpen] = useState(false);
  const [expertSystemOpen, setExpertSystemOpen] = useState(false);

  // Coordinated initialization sequence
  useEffect(() => {
    const initializeEverything = async () => {
      try {
        setIsLoading(true);

        // Step 1: Load server configuration
        setLoadingMessage("Loading server configuration...");
        if (!store.serverConfig) {
          const { fetchData } = await import('./utils/httpUtils');
          await fetchData({
            url: "http://127.0.0.1:5000/configData",
            setFunction: store.setServerConfig,
          });
        }
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Step 2: Create backend routes
        setLoadingMessage("Creating backend routes...");
        let routes = store.routes;
        if (!routes) {
          routes = await store.createBackendRoutes();
          store.updateStore("routes", routes);
        }
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Step 3: Load class types from ontology
        setLoadingMessage("Loading class types from ontology...");
        if (routes) {
          try {
            // Fetch function types
            const functionResponse = await fetch(`${routes.MODEL_CLASS_TYPES}?category=function`);
            const functionData = await functionResponse.json();

            // Fetch resource types
            const resourceResponse = await fetch(`${routes.MODEL_CLASS_TYPES}?category=resource`);
            const resourceData = await resourceResponse.json();

            // Fetch communication types
            const communicationResponse = await fetch(`${routes.MODEL_CLASS_TYPES}?category=communication`);
            const communicationData = await communicationResponse.json();

            // Convert to the format expected by the dropdowns (including descriptions)
            if (functionData.success && functionData.classes) {
              const functionTypes = functionData.classes.map(cls => ({
                functionType: cls.name,  // Use namespace-qualified name (e.g., "ISO22989.Training")
                displayName: cls.display_name,
                description: cls.description,
                namespace: cls.namespace
              }));
              store.updateStore("functionTyps", functionTypes);
            }

            if (resourceData.success && resourceData.classes) {
              const resourceTypes = resourceData.classes.map(cls => ({
                resourceType: cls.name,
                displayName: cls.display_name,
                description: cls.description,
                namespace: cls.namespace
              }));
              store.updateStore("resourceTyps", resourceTypes);
            }

            if (communicationData.success && communicationData.classes) {
              const communicationTypes = communicationData.classes.map(cls => ({
                communicationType: cls.name,
                displayName: cls.display_name,
                description: cls.description,
                namespace: cls.namespace
              }));
              store.updateStore("communicationTyps", communicationTypes);
            }
          } catch (error) {
            console.error("Error loading class types:", error);
          }
        }
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Step 4: Load model from backend
        setLoadingMessage("Loading model from backend...");
        const model = await store.initializeFromBackend();

        if (model && model.viewport) {
          setViewport(model.viewport);
        }
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Step 5: Finalize
        setLoadingMessage("Finalizing...");
        await new Promise(resolve => setTimeout(resolve, 1000));

        console.log('✅ Initialization complete');
        setIsLoading(false);
      } catch (error) {
        console.error('❌ Error during initialization:', error);
        setLoadingMessage("Error loading. Please refresh the page.");
        // Still hide loading screen after error
        setTimeout(() => setIsLoading(false), 2000);
      }
    };

    initializeEverything();
  }, []); // Empty dependency array = run once on mount

  // Handle double-click on nodes to open annotation window
  const handleNodeDoubleClick = (event, node) => {
    // Extract class name based on node type
    let className = 'Unknown';

    if (node.type === 'FunctionNode') {
      className = node.data?.functionType || 'Unknown';
    } else if (node.type === 'ResourceNode') {
      className = node.data?.resourceType || 'Unknown';
    } else if (node.type === 'ProductNode') {
      // ProductNode might not have a specific class, use a default or the name
      className = node.data?.productType || node.data?.name || 'Product';
    }

    // Create element object with necessary data
    const element = {
      id: node.id,
      type: node.type,
      class: className,
      label: node.data?.name || node.id
    };
    store.openAnnotationWindow(element);
  };

  // Handle double-click on edges to open annotation window
  const handleEdgeDoubleClick = (event, edge) => {
    // Extract class name based on edge type
    let className = 'Unknown';

    if (edge.type === 'CommunicationEdge') {
      className = 'Communication';
    } else if (edge.type === 'AssignmentEdge') {
      className = 'Assignment';
    } else if (edge.type === 'FlowEdge') {
      className = 'Flow';
    }

    // Create element object with necessary data
    const element = {
      id: edge.id,
      type: edge.type,
      class: className,
      label: edge.data?.name || edge.id
    };
    store.openAnnotationWindow(element);
  };

  // Handle right-click on edges to add waypoint
  const handleEdgeContextMenu = (event, edge) => {
    console.log('🎯 Edge context menu triggered in App.jsx!', event, edge);
    event.preventDefault();

    // Get flow position from screen coordinates
    const flowPosition = screenToFlowPosition({
      x: event.clientX,
      y: event.clientY,
    });

    console.log('📍 Adding waypoint at:', flowPosition);

    // Add waypoint to edge
    const existingWaypoints = edge.data?.waypoints || [];
    const newWaypoints = [...existingWaypoints, flowPosition];

    console.log('✅ Waypoint added to edge:', edge.id, 'Total waypoints:', newWaypoints.length);

    store.updateEdge(edge.id, {
      waypoints: newWaypoints,
    });
  };

  // Handle manual save - sync model to backend and create instance graph
  // This is an ADDITIONAL save option - automatic saving still works as before
  const handleSaveModel = async () => {
    try {
      setLoadingMessage("Saving model to ontology...");
      setIsLoading(true);

      // Sync model to backend (creates instance graph)
      const result = await syncModelToOntology(store.nodes, store.edges);

      // Elemente, die nicht in die Ontologie übernommen wurden, melden:
      // sonst weicht das grafische Modell unbemerkt von der Ontologie ab.
      const warnings = result?.warnings || [];
      if (warnings.length > 0) {
        const details = warnings.map((w) => `• ${w.message}`).join("\n");
        alert(
          `Das Modell wurde gespeichert, aber ${warnings.length} Element(e) ` +
          `konnten nicht in die Ontologie übernommen werden:\n\n${details}\n\n` +
          `Diese Elemente fehlen in der Graphansicht und bei der Auswertung.`
        );
      }

      console.log("✅ Model saved successfully");
    } catch (error) {
      console.error("❌ Failed to save model:", error);
      alert(`Failed to save model: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const isDataLoaded = store.serverConfig && store.routes && store.functionTyps && store.functionTyps.length > 0;

  return (
    <>
      {/* Loading screen as overlay when initializing */}
      {isLoading && <LoadingScreen message={loadingMessage} />}

      {/* Navigation Bar */}
      <NavigationBar
        onOpenWorldSelector={() => setWorldSelectorOpen(true)}
        onOpenExpertSystem={() => {
          if (isDataLoaded) {
            setExpertSystemOpen(true);
          }
        }}
        onOpenGraphVisualization={() => setShowGraphModal(true)}
        onSaveModel={handleSaveModel}
        isExpertSystemReady={isDataLoaded}
      />

      <ReactFlow
        nodes={store.nodes}
        edges={store.edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodesChange={store.onNodesChange}
        onEdgesChange={store.onEdgesChange}
        onNodesDelete={store.deleteHandle}
        onConnect={store.createEdge}
        onNodeDoubleClick={handleNodeDoubleClick}
        onEdgeDoubleClick={handleEdgeDoubleClick}
        onEdgeContextMenu={handleEdgeContextMenu}
        onPaneContextMenu={(e) => e.preventDefault()}
        elementsSelectable={true}
        isValidConnection={store.onValidConnection}
        connectionMode={"loose"}
      >
        <Background />
        {store.showMiniMap && (
          <MiniMap
            nodeColor={(node) => {
              switch (node.type) {
                case 'FunctionNode':
                  return '#d9f99d';
                case 'ProductNode':
                  return '#fecdd3';
                case 'ResourceNode':
                  return '#bae6fd';
                default:
                  return '#e5e7eb';
              }
            }}
            nodeStrokeWidth={3}
            zoomable
            pannable
          />
        )}
        <CreatePanel />
        <ElementPanel />
        <ExpertSystemPanel
          isOpen={expertSystemOpen}
          onOpenChange={setExpertSystemOpen}
        />
        <StoragePanel
          isOpen={worldSelectorOpen}
          onOpenChange={setWorldSelectorOpen}
        />
      </ReactFlow>

      {/* Annotation Window Modal */}
      {store.annotationElement && (
        <AnnotationWindow
          element={store.annotationElement}
          onClose={store.closeAnnotationWindow}
        />
      )}

      {/* Graph Visualization Modal */}
      <GraphVisualizationModal
        isOpen={showGraphModal}
        onClose={() => setShowGraphModal(false)}
      />
    </>
  );
}

export default App;
