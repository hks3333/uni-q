import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function POST(req) {
  const body = await req.json();
  const fastapiUrl = 'http://localhost:8000/auth/login';

  try {
    const fastapiRes = await fetch(fastapiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const data = await fastapiRes.json();

    if (!fastapiRes.ok) {
      return new NextResponse(JSON.stringify(data), { 
        status: fastapiRes.status,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    return NextResponse.json(data);
  } catch (error) {
    return new NextResponse(
      JSON.stringify({ detail: 'Internal server error' }), 
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
} 