import http.client
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

from scripts import editor


class BookCoverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.paths = patch.multiple(
            editor, CONTENT=root / "content", DRAFTS=root / "drafts", IMAGES=root / "images"
        )
        self.paths.start()
        self.server = editor.ThreadingHTTPServer((editor.HOST, 0), editor.Handler)
        self.port = patch.object(editor, "PORT", self.server.server_port)
        self.port.start()
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        self.port.stop()
        self.paths.stop()
        self.temp.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection(editor.HOST, self.server.server_port)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, response.read().decode()
        finally:
            connection.close()

    def save(self, **fields):
        form = {
            "section": "lectures", "title": "Un llibre", "date": "2026-11-25",
            "description": "", "body": "Text", **fields,
        }
        return self.request(
            "POST", "/save", urlencode(form),
            {"Content-Type": "application/x-www-form-urlencoded"},
        )

    def test_upload_and_save_edit_remove_cover(self):
        multipart = (
            b'--boundary\r\nContent-Disposition: form-data; name="image"; '
            b'filename="Portada.png"\r\nContent-Type: image/png\r\n\r\n'
            b'image bytes\r\n--boundary--\r\n'
        )
        status, cover = self.request(
            "POST", "/upload", multipart,
            {"Content-Type": "multipart/form-data; boundary=boundary"},
        )
        self.assertEqual((status, cover), (200, "/images/portada.png"))
        self.assertEqual((editor.IMAGES / "portada.png").read_bytes(), b"image bytes")

        status, _ = self.save(author="L'autora", cover=cover, draft="on")
        self.assertEqual(status, 200)
        path = editor.DRAFTS / "lectures" / "un-llibre.md"
        meta, _ = editor.read_post(path)
        self.assertEqual((meta["author"], meta["cover"]), ("L'autora", cover))
        status, page = self.request("GET", "/edit?section=lectures&slug=un-llibre")
        self.assertEqual(status, 200)
        self.assertIn('value="/images/portada.png"', page)
        self.assertIn("L&#x27;autora", page)

        status, _ = self.save(slug="un-llibre", author="L'autora", cover="")
        self.assertEqual(status, 200)
        published = editor.CONTENT / "lectures" / "un-llibre.md"
        meta, _ = editor.read_post(published)
        self.assertEqual((meta["author"], meta["cover"]), ("L'autora", ""))
        self.assertFalse(path.exists())

    def test_validation_retains_book_fields(self):
        status, page = self.save(date="incorrecta", author="Autora", cover="/images/cover.jpg")
        self.assertEqual(status, 400)
        self.assertIn('value="Autora"', page)
        self.assertIn('value="/images/cover.jpg"', page)

    def test_non_books_do_not_save_book_fields(self):
        status, _ = self.save(section="escrits", author="Autora", cover="/images/cover.jpg")
        self.assertEqual(status, 200)
        contents = (editor.CONTENT / "escrits" / "un-llibre.md").read_text()
        self.assertNotIn("author:", contents)
        self.assertNotIn("cover:", contents)

    def test_unsupported_upload_is_rejected(self):
        multipart = (
            b'--boundary\r\nContent-Disposition: form-data; name="image"; '
            b'filename="cover.txt"\r\n\r\ninvalid\r\n--boundary--\r\n'
        )
        status, message = self.request(
            "POST", "/upload", multipart,
            {"Content-Type": "multipart/form-data; boundary=boundary"},
        )
        self.assertEqual(status, 400)
        self.assertIn("Format d'imatge no adm", message)


if __name__ == "__main__":
    unittest.main()
