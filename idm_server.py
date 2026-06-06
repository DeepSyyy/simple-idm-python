import argparse
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import requests

from downloader import SimpleIDM


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_DOWNLOAD_DIR = "downloads"
CATEGORY_EXTENSIONS = {
    "Compressed": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"},
    "Documents": {
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".rtf",
        ".odt",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".csv",
        ".md",
    },
    "Music": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"},
    "Video": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"},
    "Programs": {".exe", ".msi", ".apk", ".dmg", ".pkg", ".deb", ".rpm", ".appimage"},
}


class DownloadCancelled(Exception):
    pass


DASHBOARD_HTML = """<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SimpleIDM</title>
  <style>
    :root {
      color-scheme: light dark;
      font-family: Arial, sans-serif;
      background: #f5f7fb;
      color: #182033;
    }

    body {
      margin: 0;
    }

    main {
      max-width: 920px;
      margin: 0 auto;
      padding: 28px 18px;
    }

    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 22px;
    }

    h1 {
      margin: 0;
      font-size: 28px;
    }

    .status {
      padding: 7px 10px;
      border-radius: 6px;
      background: #e8f0ff;
      color: #174ea6;
      font-size: 13px;
      font-weight: 700;
    }

    .download-form {
      display: grid;
      grid-template-columns: 1fr 180px;
      gap: 10px;
      margin-bottom: 18px;
      padding: 14px;
      background: #ffffff;
      border: 1px solid #dde3ee;
      border-radius: 8px;
      box-shadow: 0 1px 2px rgb(16 24 40 / 8%);
    }

    .download-form input {
      min-width: 0;
      height: 38px;
      padding: 0 10px;
      border: 1px solid #c9d2e1;
      border-radius: 6px;
      font: inherit;
    }

    .download-form button {
      height: 40px;
      border: 0;
      border-radius: 6px;
      background: #1f6feb;
      color: #ffffff;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }

    .download-form .wide {
      grid-column: 1 / -1;
    }

    .form-message {
      grid-column: 1 / -1;
      color: #61708a;
      font-size: 13px;
      min-height: 18px;
    }

    .task {
      background: #ffffff;
      border: 1px solid #dde3ee;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 12px;
      box-shadow: 0 1px 2px rgb(16 24 40 / 8%);
    }

    .task-top {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 10px;
    }

    .name {
      font-weight: 700;
      overflow-wrap: anywhere;
    }

    .meta {
      color: #61708a;
      font-size: 13px;
      margin-top: 5px;
      overflow-wrap: anywhere;
    }

    .percent {
      min-width: 118px;
      text-align: right;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }

    .bar {
      height: 12px;
      overflow: hidden;
      border-radius: 999px;
      background: #e7ecf5;
    }

    .fill {
      height: 100%;
      width: 0%;
      border-radius: inherit;
      background: #1f6feb;
      transition: width 180ms ease;
    }

    .fill.unknown {
      width: 100%;
      background: repeating-linear-gradient(
        45deg,
        #1f6feb,
        #1f6feb 12px,
        #78a6ff 12px,
        #78a6ff 24px
      );
    }

    .empty {
      border: 1px dashed #b9c2d1;
      border-radius: 8px;
      padding: 26px;
      text-align: center;
      color: #61708a;
      background: #ffffff;
    }

    .failed .fill {
      background: #d93025;
    }

    .finished .fill {
      background: #188038;
    }

    @media (prefers-color-scheme: dark) {
      :root {
        background: #111827;
        color: #eef2ff;
      }

      .task,
      .empty,
      .download-form {
        background: #182235;
        border-color: #2b3952;
      }

      .download-form input {
        background: #111827;
        border-color: #2b3952;
        color: #eef2ff;
      }

      .status {
        background: #20375f;
        color: #bcd2ff;
      }

      .meta {
        color: #a9b6cc;
      }

      .bar {
        background: #2b3952;
      }
    }

    @media (max-width: 720px) {
      .download-form {
        grid-template-columns: 1fr;
      }

      .task-top {
        display: block;
      }

      .percent {
        margin-top: 8px;
        text-align: left;
      }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>SimpleIDM</h1>
      <div class="status" id="server-status">Live</div>
    </header>
    <form class="download-form" id="download-form">
      <input class="wide" id="url-input" name="url" type="url" placeholder="https://example.com/file.zip" required>
      <input id="filename-input" name="filename" type="text" placeholder="Nama file opsional">
      <button type="submit">Download</button>
      <input class="wide" id="dir-input" name="download_dir" type="text" placeholder="Folder tujuan opsional, contoh: /home/user/Downloads">
      <div class="form-message" id="form-message"></div>
    </form>
    <section id="tasks">
      <div class="empty">Belum ada download.</div>
    </section>
  </main>
  <script>
    const tasksEl = document.getElementById("tasks");
    const statusEl = document.getElementById("server-status");
    const formEl = document.getElementById("download-form");
    const urlInput = document.getElementById("url-input");
    const filenameInput = document.getElementById("filename-input");
    const dirInput = document.getElementById("dir-input");
    const formMessage = document.getElementById("form-message");

    function bytes(value) {
      if (!value) return "0 B";
      const units = ["B", "KB", "MB", "GB", "TB"];
      let size = value;
      let unit = 0;

      while (size >= 1024 && unit < units.length - 1) {
        size /= 1024;
        unit += 1;
      }

      return `${size.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`;
    }

    function speed(value) {
      return `${bytes(value || 0)}/s`;
    }

    function filename(path) {
      return path.split(/[\\\\/]/).pop() || path;
    }

    function escapeHtml(value) {
      return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function render(tasks) {
      const entries = Object.entries(tasks);

      if (!entries.length) {
        tasksEl.innerHTML = '<div class="empty">Belum ada download.</div>';
        return;
      }

      tasksEl.innerHTML = entries.reverse().map(([id, task]) => {
        const total = Number(task.total || 0);
        const downloaded = Number(task.downloaded || 0);
        const known = total > 0;
        const percent = known ? Math.min(100, (downloaded / total) * 100) : 0;
        const label = known ? `${percent.toFixed(1)}%` : "streaming";
        const fillClass = known ? "fill" : "fill unknown";
        const width = known ? `style="width: ${percent}%"` : "";
        const currentSpeed = speed(task.speed || 0);
        const detail = known
          ? `${bytes(downloaded)} / ${bytes(total)} · ${currentSpeed}`
          : `${bytes(downloaded)} downloaded · ${currentSpeed}`;
        const error = task.error ? `<div class="meta">${escapeHtml(task.error)}</div>` : "";

        return `
          <article class="task ${task.status}">
            <div class="task-top">
              <div>
                <div class="name">#${escapeHtml(id)} ${escapeHtml(filename(task.output_path))}</div>
                <div class="meta">${escapeHtml(task.status)} · ${escapeHtml(detail)}</div>
                <div class="meta">${escapeHtml(task.output_path)}</div>
                ${error}
              </div>
              <div class="percent">${escapeHtml(label)}</div>
            </div>
            <div class="bar"><div class="${fillClass}" ${width}></div></div>
          </article>
        `;
      }).join("");
    }

    async function refresh() {
      try {
        const response = await fetch("/tasks");
        const payload = await response.json();
        statusEl.textContent = "Live";
        render(payload.tasks || {});
      } catch (error) {
        statusEl.textContent = "Offline";
      }
    }

    refresh();
    setInterval(refresh, 1000);

    formEl.addEventListener("submit", async (event) => {
      event.preventDefault();
      formMessage.textContent = "Mengirim download...";

      try {
        const response = await fetch("/download", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            url: urlInput.value.trim(),
            filename: filenameInput.value.trim(),
            download_dir: dirInput.value.trim()
          })
        });
        const payload = await response.json();

        if (!response.ok || !payload.ok) {
          throw new Error(payload.error || `HTTP ${response.status}`);
        }

        formMessage.textContent = `Download masuk antrean: ${payload.output_path}`;
        urlInput.value = "";
        filenameInput.value = "";
        refresh();
      } catch (error) {
        formMessage.textContent = `Gagal: ${error.message}`;
      }
    });
  </script>
</body>
</html>
"""


