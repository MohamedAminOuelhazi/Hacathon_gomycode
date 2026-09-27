import Image from "next/image";
import { AnswerRenderer } from "./AnswerRenderer";
import { ToolEvents } from "./ToolEvents";
import { VisualizationRenderer } from "./VisualizationRenderer";
import type { ChatMessage } from "@/types/assistant";

export function AssistantMessage({ message }: { message: ChatMessage }) {
  if (message.role === "user") {
    return <div className="user-message"><p>{message.content}</p></div>;
  }

  return (
    <article className="assistant-message">
      <div className="assistant-message__identity">
        <Image src="/soufet-logo.svg" alt="Soufet" width={92} height={21} priority />
        <span>ANSWER</span>
      </div>
      <AnswerRenderer answer={message.response?.answer ?? message.content} />
      {message.response?.visualizations?.length ? (
        <div className="visualization-stack">
          {message.response.visualizations.map((visualization, index) => (
            <VisualizationRenderer key={`visualization-${index}`} visualization={visualization} />
          ))}
        </div>
      ) : null}
      {message.response && <ToolEvents events={message.response.tool_events} />}
    </article>
  );
}
