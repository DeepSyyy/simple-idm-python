import argparse
import os
import threading
import tkinter as tk
from http.server import ThreadingHTTPServer
from tkinter import filedialog, messagebox, simpledialog, ttk

from app_info import APP_NAME, APP_VERSION
from idm_server import DEFAULT_DOWNLOAD_DIR, DEFAULT_HOST, DEFAULT_PORT, DownloadCancelled, DownloadManager, make_handler


class SimpleIDMApp:
    def __init__(
        self,
        root,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        download_dir=DEFAULT_DOWNLOAD_DIR,
        parts=8,
        ask_path=False,
    ):
        self.root = root
        self.host = host
        self.port = port
        self.download_dir = download_dir
        self.parts = parts
        self.ask_path_var = tk.BooleanVar(value=ask_path)
        self.server = None
        self.server_thread = None
        self.progress_is_indeterminate = False

        self.manager = DownloadManager(
            download_dir=self.download_dir,
            parts=self.parts,
            ask_path=ask_path,
            path_chooser=self.ask_output_path,
            confirm_chooser=self.confirm_download,
        )

        self.root.title(f"{APP_NAME} {APP_VERSION}")
        self.root.geometry("980x560")
        self.root.minsize(760, 440)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self._build_styles()
        self._build_layout()
        self._start_server()
        self._refresh_tasks()

    def _build_styles(self):
        self.style = ttk.Style()

        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.colors = {
            "bg": "#eef2f7",
            "panel": "#ffffff",
            "text": "#172033",
            "muted": "#63708a",
            "line": "#d8e0ec",
            "blue": "#1f6feb",
            "green": "#188038",
            "red": "#d93025",
        }

        self.root.configure(bg=self.colors["bg"])
        self.style.configure("App.TFrame", background=self.colors["bg"])
        self.style.configure("Panel.TFrame", background=self.colors["panel"], relief="flat")
        self.style.configure("Title.TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=("Arial", 20, "bold"))
        self.style.configure("Muted.TLabel", background=self.colors["bg"], foreground=self.colors["muted"], font=("Arial", 10))
        self.style.configure("Panel.TLabel", background=self.colors["panel"], foreground=self.colors["text"], font=("Arial", 10))
        self.style.configure("Accent.TButton", font=("Arial", 10, "bold"))
        self.style.configure("Horizontal.TProgressbar", troughcolor="#e6ebf3", background=self.colors["blue"], bordercolor="#e6ebf3")
        self.style.configure("Treeview", rowheight=30, fieldbackground=self.colors["panel"], background=self.colors["panel"], foreground=self.colors["text"])
        self.style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    def _build_layout(self):
        outer = ttk.Frame(self.root, style="App.TFrame", padding=18)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer, style="App.TFrame")
        header.pack(fill="x")

        title_area = ttk.Frame(header, style="App.TFrame")
        title_area.pack(side="left", fill="x", expand=True)

        ttk.Label(title_area, text=f"{APP_NAME} {APP_VERSION}", style="Title.TLabel").pack(anchor="w")
        self.server_label = ttk.Label(
            title_area,
            text=f"Receiver aktif di http://{self.host}:{self.port}",
            style="Muted.TLabel",
        )
        self.server_label.pack(anchor="w", pady=(2, 0))

        actions = ttk.Frame(header, style="App.TFrame")
        actions.pack(side="right")

        ttk.Button(actions, text="Tambah URL", style="Accent.TButton", command=self.add_url).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Pilih Folder Default", command=self.choose_default_folder).pack(side="left")

        status_panel = ttk.Frame(outer, style="Panel.TFrame", padding=14)
        status_panel.pack(fill="x", pady=(16, 12))

        self.folder_label = ttk.Label(
            status_panel,
            text=f"Folder default: {os.path.abspath(self.download_dir)}",
            style="Panel.TLabel",
        )
        self.folder_label.pack(anchor="w")
        ttk.Label(
            status_panel,
            text="Download dari browser langsung diarahkan ke SimpleIDM dan disimpan ke folder default.",
            style="Panel.TLabel",
        ).pack(anchor="w", pady=(4, 0))
        ttk.Checkbutton(
            status_panel,
            text="Tanya lokasi simpan sebelum download",
            variable=self.ask_path_var,
            command=self.toggle_ask_path,
        ).pack(anchor="w", pady=(8, 0))

        columns = ("name", "category", "status", "progress", "speed", "path")
        self.tree = ttk.Treeview(outer, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="File")
        self.tree.heading("category", text="Kategori")
        self.tree.heading("status", text="Status")
        self.tree.heading("progress", text="Progress")
        self.tree.heading("speed", text="Speed")
        self.tree.heading("path", text="Path")
        self.tree.column("name", width=220, minwidth=160)
        self.tree.column("category", width=110, minwidth=90)
        self.tree.column("status", width=110, minwidth=90)
        self.tree.column("progress", width=120, minwidth=100)
        self.tree.column("speed", width=110, minwidth=90)
        self.tree.column("path", width=360, minwidth=220)
        self.tree.pack(fill="both", expand=True)

        bottom = ttk.Frame(outer, style="App.TFrame")
        bottom.pack(fill="x", pady=(12, 0))

        self.progress = ttk.Progressbar(bottom, mode="determinate", maximum=100)
        self.progress.pack(side="left", fill="x", expand=True)

        self.summary_label = ttk.Label(bottom, text="Belum ada download", style="Muted.TLabel")
        self.summary_label.pack(side="right", padx=(12, 0))

    def _start_server(self):
        try:
            self.server = ThreadingHTTPServer((self.host, self.port), make_handler(self.manager))
        except OSError as exc:
            messagebox.showerror(
                "SimpleIDM",
                f"Tidak bisa menjalankan receiver di {self.host}:{self.port}.\n\n{exc}",
                parent=self.root,
            )
            self.root.after(100, self.root.destroy)
            return

        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()

    def choose_default_folder(self):
        folder = filedialog.askdirectory(
            title="Pilih folder default download",
            initialdir=os.path.abspath(self.download_dir),
        )

        if not folder:
            return

        self.download_dir = folder
        self.manager.download_dir = folder
        os.makedirs(folder, exist_ok=True)
        self.folder_label.configure(text=f"Folder default: {os.path.abspath(folder)}")

    def toggle_ask_path(self):
        self.manager.ask_path = self.ask_path_var.get()

    def confirm_download(self, details):
        if threading.current_thread() is threading.main_thread():
            return self._show_confirm_dialog(details)

        event = threading.Event()
        result = {"confirmed": False}

        def confirm_on_main_thread():
            result["confirmed"] = self._show_confirm_dialog(details)
            event.set()

        self.root.after(0, confirm_on_main_thread)
        event.wait()
        return result["confirmed"]

    def _show_confirm_dialog(self, details):
        message = (
            "SimpleIDM akan mengambil alih download ini.\n\n"
            f"File: {details['filename']}\n"
            f"Kategori: {details['category']}\n"
            f"Simpan ke: {details['output_path']}\n\n"
            f"URL:\n{details['url']}\n\n"
            "Lanjutkan download?"
        )
        return messagebox.askyesno("Konfirmasi Download", message, parent=self.root)

    def ask_output_path(self, filename):
        if threading.current_thread() is threading.main_thread():
            return self._show_save_dialog(filename)

        event = threading.Event()
        result = {"path": None}

        def ask_on_main_thread():
            result["path"] = self._show_save_dialog(filename)
            event.set()

        self.root.after(0, ask_on_main_thread)
        event.wait()
        return result["path"]

    def _show_save_dialog(self, filename):
        return filedialog.asksaveasfilename(
            title="Simpan download sebagai",
            initialdir=os.path.abspath(self.download_dir),
            initialfile=filename,
            parent=self.root,
        )

    def add_url(self):
        url = simpledialog.askstring("Tambah download", "Masukkan URL file:", parent=self.root)

        if not url:
            return

        try:
            self.manager.start_download(url.strip())
        except DownloadCancelled:
            return
        except Exception as exc:
            messagebox.showerror("SimpleIDM", str(exc), parent=self.root)

    def _refresh_tasks(self):
        tasks = self.manager.snapshot()
        existing = set(self.tree.get_children())
        seen = set()
        active_count = 0
        finished_count = 0
        active_tasks = []

        for task_id, task in tasks.items():
            seen.add(task_id)
            values = self._task_values(task_id, task)

            if task_id in existing:
                self.tree.item(task_id, values=values)
            else:
                self.tree.insert("", "end", iid=task_id, values=values)

            if task["status"] in ("queued", "downloading"):
                active_count += 1
                active_tasks.append((task_id, task))
            elif task["status"] == "finished":
                finished_count += 1

        for item_id in existing - seen:
            self.tree.delete(item_id)

        if active_tasks:
            _, current_task = sorted(active_tasks, key=lambda item: int(item[0]))[-1]
            total = current_task.get("total") or 0
            downloaded = current_task.get("downloaded") or 0

            if total > 0:
                self._set_determinate_progress(min(100, downloaded / total * 100))
            else:
                self._set_indeterminate_progress()
        elif finished_count:
            self._set_determinate_progress(100)
        else:
            self._set_determinate_progress(0)

        self.summary_label.configure(text=f"{active_count} aktif, {finished_count} selesai")
        self.root.after(700, self._refresh_tasks)

    def _set_indeterminate_progress(self):
        if not self.progress_is_indeterminate:
            self.progress.configure(mode="indeterminate")
            self.progress.start(10)
            self.progress_is_indeterminate = True

    def _set_determinate_progress(self, value):
        if self.progress_is_indeterminate:
            self.progress.stop()
            self.progress_is_indeterminate = False

        self.progress.configure(value=value, mode="determinate")

    def _task_values(self, task_id, task):
        path = task.get("output_path") or ""
        name = os.path.basename(path) or f"Download #{task_id}"
        category = task.get("category", "General")
        status = task.get("status", "unknown")
        total = task.get("total") or 0
        downloaded = task.get("downloaded") or 0
        speed = task.get("speed") or 0

        if total > 0:
            progress = f"{downloaded / total * 100:.1f}%"
        elif downloaded:
            progress = f"{self._format_bytes(downloaded)}"
        else:
            progress = "-"

        if status == "failed" and task.get("error"):
            status = f"failed: {task['error']}"
        elif task.get("note") and status in ("queued", "downloading"):
            status = f"{status} ({task['note']})"

        return (
            name,
            category,
            status,
            progress,
            f"{self._format_bytes(speed)}/s",
            path,
        )

    @staticmethod
    def _format_bytes(value):
        value = float(value or 0)
        units = ("B", "KB", "MB", "GB", "TB")
        unit = 0

        while value >= 1024 and unit < len(units) - 1:
            value /= 1024
            unit += 1

        if unit == 0:
            return f"{value:.0f} {units[unit]}"

        return f"{value:.1f} {units[unit]}"

    def close(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()

        self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description="SimpleIDM desktop app")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--dir", default=DEFAULT_DOWNLOAD_DIR)
    parser.add_argument("--parts", type=int, default=8)
    parser.add_argument("--ask-path", action="store_true")
    args = parser.parse_args()

    root = tk.Tk()
    SimpleIDMApp(
        root,
        host=args.host,
        port=args.port,
        download_dir=args.dir,
        parts=args.parts,
        ask_path=args.ask_path,
    )
    root.mainloop()


if __name__ == "__main__":
    main()
