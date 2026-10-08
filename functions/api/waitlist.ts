// Cloudflare Pages Function: POST /api/waitlist -> Buttondown (double opt-in handled by Buttondown).
// BUTTONDOWN_API_KEY is a Cloudflare env var (.dev.vars locally); never commit it.
// Stores only the email (and Buttondown's consent time): no tags (P4). An address that is already
// subscribed gets the same answer as a new one, so the form never reveals who is on the list (P5).
interface Env { BUTTONDOWN_API_KEY: string }

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  // Origin check: reject (403, server error) when Origin is present and is not allowed
  const origin = request.headers.get('origin');
  if (origin) {
    const isAllowed =
      origin === 'https://abliterate.app' ||
      /^https:\/\/([a-zA-Z0-9-]+\.)?abliterate\.pages\.dev$/.test(origin) ||
      /^http:\/\/(?:localhost|127\.0\.0\.1)(?::\d+)?$/.test(origin);
    if (!isAllowed) {
      return json({ error: 'server' }, 403);
    }
  }

  // Require Content-Type: application/json
  const contentType = request.headers.get('content-type') ?? '';
  if (!contentType.toLowerCase().includes('application/json')) {
    return json({ error: 'invalid' }, 400);
  }

  // Body size cap: 1024 bytes maximum
  const contentLength = request.headers.get('content-length');
  if (contentLength && parseInt(contentLength, 10) > 1024) {
    return json({ error: 'invalid' }, 413);
  }

  const raw = await request.text();
  if (raw.length > 1024) {
    return json({ error: 'invalid' }, 413);
  }

  let body: { email?: unknown; hp?: unknown; website?: unknown };
  try {
    body = JSON.parse(raw);
  } catch {
    return json({ error: 'invalid' }, 400);
  }

  // Honeypot check: return normal success and do nothing if filled
  const hp =
    (typeof body.hp === 'string' ? body.hp.trim() : '') ||
    (typeof body.website === 'string' ? body.website.trim() : '');
  if (hp) {
    return json({ ok: true }, 200);
  }

  const email = typeof body.email === 'string' ? body.email.trim().slice(0, 254) : '';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return json({ error: 'invalid' }, 400);
  }

  if (!env.BUTTONDOWN_API_KEY) {
    console.error('waitlist: BUTTONDOWN_API_KEY is not set');
    return json({ error: 'server' }, 502);
  }

  const r = await fetch('https://api.buttondown.com/v1/subscribers', {
    method: 'POST',
    headers: {
      Authorization: `Token ${env.BUTTONDOWN_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email_address: email }),
  });

  if (r.ok) return json({ ok: true }, 200);

  const resText = await r.text();
  console.error('buttondown', r.status, resText.slice(0, 500));

  // Buttondown answers an existing address with 4xx and an "already" message (shape unverified, P5):
  // same reply as a new signup so membership is never revealed.
  if (r.status === 409 || (r.status === 400 && /already|exists/i.test(resText))) {
    return json({ ok: true }, 200);
  }
  if (r.status === 400) {
    return json({ error: 'invalid' }, 400);
  }
  return json({ error: 'server' }, 502);
};

const json = (data: unknown, status: number) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
