// Cloudflare Pages Function: POST /api/waitlist -> Buttondown (double opt-in handled by Buttondown).
// BUTTONDOWN_API_KEY is a Cloudflare env var (.dev.vars locally); never commit it.
interface Env { BUTTONDOWN_API_KEY: string }

const PLANS = new Set(['general', 'free', 'pro', 'max', 'credits']);
const MODEL_ID = /^abliterate-[a-z0-9.-]{1,60}$/;

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  let body: { email?: unknown; plan?: unknown; source?: unknown };
  try { body = await request.json(); } catch { return json({ error: 'bad request' }, 400); }

  const email = typeof body.email === 'string' ? body.email.trim().slice(0, 254) : '';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json({ error: 'invalid email' }, 400);
  const plan = typeof body.plan === 'string' && (PLANS.has(body.plan) || MODEL_ID.test(body.plan)) ? body.plan : 'general';
  const source = typeof body.source === 'string' ? body.source.slice(0, 80) : '';

  const r = await fetch('https://api.buttondown.com/v1/subscribers', {
    method: 'POST',
    headers: { Authorization: `Token ${env.BUTTONDOWN_API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ email_address: email, tags: [`plan:${plan}`], metadata: { source } }),
  });
  // Already subscribed counts as success; never reveal whether an address is on the list.
  if (r.ok || r.status === 400 || r.status === 409) return json({ ok: true }, 200);
  return json({ error: 'upstream' }, 502);
};

const json = (data: unknown, status: number) =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
