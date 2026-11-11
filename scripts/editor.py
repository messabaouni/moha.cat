#!/usr/bin/env python3
"""Editor local per escriure i publicar continguts de moha.cat.

Ús:  python3 scripts/editor.py
Obre http://127.0.0.1:8765 al navegador. No cal cap dependència externa.
"""

import html
import json
import re
import subprocess
import unicodedata
import webbrowser
from datetime import date, datetime
from email.parser import BytesParser
from email.policy import HTTP
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

REPO = Path(__file__).resolve().parents[1]
CONTENT = REPO / "src/content"
DRAFTS = REPO / "drafts"  # ignorat per git: els esborranys no surten del teu ordinador
IMAGES = REPO / "public/images"
SECTIONS = {
    "escrits": "Escrits",
    "lectures": "Lectures",
    "projectes": "Projectes",
    "miscellania": "Miscel·lània",
}
HOST, PORT = "127.0.0.1", 8765
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".avif"}


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "sense-titol"


def read_post(path):
    raw = path.read_text(encoding="utf-8")
    meta = {"title": path.stem, "date": "", "description": "", "draft": False}
    body = raw
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", raw, re.S)
    if m:
        body = m.group(2).lstrip("\n")
        for line in m.group(1).splitlines():
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip()
            if key == "draft":
                meta[key] = value.lower() == "true"
            elif key in meta:
                try:
                    meta[key] = json.loads(value) if value.startswith('"') else value
                except json.JSONDecodeError:
                    meta[key] = value.strip('"')
    return meta, body