class DownloadManager:
    def __init__(
        self,
        download_dir=DEFAULT_DOWNLOAD_DIR,
        parts=8,
        ask_path=False,
        path_chooser=None,
        confirm_chooser=None,
    ):
        self.download_dir = download_dir
        self.parts = parts
        self.ask_path = ask_path
        self.path_chooser = path_chooser
        self.confirm_chooser = confirm_chooser
        self.tasks = {}
        self.lock = threading.Lock()
        self.dialog_lock = threading.Lock()
        os.makedirs(self.download_dir, exist_ok=True)

    @staticmethod
    def category_for_filename(filename):
        extension = os.path.splitext(filename)[1].lower()

        for category, extensions in CATEGORY_EXTENSIONS.items():
            if extension in extensions:
                return category

        return "General"

    def _guess_filename(self, url, filename=None):
        if filename:
            return filename

        try:
            response = requests.head(url, allow_redirects=True, timeout=10)
            response.raise_for_status()
            header_name = SimpleIDM.filename_from_headers(response.headers)

            if header_name:
                return header_name
        except requests.RequestException:
            pass

        return SimpleIDM.filename_from_url(url)

    def _ask_output_path(self, filename):
        if self.path_chooser:
            output_path = self.path_chooser(filename)

            if not output_path:
                raise DownloadCancelled("Pemilihan lokasi download dibatalkan.")

            directory = os.path.dirname(output_path) or self.download_dir
            os.makedirs(directory, exist_ok=True)
            return SimpleIDM.unique_path(output_path)

        with self.dialog_lock:
            try:
                from tkinter import Tk, filedialog
            except Exception as exc:
                raise RuntimeError(f"Tidak bisa membuka dialog pilih file: {exc}") from exc

            root = Tk()
            root.withdraw()
            root.attributes("-topmost", True)

            try:
                output_path = filedialog.asksaveasfilename(
                    title="Simpan download sebagai",
                    initialdir=os.path.abspath(self.download_dir),
                    initialfile=filename,
                )
            finally:
                root.destroy()

        if not output_path:
            raise DownloadCancelled("Pemilihan lokasi download dibatalkan.")

        directory = os.path.dirname(output_path) or self.download_dir
        os.makedirs(directory, exist_ok=True)
        return SimpleIDM.unique_path(output_path)

    def start_download(self, url, filename=None, download_dir=None, referrer=None):
        filename = self._guess_filename(url, filename)
        category = self.category_for_filename(filename)

        if self.ask_path and not download_dir:
            output_path = self._ask_output_path(filename)
            target_dir = os.path.dirname(output_path) or self.download_dir
        else:
            base_dir = download_dir or self.download_dir
            target_dir = os.path.join(base_dir, category)
            output_path = SimpleIDM.output_path_for_url(
                url,
                download_dir=target_dir,
                filename=filename,
            )

        if self.confirm_chooser:
            confirmed = self.confirm_chooser(
                {
                    "url": url,
                    "filename": os.path.basename(output_path),
                    "category": category,
                    "output_path": output_path,
                    "download_dir": target_dir,
                }
            )

            if not confirmed:
                raise DownloadCancelled("Download dibatalkan oleh user.")

        task_id = str(len(self.tasks) + 1)
        now = time.monotonic()

        with self.lock:
            self.tasks[task_id] = {
                "status": "queued",
                "url": url,
                "output_path": output_path,
                "downloaded": 0,
                "total": 0,
                "speed": 0,
                "download_dir": target_dir,
                "category": category,
                "error": None,
                "_last_downloaded": 0,
                "_last_time": now,
            }

        thread = threading.Thread(
            target=self._run_download,
            args=(task_id, url, output_path, referrer),
            daemon=True,
        )
        thread.start()
        return task_id, output_path

    def _run_download(self, task_id, url, output_path, referrer=None):
        def on_progress(downloaded, total):
            with self.lock:
                now = time.monotonic()
                task = self.tasks[task_id]
                elapsed = max(now - task["_last_time"], 0.001)
                byte_delta = max(downloaded - task["_last_downloaded"], 0)
                task["speed"] = byte_delta / elapsed
                task["_last_downloaded"] = downloaded
                task["_last_time"] = now
                self.tasks[task_id]["downloaded"] = downloaded
                self.tasks[task_id]["total"] = total

        with self.lock:
            self.tasks[task_id]["status"] = "downloading"

        try:
            headers = {}

            if referrer:
                headers["Referer"] = referrer

            SimpleIDM(
                url=url,
                output_path=output_path,
                parts=self.parts,
                progress_callback=on_progress,
                headers=headers,
            ).download()

            with self.lock:
                self.tasks[task_id]["status"] = "finished"
                self.tasks[task_id]["speed"] = 0
        except Exception as exc:
            with self.lock:
                self.tasks[task_id]["status"] = "failed"
                self.tasks[task_id]["speed"] = 0
                self.tasks[task_id]["error"] = str(exc)

            print(f"Gagal download {url}: {exc}")

    def snapshot(self):
        with self.lock:
            clean_tasks = {}

            for task_id, task in self.tasks.items():
                clean_tasks[task_id] = {
                    key: value
                    for key, value in task.items()
                    if not key.startswith("_")
                }

            return clean_tasks


