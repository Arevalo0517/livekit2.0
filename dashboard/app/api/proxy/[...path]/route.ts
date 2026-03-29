import { NextRequest, NextResponse } from 'next/server';

const API_BASE = 'http://api:8000';

async function handler(
  req: NextRequest,
  { params }: { params: { path: string[] } },
) {
  const adminKey = process.env.ADMIN_API_KEY;
  if (!adminKey) {
    return NextResponse.json({ detail: 'ADMIN_API_KEY not configured' }, { status: 500 });
  }

  const path = params.path.join('/');
  const search = req.nextUrl.search;
  const url = `${API_BASE}/${path}${search}`;

  const headers: Record<string, string> = {
    'X-Admin-Key': adminKey,
    'Content-Type': 'application/json',
  };

  const body =
    req.method !== 'GET' && req.method !== 'HEAD'
      ? await req.text()
      : undefined;

  const upstream = await fetch(url, { method: req.method, headers, body });
  const text = await upstream.text();
  const data = text ? JSON.parse(text) : null;
  return NextResponse.json(data, { status: upstream.status });
}

export const GET = handler;
export const POST = handler;
export const PATCH = handler;
export const DELETE = handler;
