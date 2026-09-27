"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import Image from "next/image";
import { ArrowUp, History, MessageSquare, Plus, Sparkles, Trash2 } from "lucide-react";
import { AssistantMessage } from "@/components/assistant/AssistantMessage";
import type { ChatMessage, SoufetResponse } from "@/types/assistant";

const SUGGESTIONS = [
  { icon: "01", text: "Show monthly revenue for 2026" },
  { icon: "02", text: "What is our refund policy?" },
  { icon: "03", text: "Which product category generated the most revenue?" },
];
const HISTORY_KEY = "soufet-chat-history-v1";

interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  updatedAt: number;
}

function makeId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [historyReady, setHistoryReady] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(HISTORY_KEY);
      const parsed = saved ? JSON.parse(saved) as Conversation[] : [];
      if (Array.isArray(parsed)) {
        const valid = parsed.filter((item) => item && typeof item.id === "string" && Array.isArray(item.messages));
        setConversations(valid);
        const latest = valid.sort((a, b) => b.updatedAt - a.updatedAt)[0];
        if (latest) {
          setActiveId(latest.id);
          setMessages(latest.messages);
        }
      }
    } catch {
      localStorage.removeItem(HISTORY_KEY);
    }
    setHistoryReady(true);
  }, []);

  useEffect(() => {
    if (historyReady) localStorage.setItem(HISTORY_KEY, JSON.stringify(conversations));
  }, [conversations, historyReady]);

  useEffect(() => {
    let alive = true;
    const check = async () => {
      try {
        const response = await fetch("/api/health", { cache: "no-store" });
        if (alive) setApiOnline(response.ok);
      } catch {
        if (alive) setApiOnline(false);
      }
    };
    void check();
    const timer = window.setInterval(check, 30_000);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    const onShortcut = (event: globalThis.KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        startNewChat();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onShortcut);
    return () => window.removeEventListener("keydown", onShortcut);
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, pending]);

  async function sendMessage(rawMessage: string) {
    const message = rawMessage.trim();
    if (!message || pending) return;
    const conversationId = activeId ?? makeId();
    if (!activeId) setActiveId(conversationId);
    const userMessage: ChatMessage = { id: makeId(), role: "user", content: message };
    appendMessage(conversationId, userMessage);
    setDraft("");
    setPending(true);
    if (inputRef.current) inputRef.current.style.height = "auto";

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          history: messages.slice(-12).map(({ role, content }) => ({ role, content: content.slice(0, 4_000) })),
        }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(typeof payload.detail === "string" ? payload.detail : "Soufet could not complete that request. Please try again.");
      }
      const result = payload as SoufetResponse;
      if (typeof result.answer !== "string") throw new Error("Soufet returned an unreadable response. Please try again.");
      appendMessage(conversationId, {
        id: makeId(),
        role: "assistant",
        content: result.answer,
        response: {
          answer: result.answer,
          tool_events: Array.isArray(result.tool_events) ? result.tool_events : [],
          visualizations: Array.isArray(result.visualizations) ? result.visualizations : [],
        },
      });
      setApiOnline(true);
    } catch (error) {
      appendMessage(conversationId, {
        id: makeId(),
        role: "assistant",
        content: error instanceof Error ? error.message : "Soufet could not reach the agent API. Start the backend and try again.",
      });
      setApiOnline(false);
    } finally {
      setPending(false);
      inputRef.current?.focus();
    }
  }

  function appendMessage(conversationId: string, message: ChatMessage) {
    setMessages((current) => [...current, message]);
    setConversations((current) => {
      const existing = current.find((item) => item.id === conversationId);
      const nextMessages = [...(existing?.messages ?? []), message];
      const title = nextMessages.find((item) => item.role === "user")?.content ?? "New conversation";
      const updated: Conversation = {
        id: conversationId,
        title: title.length > 46 ? `${title.slice(0, 46).trimEnd()}...` : title,
        messages: nextMessages,
        updatedAt: Date.now(),
      };
      return [updated, ...current.filter((item) => item.id !== conversationId)];
    });
  }

  function startNewChat() {
    setHistoryOpen(false);
    setActiveId(null);
    setMessages([]);
    setDraft("");
    inputRef.current?.focus();
  }

  function openConversation(conversation: Conversation) {
    if (pending) return;
    setHistoryOpen(false);
    setActiveId(conversation.id);
    setMessages(conversation.messages);
    setDraft("");
  }

  function deleteConversation(id: string) {
    const remaining = conversations.filter((item) => item.id !== id);
    setConversations(remaining);
    if (activeId === id) {
      const next = remaining[0];
      setActiveId(next?.id ?? null);
      setMessages(next?.messages ?? []);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void sendMessage(draft);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendMessage(draft);
    }
  }

  function updateDraft(value: string) {
    setDraft(value);
    const input = inputRef.current;
    if (input) {
      input.style.height = "auto";
      input.style.height = `${Math.min(input.scrollHeight, 144)}px`;
    }
  }

  return (
    <main className={`app-shell ${historyOpen ? "has-sidebar-open" : ""}`}>
      <aside className="sidebar">
        <div className="sidebar__brand">
          <Image src="/soufet-logo.svg" alt="Soufet" width={142} height={32} priority />
          <span className="sidebar__edition">BUSINESS INTELLIGENCE</span>
        </div>

        <button className="new-chat-button" onClick={startNewChat}>
          <Plus size={16} strokeWidth={2.2} />
          <span>New analysis</span>
          <kbd>Ctrl K</kbd>
        </button>

        <div className="sidebar__section-label">WORKSPACE</div>
        <div className="sidebar__active-item"><Sparkles size={15} /><span>Ask Soufet</span><i /></div>

        <div className="sidebar__section-label history-heading">HISTORY <span>{conversations.length}</span></div>
        <div className="conversation-history" aria-label="Chat history">
          {conversations.length === 0 ? <p className="conversation-history__empty">Your conversations will appear here.</p> : conversations.map((conversation) => (
            <div className={`history-item ${activeId === conversation.id ? "is-active" : ""}`} key={conversation.id}>
              <button className="history-item__open" onClick={() => openConversation(conversation)} disabled={pending} title={conversation.title}>
                <MessageSquare size={14} /><span>{conversation.title}</span>
              </button>
              <button className="history-item__delete" onClick={() => deleteConversation(conversation.id)} aria-label={`Delete ${conversation.title}`} title="Delete conversation" disabled={pending}>
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </div>

        <div className="sidebar__section-label sidebar__section-label--lower">START WITH</div>
        <div className="sidebar__suggestions">
          {SUGGESTIONS.map((item) => (
            <button key={item.icon} onClick={() => void sendMessage(item.text)} disabled={pending}>
              <span>{item.icon}</span>{item.text}
            </button>
          ))}
        </div>

        <div className="sidebar__spacer" />
        <div className="sidebar__footer">
          <div className="connection-label">
            <span className={`connection-label__dot ${apiOnline === false ? "is-offline" : ""}`} />
            <span>{apiOnline === null ? "Checking connection" : apiOnline ? "Agent API connected" : "Agent API offline"}</span>
          </div>
        </div>
      </aside>

      <section className="workspace">
        <header className="workspace-header">
          <div className="workspace-header__crumb"><span>Workspace</span><span className="crumb-slash">/</span><strong>Ask Soufet</strong></div>
          <div className="workspace-header__right">
            <button className="mobile-history-toggle" onClick={() => setHistoryOpen((open) => !open)} aria-label="Toggle chat history" title="Chat history"><History size={16} /></button>
            <span className={`workspace-header__status ${apiOnline === false ? "is-offline" : ""}`}><i />{apiOnline ? "SYSTEM READY" : apiOnline === false ? "API OFFLINE" : "CONNECTING"}</span>
            <span className="workspace-header__avatar" aria-label="User profile">M</span>
          </div>
        </header>

        <div className="conversation-scroll">
          {messages.length === 0 ? (
            <div className="welcome-state">
              <div className="welcome-state__eyebrow"><span />INTELLIGENCE, IN THE OPEN</div>
              <h1>Make the complex<br /><em>legible.</em></h1>
              <p className="welcome-state__copy">Ask a question about your business. Soufet will find the signal in your data and company knowledge.</p>
              <div className="suggestion-grid">
                {SUGGESTIONS.map((item) => (
                  <button className="suggestion-card" key={item.icon} onClick={() => void sendMessage(item.text)} disabled={pending}>
                    <span className="suggestion-card__index">{item.icon}</span>
                    <span>{item.text}</span>
                    <ArrowUp className="suggestion-card__arrow" size={15} />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="message-list">
              {messages.map((message) => <AssistantMessage key={message.id} message={message} />)}
              {pending && (
                <div className="pending-message" role="status" aria-live="polite">
                  <span className="pending-message__mark"><Image src="/soufet-logo.svg" alt="" width={14} height={14} /></span>
                  <span>Soufet is working with your request</span>
                  <i /><i /><i />
                </div>
              )}
              <div ref={endRef} />
            </div>
          )}
        </div>

        <div className="composer-dock">
          <form className="composer" onSubmit={submit}>
            <textarea
              ref={inputRef}
              value={draft}
              onChange={(event) => updateDraft(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about your business..."
              aria-label="Ask Soufet a question"
              rows={1}
              maxLength={10_000}
              disabled={pending}
            />
            <div className="composer__bottom">
              <span className="composer__hint">Business data · Company knowledge</span>
              <div className="composer__actions">
                <span className="composer__keyboard">Shift + Enter for a new line</span>
                <button className="send-button" type="submit" disabled={!draft.trim() || pending} aria-label="Send message" title="Send message">
                  {pending ? <span className="send-spinner" /> : <ArrowUp size={18} strokeWidth={2.4} />}
                </button>
              </div>
            </div>
          </form>
          <p className="composer-dock__disclaimer">Soufet can make mistakes. Verify important business decisions against the source data.</p>
        </div>
      </section>
    </main>
  );
}
