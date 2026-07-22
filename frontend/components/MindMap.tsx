"use client";

import { useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  type Edge,
  type Node,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import type { MindmapResponse, NodeType } from "@/lib/types";

const NODE_COLORS: Record<NodeType, string> = {
  goal: "#4FD1C5",
  plan: "#F2B84B",
  task: "#8B9DFF",
  topic: "#EDEEF2",
  note_ref: "#4A5065",
};

export default function MindMap({
  mindmap,
  onNodeClick,
}: {
  mindmap: MindmapResponse;
  onNodeClick?: (nodeId: string) => void;
}) {
  const { nodes, edges } = useMemo<{ nodes: Node[]; edges: Edge[] }>(() => {
    const flowNodes: Node[] = mindmap.nodes.map((n) => ({
      id: n.id,
      position: { x: n.position_x, y: n.position_y },
      data: { label: n.label },
      style: {
        background: "#171A22",
        color: "#EDEEF2",
        border: `1.5px solid ${NODE_COLORS[n.type]}`,
        borderRadius: 12,
        padding: "8px 14px",
        fontSize: 13,
        fontFamily: "Inter, sans-serif",
      },
    }));

    // parent/child structure from mindmap_nodes.parent_id
    const treeEdges: Edge[] = mindmap.nodes
      .filter((n) => n.parent_id)
      .map((n) => ({
        id: `tree-${n.parent_id}-${n.id}`,
        source: n.parent_id as string,
        target: n.id,
        style: { stroke: "#232733" },
      }));

    // cross-links from mindmap_edges (e.g. "depends_on")
    const relationEdges: Edge[] = mindmap.edges.map((e) => ({
      id: e.id,
      source: e.source_node_id,
      target: e.target_node_id,
      label: e.relationship_type,
      animated: true,
      style: { stroke: "#4FD1C5" },
      labelStyle: { fill: "#4FD1C5", fontSize: 10 },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#4FD1C5" },
    }));

    return { nodes: flowNodes, edges: [...treeEdges, ...relationEdges] };
  }, [mindmap]);

  return (
    <div className="h-[600px] w-full overflow-hidden rounded-2xl bg-ink-900">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeClick={(_, node) => onNodeClick?.(node.id)}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#232733" gap={20} />
        <Controls className="!bg-ink-800 !text-paper" />
      </ReactFlow>
    </div>
  );
}
