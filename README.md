# moha.cat

Web personal en català, construïda amb Astro. Els continguts s'escriuen en fitxers Markdown i es publiquen automàticament quan s'actualitza el repositori.

## Estructura dels continguts

- `src/content/escrits/` — articles, assajos, relats i apunts.
- `src/content/lectures/` — notes sobre llibres i lectures.
- `src/content/projectes/` — projectes personals i professionals.
- `public/images/` — imatges que pots inserir als articles.

## Crear un article

Crea un fitxer `.md` dins de la carpeta corresponent, per exemple `src/content/escrits/el-meu-article.md`:

```md
---
title: "El títol de l'article"
date: 2026-11-10
description: "Una breu descripció."
draft: false
---

Comença a escriure aquí...
```

Per deixar un article sense publicar, posa `draft: true`. Quan estigui a punt, canvia-ho a `false`.

## Afegir una imatge

Puja la imatge a `public/images/` i, dins del Markdown, fes servir:

```md
![Descripció de la imatge](/images/fotografia.jpg)
```

## Treballar al teu ordinador

Necessites Node.js instal·lat. Des de la carpeta del projecte:

```bash
npm install
npm run dev
```

Obre l'adreça local que aparegui al terminal (normalment `http://localhost:4321`).

Per comprovar la versió de publicació:

```bash
npm run build
npm run preview
```

## Publicar amb GitHub

1. Crea un repositori a GitHub, per exemple `moha.cat`.
2. Puja tots els fitxers d'aquest projecte.
3. A Cloudflare Pages, connecta el compte de GitHub i selecciona el repositori.
4. Configura:
   - Framework preset: Astro
   - Build command: `npm run build`
   - Build output directory: `dist`
5. Desa i desplega.
6. A Cloudflare Pages → Custom domains, afegeix `moha.cat`.

Cada vegada que facis `commit` i `push` a la branca principal, Cloudflare tornarà a construir i publicar la web.

Abans de canviar els nameservers del domini a SWPanel, comprova si utilitzes correu amb `@moha.cat` i conserva els registres MX, SPF, DKIM i DMARC.
