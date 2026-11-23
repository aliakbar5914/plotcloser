"use client";

import { useEffect, useRef, useState } from "react";
import { sendChat, type ToolCall } from "@/lib/api";
import { getThreadId, getUserId, startNewThread } from "@/lib/identity";

type ChatMessage = { role: "user" | "agent"; text: string; tools?: ToolCall[] };

const WELCOME: ChatMessage = {
  role: "agent",
  text: "Assalam o Alaikum! 👋 I'm PlotCloser. Tell me what you're looking for: a house, plot, rental or car, your area and budget.",
};

const SUGGESTIONS = ["10 marla house under 3 crore", "Used Corolla under 70 lakh", "What visits do I have?"];

// Messages shown on screen are also saved per thread, so a page refresh keeps the chat.
const storageKey = (threadId: string) => `plotcloser_messages_${threadId}`;

function loadMessages(threadId: string): ChatMessage[] {
  const saved = localStorage.getItem(storageKey(threadId));
  return saved ? JSON.parse(saved) : [WELCOME];
}

type Props = { prefill?: { text: string; nonce: number } };

// NOTE: this component is loaded with ssr:false (see listings page), so it only
// runs in the browser and can read localStorage directly when it starts.
export default function ChatPanel({ prefill }: Props) {
  const [ids, setIds] = useState(() => ({ userId: getUserId(), threadId: getThreadId() }));
  const [messages, setMessages] = useState<ChatMessage[]>(() => loadMessages(ids.threadId));
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // "Ask about this" on a listing card fills the input box.
  // React pattern "adjust state when a prop changes": compare during render, no effect needed.
  const [seenNonce, setSeenNonce] = useState(prefill?.nonce);
  if (prefill && prefill.nonce !== seenNonce) {
    setSeenNonce(prefill.nonce);
    setInput(prefill.text);
  }

  // Save messages whenever they change (writing to storage is a side effect = fine in an effect).
  useEffect(() => {
    localStorage.setItem(storageKey(ids.threadId), JSON.stringify(messages));
  }, [messages, ids]);

  // Scroll to the newest message.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function send(text: string) {
    const message = text.trim();
    if (!message || sending) return;

    setMessages((old) => [...old, { role: "user", text: message }]);
    setInput("");
    setSending(true);
    try {
      const result = await sendChat(ids.userId, ids.threadId, message);
      setMessages((old) => [...old, { role: "agent", text: result.reply, tools: result.tool_calls }]);
    } catch {
      setMessages((old) => [
        ...old,
        { role: "agent", text: "⚠️ I couldn't reach the server. Please check your internet and try again." },
      ]);
    } finally {
      setSending(false);
    }
  }

  function newChat() {
    setIds({ ...ids, threadId: startNewThread() }); // same user, fresh conversation
    setMessages([WELCOME]);
  }

  return (
    <div className="flex h-[calc(100vh-7rem)] min-h-[480px] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-200 bg-emerald-600 px-4 py-3 text-white">
        <div>
          <p className="font-semibold">PlotCloser Agent</p>
          <p className="text-xs text-emerald-100">AI sales assistant · replies in seconds</p>
        </div>
        <button onClick={newChat} className="rounded-lg bg-white/15 px-3 py-1 text-sm hover:bg-white/25">
          + New chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((message, index) => (
          <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm ${
                message.role === "user" ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-800"
              }`}
            >
              {message.text.replace(/\*\*/g, "")}
              {/* Show which tools the agent used: makes the agent's work visible */}
              {message.tools && message.tools.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {message.tools.map((tool, toolIndex) => (
                    <span key={toolIndex} className="rounded-full bg-white px-2 py-0.5 font-mono text-[10px] text-slate-500 ring-1 ring-slate-200">
                      🔧 {tool.name}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {sending && <div className="w-fit rounded-2xl bg-slate-100 px-4 py-2 text-sm text-slate-500">Typing…</div>}
        <div ref={bottomRef} />
      </div>

      {/* Quick suggestions (only before the first question) */}
      {messages.length === 1 && (
        <div className="flex flex-wrap gap-2 px-4 pb-2">
          {SUGGESTIONS.map((suggestion) => (
            <button
              key={suggestion}
              onClick={() => send(suggestion)}
              className="rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600 hover:bg-slate-50"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <form
        onSubmit={(event) => {
          event.preventDefault(); // stop the browser from reloading the page
          send(input);
        }}
        className="flex gap-2 border-t border-slate-200 p-3"
      >
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Type your message…"
          maxLength={2000}
          className="flex-1 rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none focus:border-emerald-500"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </div>
  );
}