def write_post(path, meta, body):
    lines = ["---"]
    if meta["title"]:
        lines.append(f"title: {json.dumps(meta['title'], ensure_ascii=False)}")
    lines.append(f"date: {meta['date']}")
    if meta["description"]:
        lines.append(f"description: {json.dumps(meta['description'], ensure_ascii=False)}")
    lines.append(f"draft: {'true' if meta['draft'] else 'false'}")
    lines += ["---", "", body.strip().replace("\r\n", "\n"), ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def post_paths(section, slug):
    """Return (published_path, draft_path) for a post or raise ValueError."""
    if section not in SECTIONS or slug != slugify(slug):
        raise ValueError("Ruta no vàlida")
    return CONTENT / section / f"{slug}.md", DRAFTS / section / f"{slug}.md"


def find_post(section, slug):
    published, draft = post_paths(section, slug)
    return published if published.exists() else draft


def save_post(section, slug, meta, body):
    """Write drafts to drafts/ (untracked) and published posts to src/content/."""
    published, draft = post_paths(section, slug)
    target, other = (draft, published) if meta["draft"] else (published, draft)
    write_post(target, meta, body)
    other.unlink(missing_ok=True)


def note_excerpt(text, limit=60):
    plain = re.sub(r"!\[[^\]]*\]\([^)]*\)", "[imatge]", text)
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain[:limit] + ("…" if len(plain) > limit else "")


def git(*args):
    result = subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def publish(message):
    git("add", "src/content", "public/images")
    code, out = git("diff", "--cached", "--quiet")
    if code == 0:
        return True, "No hi ha canvis per publicar."
    log = []
    for args in (
        ["commit", "-m", message or "Actualitza continguts"],
        ["pull", "--rebase"],
        ["push"],
    ):
        code, out = git(*args)
        log.append(f"$ git {' '.join(args[:1])}\n{out}")
        if code != 0:
            return False, "\n\n".join(log)
    return True, "\n\n".join(log)


STYLE = """
body{font:16px/1.5 system-ui,sans-serif;max-width:46rem;margin:2rem auto;padding:0 1rem;color:#222}
h1{font-size:1.4rem} h2{font-size:1.1rem;margin-top:1.8rem}
a{color:#1a5fb4} label{display:block;margin:.8rem 0 .2rem;font-weight:600}
input[type=text],input[type=date],select,textarea{width:100%;padding:.5rem;font:inherit;box-sizing:border-box}
textarea{min-height:26rem;font-family:ui-monospace,monospace;font-size:.95rem}
button{padding:.5rem 1rem;font:inherit;cursor:pointer}
.row{display:flex;gap:1rem;align-items:end} .row>div{flex:1}
.msg{padding:.7rem 1rem;background:#e8f3e8;border-left:4px solid #3a3;margin:1rem 0;white-space:pre-wrap}
.err{background:#fbe9e9;border-color:#c33}
ul{padding-left:1.2rem} .tag{font-size:.8rem;background:#eee;padding:0 .4rem;border-radius:3px}
.bar{display:flex;gap:.6rem;align-items:center;margin-top:1rem;flex-wrap:wrap}
"""


def page(title, body, msg=None, ok=True):
    note = f'<div class="msg{"" if ok else " err"}">{html.escape(msg)}</div>' if msg else ""
    return f"""<!doctype html><html lang="ca"><meta charset="utf-8">
<title>{html.escape(title)}</title><style>{STYLE}</style>
<h1><a href="/" style="text-decoration:none">✎ Editor moha.cat</a></h1>{note}{body}</html>"""


def index_page(msg=None, ok=True):
    out = ['<p><a href="/edit">+ Nou contingut</a></p>', note_form_html()]
    for section, label in SECTIONS.items():
        posts = sorted(
            [*(CONTENT / section).glob("*.md"), *(DRAFTS / section).glob("*.md")],
            key=lambda p: p.stem,
        )
        items = []
        for p in posts:
            meta, text = read_post(p)
            if section == "miscellania":
                meta["title"] = f"{str(meta['date'])[:16].replace('T', ' ')} — {note_excerpt(text)}"
            tag = ' <span class="tag">esborrany</span>' if meta["draft"] else ""
            items.append(
                f'<li><a href="/edit?section={section}&slug={quote(p.stem)}">'
                f'{html.escape(meta["title"])}</a>{tag}</li>'
            )
        out.append(f"<h2>{label}</h2>" + (f"<ul>{''.join(items)}</ul>" if items else "<p><em>Buit</em></p>"))
    out.append(
        """<h2>Publicar</h2>
<form method="post" action="/publish">
<label>Missatge del commit (opcional)</label>
<input type="text" name="message" placeholder="Nou escrit: ...">
<div class="bar"><button>Publicar al web</button>
<small>Fa commit i push dels canvis a src/content i public/images. Els esborranys no es pugen.</small></div></form>"""
    )
    return page("Editor", "".join(out), msg, ok)


UPLOAD_JS = """
<script>
document.getElementById('img').addEventListener('change', async (ev) => {
  const file = ev.target.files[0]; if (!file) return;
  const fd = new FormData(); fd.append('image', file);
  const r = await fetch('/upload', {method: 'POST', body: fd});
  const t = document.getElementById('body'), msg = document.getElementById('imgmsg');
  if (!r.ok) { msg.textContent = await r.text(); return; }
  const md = '\\n![Descripció](' + (await r.text()) + ')\\n';
  t.setRangeText(md, t.selectionStart, t.selectionEnd, 'end'); t.focus();
  msg.textContent = 'Imatge afegida. Edita la descripció.'; ev.target.value = '';
});
</script>"""


def note_form_html(slug="", body="", draft=False):
    """Form for short Miscel·lània notes (like a personal tweet)."""
    title = "Edita la nota" if slug else "Nota ràpida (Miscel·lània)"
    return f"""<h2>{title}</h2>
<form method="post" action="/note">
<input type="hidden" name="slug" value="{html.escape(slug)}">
<textarea name="body" id="body" style="min-height:7rem" placeholder="Què tens al cap?" required>{html.escape(body)}</textarea>
<div class="bar"><button name="action" value="publish">Publicar ara</button><button name="action" value="save">Desar</button>
<label style="margin:0;font-weight:400"><input type="checkbox" name="draft"{" checked" if draft else ""}> Esborrany</label>
<input type="file" id="img" accept="image/*"><small id="imgmsg">Afegeix una imatge</small></div>
</form>{UPLOAD_JS}"""


def note_page(slug, msg=None, ok=True):
    meta, body = read_post(find_post("miscellania", slug))
    return page("Edita la nota", note_form_html(slug, body, meta["draft"]), msg, ok)


def edit_page(section="escrits", slug="", msg=None, ok=True, form=None):
    if form:
        meta, body = form
    elif slug:
        meta, body = read_post(find_post(section, slug))
    else:
        meta = {"title": "", "date": date.today().isoformat(), "description": "", "draft": True}
        body = ""
    options = "".join(
        f'<option value="{k}"{" selected" if k == section else ""}>{v}</option>'
        for k, v in SECTIONS.items()
        if k != "miscellania"
    )
    lock = " disabled" if slug else ""
    hidden = f'<input type="hidden" name="section" value="{section}">' if slug else ""
    e = html.escape
    body_html = f"""
<form method="post" action="/save">
<input type="hidden" name="slug" value="{e(slug)}">{hidden}
<div class="row"><div><label>Secció</label><select name="section"{lock}>{options}</select></div>
<div><label>Data</label><input type="date" name="date" value="{e(str(meta['date']))}" required></div></div>
<label>Títol</label><input type="text" name="title" value="{e(meta['title'])}" required>
<label>Descripció (opcional)</label><input type="text" name="description" value="{e(meta['description'])}">
<label><input type="checkbox" name="draft"{" checked" if meta['draft'] else ""}> Esborrany (només al teu ordinador, no es puja a GitHub)</label>
<label>Text (Markdown)</label><textarea name="body" id="body">{e(body)}</textarea>
<div class="bar"><button>Desar</button>
<input type="file" id="img" accept="image/*"><small id="imgmsg">Afegeix una imatge al text</small></div>
</form>
<script>
document.getElementById('img').addEventListener('change', async (ev) => {{
  const file = ev.target.files[0]; if (!file) return;
  const fd = new FormData(); fd.append('image', file);
  const r = await fetch('/upload', {{method: 'POST', body: fd}});
  const t = document.getElementById('body'), msg = document.getElementById('imgmsg');
  if (!r.ok) {{ msg.textContent = await r.text(); return; }}
  const md = '\\n![Descripció](' + (await r.text()) + ')\\n';
  t.setRangeText(md, t.selectionStart, t.selectionEnd, 'end'); t.focus();
  msg.textContent = 'Imatge afegida. Edita la descripció.'; ev.target.value = '';
}});
</script>"""
    return page("Edita", body_html, msg, ok)


class Handler(BaseHTTPRequestHandler):
    def send(self, content, status=200, ctype="text/html; charset=utf-8"):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        return self.rfile.read(int(self.headers.get("Content-Length", 0)))

    def local_origin(self):
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        return host in (f"{HOST}:{PORT}", f"localhost:{PORT}") and (
            origin is None or origin.split("://", 1)[-1] == host
        )

    def do_GET(self):
        if not self.local_origin():
            return self.send("Prohibit", 403)
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if url.path == "/":
                self.send(index_page())
            elif url.path == "/edit":
                if q.get("section") == "miscellania" and q.get("slug"):
                    self.send(note_page(q["slug"]))
                else:
                    self.send(edit_page(q.get("section", "escrits"), q.get("slug", "")))
            else:
                self.send("No trobat", 404)
        except (ValueError, OSError) as exc:
            self.send(index_page(str(exc), ok=False), 400)

    def do_POST(self):
        if not self.local_origin():
            return self.send("Prohibit", 403)
        try:
            if self.path == "/upload":
                self.upload()
            else:
                form = {k: v[0] for k, v in parse_qs(self.body().decode("utf-8"), keep_blank_values=True).items()}
                if self.path == "/save":
                    self.save(form)
                elif self.path == "/note":
                    self.note(form)
                elif self.path == "/publish":
                    ok, log = publish(form.get("message", "").strip())
                    self.send(index_page(log, ok), 200 if ok else 500)
                else:
                    self.send("No trobat", 404)
        except (ValueError, OSError) as exc:
            self.send(f"Error: {exc}", 400)

    def save(self, form):
        section, slug = form.get("section", ""), form.get("slug", "")
        title = form.get("title", "").strip()
        meta = {
            "title": title,
            "date": form.get("date", ""),
            "description": form.get("description", "").strip(),
            "draft": "draft" in form,
        }
        body = form.get("body", "")
        try:
            if not title or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", meta["date"]):
                raise ValueError("Cal un títol i una data vàlida.")
            if not slug:
                slug = slugify(title)
                if any(p.exists() for p in post_paths(section, slug)):
                    raise ValueError(f"Ja existeix «{slug}» a {SECTIONS[section]}.")
            save_post(section, slug, meta, body)
        except ValueError as exc:
            return self.send(edit_page(section if section in SECTIONS else "escrits", "", str(exc), False, (meta, body)), 400)
        self.send(edit_page(section, slug, "Desat. Quan estiguis a punt, publica des de la pàgina principal."))

    def note(self, form):
        body = form.get("body", "").strip()
        if not body:
            return self.send(index_page("La nota és buida.", ok=False), 400)
        slug = form.get("slug", "")
        meta = {"title": "", "description": "", "draft": "draft" in form}
        if slug:
            meta["date"] = read_post(find_post("miscellania", slug))[0]["date"]
        else:
            now = datetime.now().astimezone()
            meta["date"] = now.isoformat(timespec="minutes")
            slug = now.strftime("%Y-%m-%d-%H%M%S")
            while any(p.exists() for p in post_paths("miscellania", slug)):
                slug += "-2"
        save_post("miscellania", slug, meta, body)
        if form.get("action") == "publish" and not meta["draft"]:
            ok, log = publish("Nova nota a Miscel·lània")
            return self.send(index_page(log, ok), 200 if ok else 500)
        self.send(index_page("Nota desada."))

    def upload(self):
        ctype = self.headers.get("Content-Type", "")
        msg = BytesParser(policy=HTTP).parsebytes(
            f"Content-Type: {ctype}\r\n\r\n".encode() + self.body()
        )
        for part in msg.iter_parts():
            if part.get_param("name", header="content-disposition") == "image":
                name = Path(part.get_filename() or "").name
                stem = slugify(Path(name).stem)
                ext = Path(name).suffix.lower()
                if ext not in IMAGE_EXTS:
                    raise ValueError("Format d'imatge no admès.")
                IMAGES.mkdir(parents=True, exist_ok=True)
                target, n = IMAGES / f"{stem}{ext}", 1
                while target.exists():
                    n += 1
                    target = IMAGES / f"{stem}-{n}{ext}"
                target.write_bytes(part.get_payload(decode=True))
                return self.send(f"/images/{target.name}", ctype="text/plain; charset=utf-8")
        raise ValueError("Falta la imatge.")

    def log_message(self, *args):
        pass


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}/"
    print(f"Editor obert a {url}  (Ctrl+C per sortir)")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
