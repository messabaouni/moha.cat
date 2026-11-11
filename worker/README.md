# Notes des de l'iPhone (Compartir)

Un Cloudflare Worker petit i independent del web. Rep text des d'una drecera d'iOS i el desa com a nota a Miscel·lània; el commit fa que Cloudflare reconstrueixi el web.

## Instal·lació (una sola vegada)

1. A GitHub → Settings → Developer settings → Fine-grained tokens, crea un token **només per a aquest repositori** amb el permís **Contents: Read and write**.
2. Genera una clau llarga i aleatòria (per exemple `openssl rand -hex 24`).
3. Des d'aquesta carpeta:

```bash
cd worker
npx wrangler login
npx wrangler secret put GITHUB_TOKEN     # enganxa el token de GitHub
npx wrangler secret put SHARED_SECRET    # enganxa la clau del pas 2
npx wrangler deploy
```

`deploy` mostra l'adreça del Worker (`https://moha-cat-notes.<el-teu-subdomini>.workers.dev`).

## Drecera d'iOS

A l'app **Dreceres**, crea una drecera nova:

1. Activa **Mostra al full de compartició** i accepta **Text** i **URLs**.
2. Acció **Obtén contingut d'URL**:
   - URL: l'adreça del Worker
   - Mètode: **POST**
   - Capçaleres: `Authorization` = `Bearer LA_TEVA_CLAU`
   - Cos de la petició: **Fitxer**, amb l'entrada de la drecera.
3. (Opcional) Acció **Mostra notificació** amb el resultat.

Per escriure una nota sense compartir res, afegeix abans una acció **Demana entrada** (text) i fes servir el seu resultat com a cos.

## Notes

- Només accepta peticions amb la clau correcta. No posis mai el token ni la clau al codi.
- Per ara només admet text (Markdown i enllaços). Les imatges es pugen amb l'editor local.
- Les notes es publiquen directament (no com a esborrany).
