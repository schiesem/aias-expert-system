import { Panel } from "reactflow";
import { Card, CardHeader, CardContent } from "../ui";
import CreateButton from "./panelElements/CreateButton";
import "./CreatePanel.css";

export default function CreatePanel() {
  return (
    <Panel position="top-left">
      <Card variant="panel" className="create-panel">
        <CardHeader
          title="Create Elements"
        />
        <CardContent>
          <div className="create-grid">
            <CreateButton
              nodeType="FunctionNode"
              color="#d9f99d"
            >
              Function
            </CreateButton>
            <CreateButton
              nodeType="ProductNode"
              color="#fecdd3"
            >
              Product
            </CreateButton>
            <CreateButton
              nodeType="ResourceNode"
              color="#bae6fd"
            >
              Resource
            </CreateButton>
          </div>
        </CardContent>
      </Card>
    </Panel>
  );
}
