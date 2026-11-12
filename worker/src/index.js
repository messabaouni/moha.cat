// Rep un correu electrònic i el desa com a nota de Miscel·lània a GitHub.
// Secret (wrangler secret put): GITHUB_TOKEN.
import PostalMime from 'postal-mime';

const MAX_LENGTH = 5000;
const encoder = new TextEncoder();

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

// Treu la resposta citada i la signatura per quedar-nos amb el text escrit.
export function cleanBody(text) {
  const lines = text.replace(/\r\n/g, '\n').split('\n');
  const end = lines.findIndex((l) => /^--\s*$/.test(l) || /^>/.test(l) || /^On .+ wrote:$/.test(l));
  return (end === -1 ? lines : lines.slice(0, end)).join('\n').trim();
}

const same = (a, b) => a.trim().toLowerCase() === b.trim().toLowerCase();

export default {
  async email(message, env) {
    for (const key of ['NOTE_ADDRESS', 'ALLOWED_SENDER', 'GITHUB_TOKEN']) {
      if (!env[key]) throw new Error(`Falta el secret ${key}`);
    }
    if (!same(message.to, env.NOTE_ADDRESS) || !same(message.from, env.ALLOWED_SENDER)) {
      message.setReject('Adreça no autoritzada');
      return;
    }

    // Cloudflare afegeix aquesta capçalera; evita remitents falsificats.
    const auth = message.headers.get('authentication-results') ?? '';
    if (!/dmarc=pass|dkim=pass|spf=pass/i.test(auth)) {
      message.setReject('Autenticació del remitent no vàlida');
      return;
    }

    const parsed = await PostalMime.parse(message.raw);
    const subject = (parsed.subject ?? '').trim();
    const body = cleanBody(parsed.text ?? '');
    // L'assumpte és opcional: si hi és, es posa com a primera línia en negreta.
    const text = [subject && `**${subject}**`, body].filter(Boolean).join('\n\n');
    if (!text) {
      message.setReject('La nota és buida');
      return;
    }
    if (text.length > MAX_LENGTH) {
      message.setReject('Nota massa llarga');
      return;
    }

    const { path, content } = buildNote(text);
    const response = await fetch(
      `https://api.github.com/repos/${env.GITHUB_REPO}/contents/${path}`,
      {
        method: 'PUT',
        headers: {
          authorization: `Bearer ${env.GITHUB_TOKEN}`,
          accept: 'application/vnd.github+json',
          'user-agent': 'moha-cat-notes',
        },
        body: JSON.stringify({
          message: 'Nova nota a Miscel·lània (correu)',
          content: toBase64(content),
          branch: env.GITHUB_BRANCH,
        }),
      },
    );
    if (!response.ok) throw new Error(`GitHub ${response.status}`);
  },
};
