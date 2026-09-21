import { Panel } from "reactflow";
import { useStore } from "../../store";
import { Card, CardHeader, CardContent } from "../ui";
import { EmptyState } from "../ui";
import { getElementIcon } from "../../utils/styleUtils";

import FunctionNodePanel from "./FunctionNodePanel";
import ProductNodePanel from "./ProductNodePanel";
import ResourceNodePanel from "./ResourceNodePanel";
import AssignmentEdgePanel from "./AssignmentEdgePanel";
import CommunicationEdgePanel from "./CommunicationEdgePanel";
import ProductFlowEdgePanel from "./ProductFlowEdgePanel";
import "./ElementPanel.css";

const selector = (store) => ({
  nodes: store.nodes,
  edges: store.edges,
  getActiveElementId: store.getActiveElementId,
  getElementDataById: store.getElementDataById,
  showEdgeLabels: store.showEdgeLabels,
  toggleEdgeLabels: store.toggleEdgeLabels,
  showNodeId: store.showNodeId,
  toggleNodeId: store.toggleNodeId,
  showNodeType: store.showNodeType,
  toggleNodeType: store.toggleNodeType,
  showMiniMap: store.showMiniMap,
  toggleMiniMap: store.toggleMiniMap,
  showAnchorPoints: store.showAnchorPoints,
  toggleAnchorPoints: store.toggleAnchorPoints,
  showClassDefinitions: store.showClassDefinitions,
  toggleClassDefinitions: store.toggleClassDefinitions,
});

const elementPanelSelector = (elementTyp) => {
  if (elementTyp != undefined) {
    switch (elementTyp) {
      case "FunctionNode":
        return <FunctionNodePanel />;
      case "ProductNode":
        return <ProductNodePanel />;
      case "ResourceNode":
        return <ResourceNodePanel />;
      case "AssignmentEdge":
        return <AssignmentEdgePanel />;
      case "CommunicationEdge":
        return <CommunicationEdgePanel />;
      case "FlowEdge":
        return <ProductFlowEdgePanel />;
      default:
        return null;
    }
  } else {
    return null;
  }
};

export default function ElementPanel() {
  const store = useStore(selector);
  const activeElementId = store.getActiveElementId();
  const activeElementType =
    activeElementId && store.getElementDataById(activeElementId).type;

  return (
    <Panel position="top-right">
      <Card variant="panel" className="element-panel">
        <CardHeader
          title="Element Configuration"
        />
        <CardContent>
          {activeElementType ? (
            elementPanelSelector(activeElementType)
          ) : (
            <>
              <EmptyState
                message="Select a node or edge to configure"
                submessage="Click on any element in the canvas"
              />

              <hr style={{ margin: "16px 0", borderColor: "#e5e7eb" }} />

              <div>
                <p className="text-sm font-medium mb-3">Canvas Settings</p>
                <div className="flex flex-col gap-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={store.showEdgeLabels}
                      onChange={store.toggleEdgeLabels}
                      className="w-4 h-4"
                    />
                    <span className="text-sm">Show Edge Labels</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={store.showNodeId}
                      onChange={store.toggleNodeId}
                      className="w-4 h-4"
                    />
                    <span className="text-sm">Show Node ID</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={store.showNodeType}
                      onChange={store.toggleNodeType}
                      className="w-4 h-4"
                    />
                    <span className="text-sm">Show Node Type</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={store.showMiniMap}
                      onChange={store.toggleMiniMap}
                      className="w-4 h-4"
                    />
                    <span className="text-sm">Show MiniMap</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={store.showAnchorPoints}
                      onChange={store.toggleAnchorPoints}
                      className="w-4 h-4"
                    />
                    <span className="text-sm">Show Anchor Points</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={store.showClassDefinitions}
                      onChange={store.toggleClassDefinitions}
                      className="w-4 h-4"
                    />
                    <span className="text-sm">Show Class Definitions</span>
                  </label>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </Panel>
  );
}
