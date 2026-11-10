
from pathlib import Path
from datetime import datetime
import subprocess
import unicodedata
import hashlib
import shutil
import json
import re
import sys

# ==========================================================
# CONFIGURACIO
# ==========================================================

CARPETA_ORIGEN = Path(
    "/mnt/c/Users/Home/Desktop/Mecanuscritos/0. Publicats"
)

REPO = Path.home() / "projects" / "moha.cat"

CARPETA_DESTI = REPO / "src/content/escrits"
CARPETA_IMATGES = REPO / "public/images/odt"

FITXER_ESTATS = REPO / "scripts/odt_importats.json"


# ==========================================================
# FUNCIONS AUXILIARS
# ==========================================================

def slugify(text):
    """Converteix un nom en un slug apte per a URLs."""

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)

    return text.strip("-")


def calcular_hash(fitxer):
    """Calcula una empremta digital del document."""

    sha = hashlib.sha256()

    with fitxer.open("rb") as f:
        for bloc in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(bloc)

    return sha.hexdigest()


def carregar_estats():
    """Llegeix l'historial de documents importats."""

    if not FITXER_ESTATS.exists():
        return {}

    try:
        return json.loads(
            FITXER_ESTATS.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError:
        print("ERROR: el fitxer d'estats JSON no es pot llegir.")
        sys.exit(1)


def desar_estats(estats):
    """Desa l'historial actualitzat."""

    FITXER_ESTATS.write_text(
        json.dumps(estats, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def executar(comanda, descripcio):
    """Executa una ordre i informa dels errors."""

    resultat = subprocess.run(
        comanda,
        cwd=REPO,
        text=True,
        capture_output=True
    )

    if resultat.returncode != 0:
        print(f"\nERROR: {descripcio}")
        print(resultat.stderr)
        raise RuntimeError(descripcio)

    return resultat


# ==========================================================
# CONVERSIO ODT -> MARKDOWN
# ==========================================================

def convertir_document(odt, estats):
    nom = odt.name
    slug = slugify(odt.stem)

    if not slug:
        print(f"IGNORAT: nom de fitxer no vàlid: {nom}")
        return None

    hash_actual = calcular_hash(odt)

    estat_anterior = estats.get(nom, {})

    # No convertir si el contingut no ha canviat
    if estat_anterior.get("hash") == hash_actual:
        print(f"SENSE CANVIS: {nom}")
        return None

    es_nou = not estat_anterior

    desti = CARPETA_DESTI / f"{slug}.md"
    carpeta_imatges = CARPETA_IMATGES / slug

    if desti.exists() and es_nou:
        print(
            f"AVÍS: {desti.name} ja existeix i no consta "
            "a l'historial. Es tornarà a generar."
        )

    print(f"\nCONVERTINT: {nom}")

    # Eliminar les imatges anteriors d'aquest document
    # abans de tornar-les a extreure.
    if carpeta_imatges.exists():
        shutil.rmtree(carpeta_imatges)

    carpeta_imatges.mkdir(parents=True, exist_ok=True)

    # Pandoc converteix el document i extreu les imatges
    ruta_media = f"public/images/odt/{slug}"

    resultat = executar(
        [
            "pandoc",
            str(odt),
            "--from=odt",
            "--to=gfm",
            "--wrap=none",
            f"--extract-media={ruta_media}"
        ],
        f"Conversió del document {nom}"
    )

    contingut = resultat.stdout.strip()

    # Canviar les rutes internes de Pandoc per les rutes
    # públiques que utilitzarà Astro.
    contingut = contingut.replace(
        "public/images/",
        "/images/"
    )

    # Metadades de l'article
    titol = odt.stem.replace("_", " ").replace("-", " ").strip()

    data = datetime.fromtimestamp(
        odt.stat().st_mtime
    ).date().isoformat()

    markdown = (
        "---\n"
        f"title: {json.dumps(titol, ensure_ascii=False)}\n"
        f"date: {data}\n"
        f"description: {json.dumps(titol, ensure_ascii=False)}\n"
        "draft: false\n"
        "---\n\n"
        f"{contingut}\n"
    )

    desti.write_text(markdown, encoding="utf-8")

    estats[nom] = {
        "hash": hash_actual,
        "slug": slug,
        "markdown": str(desti.relative_to(REPO)),
        "ultima_importacio": datetime.now().isoformat(
            timespec="seconds"
        )
    }

    if es_nou:
        print(f"ARTICLE NOU: {desti.name}")
    else:
        print(f"ARTICLE ACTUALITZAT: {desti.name}")

    return desti


# ==========================================================
# PROCES PRINCIPAL
# ==========================================================

def main():

    print("\n====================================")
    print("      IMPORTADOR ODT - MOHA.CAT")
    print("====================================\n")

    if not CARPETA_ORIGEN.is_dir():
        print(f"No existeix la carpeta: {CARPETA_ORIGEN}")
        sys.exit(1)

    if not (REPO / ".git").exists():
        print(f"No s'ha trobat el repositori: {REPO}")
        sys.exit(1)

    CARPETA_DESTI.mkdir(parents=True, exist_ok=True)
    CARPETA_IMATGES.mkdir(parents=True, exist_ok=True)

    estats = carregar_estats()

    documents = sorted(
        p for p in CARPETA_ORIGEN.iterdir()
        if p.is_file() and p.suffix.lower() == ".odt"
        and not p.name.startswith("~$")
    )

    if not documents:
        print("No s'han trobat documents ODT.")
        return

    print(f"Documents trobats: {len(documents)}")

    # Comprovar que no hi ha canvis preparats prèviament
    resultat = executar(
        ["git", "diff", "--cached", "--quiet"],
        "Comprovació dels canvis preparats a Git"
    ) if False else subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=REPO
    )

    if resultat.returncode != 0:
        print(
            "\nHi ha canvis preparats a Git. "
            "Publicació cancel·lada per evitar barrejar canvis."
        )
        return

    articles_modificats = []

    # Guardar l'estat anterior per poder recuperar-lo si cal
    estats_anteriors = dict(estats)

    try:
        for odt in documents:
            article = convertir_document(odt, estats)

            if article:
                articles_modificats.append(article)

        if not articles_modificats:
            print("\nNo hi ha articles nous ni modificats.")
            return

        # Actualitzar l'historial
        desar_estats(estats)

        fitxers = [
            str(article.relative_to(REPO))
            for article in articles_modificats
        ]

        fitxers.append(
            str(FITXER_ESTATS.relative_to(REPO))
        )

        # Afegir només els fitxers generats per l'importador
        executar(
            ["git", "add", "--", *fitxers],
            "Afegir articles a Git"
        )

        executar(
            [
                "git",
                "commit",
                "-m",
                f"Importar/actualitzar {len(articles_modificats)} article(s)"
            ],
            "Crear commit"
        )

        executar(
            ["git", "push"],
            "Pujar els canvis a GitHub"
        )

        print("\n====================================")
        print("PUBLICACIO COMPLETADA")
        print(f"Articles processats: {len(articles_modificats)}")
        print("GitHub ha rebut els canvis.")
        print("Cloudflare iniciarà el desplegament.")
        print("====================================\n")

    except Exception as error:
        print(f"\nPROCÉS INTERROMPUT: {error}")
        print(
            "Revisa Git amb: git status"
        )
        print(
            "Si cal, restaura l'historial abans de tornar-ho a provar."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
