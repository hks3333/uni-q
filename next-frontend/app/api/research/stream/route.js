import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function POST(req) {
  const body = await req.json();
  const fastapiUrl = 'http://localhost:8000/research/stream';

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

    // Create a readable stream from the FastAPI response
    const stream = new ReadableStream({
      async start(controller) {
        const reader = fastapiRes.body.getReader();
        
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            controller.enqueue(value);
          }
        } catch (error) {
          controller.error(error);
        } finally {
          controller.close();
        }
      }
    });

    return new NextResponse(stream, {
      status: 200,
      headers: {
        'Content-Type': 'text/plain',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    return new NextResponse(`Error: ${error.message}`, { status: 500 });
  }
} 