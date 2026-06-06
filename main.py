import argparse
import os
from downloader import SimpleIDM
from idm_server import DEFAULT_DOWNLOAD_DIR, DEFAULT_HOST, DEFAULT_PORT, DownloadManager, make_handler
from http.server import ThreadingHTTPServer


def run_manual_download(parts, download_dir):
    url = input("Masukkan URL file: ").strip()
    filename = input("Masukkan nama file output (kosong = otomatis): ").strip()

    if not url:
        print("URL tidak boleh kosong.")
        return

    os.makedirs(download_dir, exist_ok=True)
    output_path = SimpleIDM.output_path_for_url(
        url,
        download_dir=download_dir,
        filename=filename or None,
    )

    downloader = SimpleIDM(
        url=url,
        output_path=output_path,
        parts=parts,
    )

    downloader.download()


def run_server(host, port, download_dir, parts, ask_path):
    manager = DownloadManager(
        download_dir=download_dir,
        parts=parts,
        ask_path=ask_path,
    )
    server = ThreadingHTTPServer((host, port), make_handler(manager))

    print(f"SimpleIDM aktif di http://{host}:{port}")
    print(f"Folder download: {os.path.abspath(download_dir)}")
    if ask_path:
        print("Mode pilih lokasi aktif: dialog Save As akan muncul sebelum download.")
    print("Install extension dari folder extension/ agar download browser dialihkan otomatis.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSimpleIDM dihentikan.")
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="SimpleIDM Python")
    parser.add_argument("--gui", action="store_true", help="jalankan aplikasi desktop")
    parser.add_argument("--server", action="store_true", help="jalankan penerima link dari browser")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--dir", default=DEFAULT_DOWNLOAD_DIR)
    parser.add_argument("--parts", type=int, default=8)
    parser.add_argument(
        "--ask-path",
        action="store_true",
        help="tampilkan dialog Save As untuk download dari browser/dashboard",
    )
    args = parser.parse_args()

    if args.gui:
        from gui_app import SimpleIDMApp
        import tkinter as tk

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
        return

    if args.server:
        run_server(args.host, args.port, args.dir, args.parts, args.ask_path)
        return

    run_manual_download(args.parts, args.dir)


if __name__ == "__main__":
    main()
