import { NextResponse } from "next/server";

export async function GET() {
  const baseUrl = (process.env.SOUFET_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
  try {
    const response = await fetch(`${baseUrl}/health`, { cache: "no-store", signal: AbortSignal.timeout(4000) });
    return NextResponse.json({ online: response.ok }, { status: response.ok ? 200 : 503 });
  } catch {
    return NextResponse.json({ online: false }, { status: 503 });
  }
}
