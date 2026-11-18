import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/** Renders AI replies (markdown, including tables) inside narrow panels. */
export function Markdown({ children }: { children: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        table: ({ children }) => (
          <div className="my-2 overflow-x-auto">
            <table className="w-full border-collapse text-xs">{children}</table>
          </div>
        ),
        th: ({ children }) => (
          <th className="border border-slate-200 bg-slate-100 px-2 py-1 text-left font-semibold">{children}</th>
        ),
        td: ({ children }) => <td className="border border-slate-200 px-2 py-1 align-top">{children}</td>,
        a: ({ href, children }) => (
          <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-700 underline">
            {children}
          </a>
        ),
        ul: ({ children }) => <ul className="my-1 list-disc space-y-1 pl-5">{children}</ul>,
        ol: ({ children }) => <ol className="my-1 list-decimal space-y-1 pl-5">{children}</ol>,
        p: ({ children }) => <p className="my-1">{children}</p>,
      }}
    >
      {children}
    </ReactMarkdown>
  );
}

/** One line of markdown (quiz questions and options): `code` and **bold**, without block margins. */
export function InlineMarkdown({ children }: { children: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => <span>{children}</span>,
        code: ({ children }) => (
          <code className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[0.9em]">{children}</code>
        ),
        pre: ({ children }) => <pre className="my-1 overflow-x-auto rounded bg-slate-100 p-2 text-xs">{children}</pre>,
      }}
    >
      {children}
    </ReactMarkdown>
  );
}
