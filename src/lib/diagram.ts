/**
 * Convert an Excalidraw scene to a compact text description the LLM can reason about.
 * We list shapes (with their text labels) and arrows between shapes.
 */

interface ExEl {
  id: string;
  type: string;
  x: number;
  y: number;
  width?: number;
  height?: number;
  text?: string;
  containerId?: string | null;
  startBinding?: { elementId: string } | null;
  endBinding?: { elementId: string } | null;
  groupIds?: string[];
  isDeleted?: boolean;
}

export function diagramToText(scene: unknown): string {
  if (!scene || typeof scene !== "object") return "(no diagram drawn yet)";
  const elements = (scene as { elements?: ExEl[] }).elements ?? [];
  if (!Array.isArray(elements) || elements.length === 0) return "(no diagram drawn yet)";

  const live = elements.filter((e) => !e.isDeleted);

  // text-bearing shapes: rectangle/diamond/ellipse/text. Build label map by id.
  const textLabels = new Map<string, string>();
  for (const el of live) {
    if (el.type === "text" && el.text) {
      const owner = el.containerId || el.id;
      const existing = textLabels.get(owner);
      textLabels.set(owner, existing ? `${existing} ${el.text}`.trim() : el.text.trim());
    } else if (el.text) {
      textLabels.set(el.id, el.text.trim());
    }
  }

  const shapeIds = new Set<string>();
  const shapeLines: string[] = [];
  for (const el of live) {
    if (["rectangle", "diamond", "ellipse"].includes(el.type)) {
      shapeIds.add(el.id);
      const label = textLabels.get(el.id) || "(unlabeled)";
      shapeLines.push(`- ${cap(el.type)} "${label}"`);
    }
  }
  // standalone text not bound to a shape becomes a "Note"
  for (const el of live) {
    if (el.type === "text" && !el.containerId) {
      shapeLines.push(`- Note "${(el.text || "").trim()}"`);
    }
  }

  const arrowLines: string[] = [];
  for (const el of live) {
    if (el.type === "arrow" || el.type === "line") {
      const from =
        (el.startBinding && textLabels.get(el.startBinding.elementId)) || "?";
      const to = (el.endBinding && textLabels.get(el.endBinding.elementId)) || "?";
      const label = textLabels.get(el.id);
      arrowLines.push(
        `- ${from} → ${to}${label ? ` (label: "${label}")` : ""}`,
      );
    }
  }

  const parts: string[] = [];
  if (shapeLines.length) parts.push("Components:\n" + shapeLines.join("\n"));
  if (arrowLines.length) parts.push("Connections:\n" + arrowLines.join("\n"));
  return parts.length ? parts.join("\n\n") : "(diagram has elements but no recognizable shapes)";
}

function cap(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
