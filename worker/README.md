# Notes per correu electrònic

Un Cloudflare Email Worker. Envies un correu a una adreça secreta i el text es desa com a nota a Miscel·lània; el commit fa que Cloudflare reconstrueixi el web.

## Seguretat

La nota només es publica si:

1. el correu arriba a `NOTE_ADDRESS` (secret de Cloudflare: una adreça llarga i impossible d'endevinar),
2. el remitent és `ALLOWED_SENDER`, i
3. Cloudflare ha verificat el remitent (SPF/DKIM/DMARC).

## Instal·lació (una sola vegada)

1. Escull una adreça secreta, per exemple `nota-k7x2q9m4@moha.cat`. No la posis mai al codi: es desa com a secret (pas 3).
2. A GitHub → Settings → Developer settings → Fine-grained tokens, crea un token **només per a aquest repositori** amb **Contents: Read and write**.
3. Des d'aquesta carpeta (cada comanda demana el valor; el nom ja és a la comanda):

```bash
cd worker
npm install
npx wrangler login
npx wrangler secret put GITHUB_TOKEN    # enganxa el token de GitHub
npx wrangler secret put NOTE_ADDRESS    # l'adreça secreta del pas 1
npx wrangler secret put ALLOWED_SENDER  # el teu correu, p. ex. el de Gmail
npx wrangler deploy
```

4. Al tauler de Cloudflare → `moha.cat` → **Email → Email Routing**: activa-ho (afegirà els registres MX) i crea una **adreça personalitzada** amb el mateix valor que `NOTE_ADDRESS`, acció **Send to a Worker** → `moha-cat-notes`.

## Ús

Envia un correu des de `ALLOWED_SENDER` a `NOTE_ADDRESS`:

- El cos és la nota (Markdown i enllaços). La resposta citada i la signatura (`-- `) s'ignoren.
- L'assumpte és opcional; si hi és, es posa en negreta a dalt de la nota.
- Només text: els adjunts i imatges s'ignoren (usa l'editor local).
- Es publica directament, no com a esborrany.

Consell: desa l'adreça com a contacte («Nota web») al telèfon.
