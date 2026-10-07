// Cloudflare Pages Function: POST /api/waitlist -> Buttondown (double opt-in handled by Buttondown).
// BUTTONDOWN_API_KEY is a Cloudflare env var (.dev.vars locally); never commit it.
// Stores only the email (and Buttondown's consent time): no tags (P4). An address that is already
// subscribed gets the same answer as a new one, so the form never reveals who is on the list (P5).
interface Env { BUTTONDOWN_API_KEY: string }

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  let body: { email?: unknown };
  try { body = await request.json(); } catch { return json({ error: 'invalid' }, 400); }

  const email = typeof body.email === 'string' ? body.email.trim().slice(0, 254) : '';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json({ error: 'invalid' }, 400);

  const r = await fetch('https://api.buttondown.com/v1/subscribers', {
    method: 'POST',
    headers: { Authorization: `Token ${env.BUTTONDOWN_API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ email_address: email }),
  });
  if (r.ok) return json({ ok: true }, 200);
  // Buttondown answers an existing address with 4xx and an "already" message (shape unverified, P5): same reply as a new signup.
  if (r.status === 409 || (r.status === 400 && /already|exists/i.test(await r.text()))) return json({ ok: true }, 200);
  if (r.status === 400) return json({ error: 'invalid' }, 400);
  console.error('buttondown', r.status, (await r.text()).slice(0, 200));
  return json({ error: 'server' }, 502);
};

const json = (data: unknown, status: number) =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
