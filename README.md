# moha.cat

Web personal en català, construïda amb Astro. Els continguts s'escriuen en fitxers Markdown i es publiquen automàticament quan s'actualitza el repositori.

## Estructura dels continguts

- `src/content/escrits/` — articles, assajos, relats i apunts.
- `src/content/lectures/` — notes sobre llibres i lectures.
- `src/content/projectes/` — projectes personals i professionals.
- `src/content/miscellania/` — fotografies, música, vídeos i enllaços.
- `public/images/` — imatges que pots inserir als articles.

## Estructura del codi

- `src/pages/index.astro` — pàgina d'inici.
- `src/pages/[section]/` — llistat i pàgina de cada contingut, compartits per totes les seccions.
- `src/lib/content.ts` — configuració de les seccions (textos, rutes) i funcions comunes.
- `src/components/` — capçalera, peu, «Sobre mi» i llista d'entrades.
- `src/layouts/MainLayout.astro` — plantilla base de les pàgines.
- `scripts/editor.py` — editor local (vegeu a sota).

Per afegir una secció nova, defineix-la a `src/lib/content.ts` i a `src/content.config.ts`, i afegeix-la al menú de `Header.astro`.

## Editor local (Python)

Per escriure i publicar sense tocar codi ni git:

```bash
python3 scripts/editor.py
```

Obre `http://127.0.0.1:8765`. Des d'allà pots crear i editar entrades, marcar-les com a esborrany, pujar imatges i prémer **Publicar al web**, que fa `commit`, `pull --rebase` i `push` de `src/content` i `public/images`. Només necessita Python 3 i `git` configurat amb accés al repositori. Les entrades noves es creen com a esborrany.

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


## Nota sobre l'autoria

Per ser honest: la major part del codi d'aquest projecte ha estat generada amb eines d'intel·ligència artificial. Tot i això, l'he revisat i l'he acceptat jo, i en soc el responsable. Els textos publicats al web són meus.
