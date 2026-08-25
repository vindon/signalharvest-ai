import { NextRequest, NextResponse } from 'next/server';

// Thin authenticated proxy: client components call /api/proxy/<path>, this
// handler attaches X-API-Key server-side and forwards to the real gateway.
// The API key never reaches the browser. GET is open to any /api/v1/* path
// (every route already requires the key); mutating methods are restricted
// to exactly what the UI does — this is not a general-purpose passthrough.

const API_URL = process.env.SIGNALHARVEST_API_URL || 'http://localhost:8000';
const API_KEY = process.env.SIGNALHARVEST_API_KEY || '';

const ALLOWED_POST_PATHS = [/^pipeline\/run$/, /^brands$/];
const ALLOWED_PATCH_PATHS = [/^brands\/[^/]+$/];
const ALLOWED_DELETE_PATHS = [/^brands\/[^/]+$/];

function resolveTarget(pathSegments: string[]): string | null {
  if (pathSegments.some((seg) => seg === '..' || seg === '.' || seg === '')) {
    return null;
  }
  return `/api/v1/${pathSegments.join('/')}`;
}

async function forward(
  method: string,
  target: string,
  search: string,
  body?: string
): Promise<NextResponse> {
  const res = await fetch(`${API_URL}${target}${search}`, {
    method,
    headers: {
      'X-API-Key': API_KEY,
      ...(body ? { 'Content-Type': 'application/json' } : {}),
    },
    ...(body ? { body } : {}),
    cache: 'no-store',
  });
  const responseBody = await res.text();
  const headers: Record<string, string> = {
    'Content-Type': res.headers.get('Content-Type') ?? 'application/json',
  };
  const disposition = res.headers.get('Content-Disposition');
  if (disposition) headers['Content-Disposition'] = disposition;
  return new NextResponse(responseBody, { status: res.status, headers });
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const target = resolveTarget(path);
  if (!target) return NextResponse.json({ error: 'invalid path' }, { status: 400 });
  return forward('GET', target, request.nextUrl.search);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const target = resolveTarget(path);
  const joined = path.join('/');
  if (!target || !ALLOWED_POST_PATHS.some((re) => re.test(joined))) {
    return NextResponse.json({ error: 'invalid path' }, { status: 400 });
  }
  const bodyText = await request.text();
  return forward('POST', target, '', bodyText);
}

export async function PATCH(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const target = resolveTarget(path);
  const joined = path.join('/');
  if (!target || !ALLOWED_PATCH_PATHS.some((re) => re.test(joined))) {
    return NextResponse.json({ error: 'invalid path' }, { status: 400 });
  }
  const bodyText = await request.text();
  return forward('PATCH', target, '', bodyText);
}

export async function DELETE(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const target = resolveTarget(path);
  const joined = path.join('/');
  if (!target || !ALLOWED_DELETE_PATHS.some((re) => re.test(joined))) {
    return NextResponse.json({ error: 'invalid path' }, { status: 400 });
  }
  return forward('DELETE', target, '');
}
