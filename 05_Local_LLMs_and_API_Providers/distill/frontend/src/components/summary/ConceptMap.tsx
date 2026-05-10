import { useEffect, useRef } from "react";
import Box from "@cloudscape-design/components/box";

interface Props {
  mermaidSyntax: string;
}

export default function ConceptMap({ mermaidSyntax }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  // Track render errors so the component can show a fallback gracefully
  const hasError = useRef(false);

  useEffect(() => {
    if (!mermaidSyntax || !containerRef.current) return;

    const render = async () => {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: "base",
          themeVariables: {
            primaryColor: "#0972d3",
            primaryTextColor: "#ffffff",
            primaryBorderColor: "#0972d3",
            lineColor: "#414d5c",
            background: "#ffffff",
          },
        });

        // Use a timestamped id to avoid conflicts when re-rendering
        const id = `mermaid-${Date.now()}`;
        const { svg } = await mermaid.render(id, mermaidSyntax);
        if (containerRef.current) {
          containerRef.current.innerHTML = svg;
          hasError.current = false;
        }
      } catch {
        // On parse error fall back to displaying the raw syntax
        hasError.current = true;
        if (containerRef.current) {
          containerRef.current.innerHTML = `<pre style="font-size:12px;overflow:auto">${mermaidSyntax}</pre>`;
        }
      }
    };

    render();
  }, [mermaidSyntax]);

  return (
    <Box>
      <div
        ref={containerRef}
        style={{
          minHeight: "200px",
          overflow: "auto",
          display: "flex",
          justifyContent: "center",
          padding: "16px",
        }}
      />
    </Box>
  );
}
