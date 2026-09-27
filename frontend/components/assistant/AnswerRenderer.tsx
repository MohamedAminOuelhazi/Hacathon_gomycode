import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function AnswerRenderer({ answer }: { answer: string }) {
  return (
    <div className="answer-copy">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{answer}</ReactMarkdown>
    </div>
  );
}
