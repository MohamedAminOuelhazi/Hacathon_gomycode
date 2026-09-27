import { NextResponse } from "next/server";

export const maxDuration = 180;

export async function POST(request: Request) {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ detail: "Please enter a valid question." }, { status: 400 });
  }

  if (
    !payload ||
    typeof payload !== "object" ||
    typeof (payload as { message?: unknown }).message !== "string" ||
    !(payload as { message: string }).message.trim()
  ) {
    return NextResponse.json({ detail: "Please enter a valid question." }, { status: 400 });
  }

  const input = payload as { message: string; history?: unknown };
  const history = Array.isArray(input.history)
    ? input.history
        .filter((item): item is { role: "user" | "assistant"; content: string } =>
          !!item && typeof item === "object" &&
          ((item as { role?: unknown }).role === "user" || (item as { role?: unknown }).role === "assistant") &&
          typeof (item as { content?: unknown }).content === "string" &&
          !!(item as { content: string }).content.trim(),
        )
        .slice(-12)
        .map(({ role, content }) => ({ role, content: content.slice(0, 4_000) }))
    : [];

  const baseUrl = (process.env.SOUFET_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
  try {
    const upstream = await fetch(`${baseUrl}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: input.message, history }),
      cache: "no-store",
      signal: AbortSignal.timeout(150_000),
    });

    if (!upstream.ok) {
      const safeDetail = upstream.status === 504
        ? "Soufet took too long to respond. Check the backend logs and try again."
        : upstream.status === 502
          ? "The agent could not complete the request. Check the NVIDIA hosted API and PostgreSQL connectivity, then review the backend logs."
          : upstream.status === 422 || upstream.status === 400
            ? "The backend rejected the request. Check the question format and backend logs."
            : `The agent API returned an error (HTTP ${upstream.status}). Check the backend logs.`;
      return NextResponse.json({ detail: safeDetail }, { status: upstream.status });
    }

    return NextResponse.json(await upstream.json());
  } catch {
    return NextResponse.json(
      { detail: "Soufet could not reach the agent API. Start the backend and try again." },
      { status: 503 },
    );
  }
}
