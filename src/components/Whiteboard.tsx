"use client";

import "@excalidraw/excalidraw/index.css";
import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef } from "react";

// Excalidraw is client-only; load it lazily.
const Excalidraw = dynamic(
  async () => (await import("@excalidraw/excalidraw")).Excalidraw,
  { ssr: false, loading: () => <div className="p-4 text-sm text-text-mute">Loading whiteboard…</div> },
);

// We treat the Excalidraw API and scene as opaque to keep our own code untyped.
// Using `any` here is a deliberate boundary at a 3rd-party React component.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ExcalidrawAPI = any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Scene = any;

export interface WhiteboardHandle {
  getScene: () => Scene | null;
}

export default function Whiteboard({
  initialScene,
  onChange,
  apiRef,
}: {
  initialScene: Scene | null;
  onChange?: (scene: Scene) => void;
  apiRef: React.RefObject<WhiteboardHandle | null>;
}) {
  const excalidrawRef = useRef<ExcalidrawAPI | null>(null);

  useEffect(() => {
    apiRef.current = {
      getScene: () => {
        if (!excalidrawRef.current) return null;
        return {
          elements: [...excalidrawRef.current.getSceneElements()],
          appState: { ...excalidrawRef.current.getAppState() },
        };
      },
    };
  }, [apiRef]);

  const handleChange = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (elements: readonly any[], appState: any) => {
      onChange?.({ elements: [...elements], appState });
    },
    [onChange],
  );

  return (
    <div className="excalidraw-host h-full w-full">
      <Excalidraw
        excalidrawAPI={(api: ExcalidrawAPI) => {
          excalidrawRef.current = api;
        }}
        initialData={initialScene ?? undefined}
        onChange={handleChange}
        theme="dark"
        UIOptions={{
          canvasActions: {
            saveToActiveFile: false,
            loadScene: false,
            export: false,
            saveAsImage: false,
          },
        }}
      />
    </div>
  );
}