def make_handler(manager):
    class IDMRequestHandler(BaseHTTPRequestHandler):
        def _send_html(self, html, status=200):
            body = html.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, payload, status=200):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            self._send_json({"ok": True})

        def do_GET(self):
            parsed = urlparse(self.path)

            if parsed.path == "/":
                self._send_html(DASHBOARD_HTML)
                return

            if parsed.path == "/health":
                self._send_json({"ok": True, "app": "SimpleIDM"})
                return

            if parsed.path == "/tasks":
                self._send_json({"ok": True, "tasks": manager.snapshot()})
                return

            if parsed.path == "/download":
                query = parse_qs(parsed.query)
                url = query.get("url", [""])[0].strip()
                filename = query.get("filename", [None])[0]
                download_dir = query.get("download_dir", [None])[0]
                referrer = query.get("referrer", [None])[0]

                if not url:
                    self._send_json({"ok": False, "error": "Parameter url kosong."}, 400)
                    return

                try:
                    task_id, output_path = manager.start_download(
                        url,
                        filename=filename,
                        download_dir=download_dir,
                        referrer=referrer,
                    )
                except DownloadCancelled as exc:
                    self._send_json({"ok": False, "error": str(exc)}, 409)
                    return

                self._send_json(
                    {"ok": True, "task_id": task_id, "output_path": output_path},
                    202,
                )
                return

            self._send_json({"ok": False, "error": "Endpoint tidak ditemukan."}, 404)

        def do_POST(self):
            parsed = urlparse(self.path)

            if parsed.path != "/download":
                self._send_json({"ok": False, "error": "Endpoint tidak ditemukan."}, 404)
                return

            length = int(self.headers.get("content-length", 0))
            raw_body = self.rfile.read(length).decode("utf-8")

            try:
                payload = json.loads(raw_body) if raw_body else {}
            except json.JSONDecodeError:
                self._send_json({"ok": False, "error": "JSON tidak valid."}, 400)
                return

            url = str(payload.get("url", "")).strip()
            filename = payload.get("filename")
            download_dir = payload.get("download_dir")
            referrer = payload.get("referrer")

            if not url:
                self._send_json({"ok": False, "error": "URL kosong."}, 400)
                return

            try:
                task_id, output_path = manager.start_download(
                    url,
                    filename=filename or None,
                    download_dir=download_dir or None,
                    referrer=referrer or None,
                )
            except DownloadCancelled as exc:
                self._send_json({"ok": False, "error": str(exc)}, 409)
                return

            self._send_json(
                {"ok": True, "task_id": task_id, "output_path": output_path},
                202,
            )

        def log_message(self, format, *args):
            print(f"[{self.log_date_time_string()}] {format % args}")

    return IDMRequestHandler


def main():
    parser = argparse.ArgumentParser(description="SimpleIDM local receiver")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--dir", default=DEFAULT_DOWNLOAD_DIR)
    parser.add_argument("--parts", type=int, default=8)
    parser.add_argument(
        "--ask-path",
        action="store_true",
        help="tampilkan dialog Save As untuk setiap download tanpa folder eksplisit",
    )
    args = parser.parse_args()

    manager = DownloadManager(
        download_dir=args.dir,
        parts=args.parts,
        ask_path=args.ask_path,
    )
    server = ThreadingHTTPServer((args.host, args.port), make_handler(manager))

    print(f"SimpleIDM aktif di http://{args.host}:{args.port}")
    print(f"Folder download: {os.path.abspath(args.dir)}")
    if args.ask_path:
        print("Mode pilih lokasi aktif: dialog Save As akan muncul sebelum download.")
    print("Kirim link ke POST /download atau pakai browser extension di folder extension/.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSimpleIDM dihentikan.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
