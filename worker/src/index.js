// Rep una nota des de la drecera d'iOS i la desa com a fitxer Markdown a GitHub.
// Secrets (wrangler secret put): SHARED_SECRET, GITHUB_TOKEN.

const MAX_LENGTH = 5000;

const encoder = new TextEncoder();

async function safeEqual(a, b) {
  const [ha, hb] = await Promise.all(
    [a, b].map((v) => crypto.subtle.digest('SHA-256', encoder.encode(v))),
  );
  const x = new Uint8Array(ha);
  const y = new Uint8Array(hb);
  let diff = 0;
  for (let i = 0; i < x.length; i++) diff |= x[i] ^ y[i];
  return diff === 0;
}

function toBase64(text) {
  let binary = '';
  for (const byte of encoder.encode(text)) binary += String.fromCharCode(byte);
  return btoa(binary);
}

export function buildNote(text, now = new Date()) {
  const iso = now.toISOString();
  const slug = iso.slice(0, 19).replace('T', '-').replace(/:/g, '');
  const content = `---\ndate: ${iso}\ndraft: false\n---\n\n${text.trim()}\n`;
  return { path: `src/content/miscellania/${slug}.md`, content };
}

async function readText(request) {
  const type = request.headers.get('content-type') ?? '';
  if (type.includes('application/json')) {
    const data = await request.json();
    return typeof data.text === 'string' ? data.text : '';
  }
  return request.text();
}

export default {
  async fetch(request, env) {
    if (request.method !== 'POST') return new Response('Method not allowed', { status: 405 });

    const auth = request.headers.get('authorization') ?? '';
    if (!(await safeEqual(auth, `Bearer ${env.SHARED_SECRET}`))) {
      return new Response('Unauthorized', { status: 401 });
    }

    let text;
    try {
      text = (await readText(request)).trim();
    } catch {
      return new Response('Cos de la petició no vàlid', { status: 400 });
    }
    if (!text) return new Response('La nota és buida', { status: 400 });
    if (text.length > MAX_LENGTH) return new Response('Nota massa llarga', { status: 413 });

    const { path, content } = buildNote(text);
    const url = `https://api.github.com/repos/${env.GITHUB_REPO}/contents/${path}`;
    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        authorization: `Bearer ${env.GITHUB_TOKEN}`,
        accept: 'application/vnd.github+json',
        'user-agent': 'moha-cat-notes',
      },
      body: JSON.stringify({
        message: 'Nova nota a Miscel·lània',
        content: toBase64(content),
        branch: env.GITHUB_BRANCH,
      }),
    });

    if (!response.ok) return new Response('Error en desar a GitHub', { status: 502 });
    return new Response('Nota publicada', { status: 201 });
  },
};
