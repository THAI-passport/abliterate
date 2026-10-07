// Cloudflare Pages Function: POST /api/waitlist -> Buttondown (double opt-in handled by Buttondown).
// BUTTONDOWN_API_KEY is a Cloudflare env var (.dev.vars locally); never commit it.
// Stores only the email (and Buttondown's consent time): no plan or source tags until P4 is decided.
interface Env { BUTTONDOWN_API_KEY: string }

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  let body: { email?: unknown };
  try { body = await request.json(); } catch { return json({ error: 'invalid' }, 400); }

  const email = typeof body.email === 'string' ? body.email.trim().slice(0, 254) : '';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json({ error: 'invalid' }, 400);

  const auth = { Authorization: `Token ${env.BUTTONDOWN_API_KEY}` };
  const r = await fetch('https://api.buttondown.com/v1/subscribers', {
    method: 'POST',
    headers: { ...auth, 'Content-Type': 'application/json' },
    body: JSON.stringify({ email_address: email }),
  });
  if (r.ok) return json({ ok: true }, 200);
  const text = await r.text();
  if (r.status === 409 || /already/i.test(text)) {
    // Already there: confirmed, or still waiting for the confirmation click (Buttondown: "unactivated"). See P5.
    const s = await fetch(`https://api.buttondown.com/v1/subscribers/${encodeURIComponent(email)}`, { headers: auth });
    const type = s.ok ? ((await s.json()) as { type?: string; subscriber_type?: string }) : {};
    const state = type.type ?? type.subscriber_type ?? '';
    return json({ error: state === 'unactivated' ? 'unconfirmed' : 'exists' }, 409);
  }
  if (r.status === 400) return json({ error: 'invalid' }, 400);
  return json({ error: 'server' }, 502);
};

const json = (data: unknown, status: number) =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
