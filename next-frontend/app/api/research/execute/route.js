import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function POST(req) {
  const body = await req.json();
  const fastapiUrl = 'http://localhost:8000/research/execute';

  try {
    const fastapiRes = await fetch(fastapiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!fastapiRes.ok) {
      const errorText = await fastapiRes.text();
      return new NextResponse(errorText, { status: fastapiRes.status });
    }

    const data = await fastapiRes.json();
    return NextResponse.json(data);
  } catch (error) {
    return new NextResponse(`Error: ${error.message}`, { status: 500 });
  }
} 