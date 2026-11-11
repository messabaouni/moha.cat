# moha.cat

Web personal en català, construïda amb Astro. Els continguts s'escriuen en fitxers Markdown i es publiquen automàticament quan s'actualitza el repositori.

## Estructura dels continguts

- `src/content/escrits/` — articles, assajos, relats i apunts.
- `src/content/lectures/` — notes sobre llibres i lectures.
- `src/content/projectes/` — projectes personals i professionals.
- 
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

