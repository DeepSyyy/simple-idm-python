import os
import re
import threading
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import unquote, urlparse


class SimpleIDM:
    def __init__(self, url, output_path, parts=8, progress_callback=None, headers=None):
        self.url = url
        self.output_path = output_path
        self.parts = parts
        self.temp_dir = output_path + "_parts"
        self.progress_callback = progress_callback
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Accept-Encoding": "identity",
            "Connection": "keep-alive",
        }

        if headers:
            self.headers.update(headers)

        self._progress_lock = threading.Lock()
        self._downloaded_bytes = 0

    def _host(self):
        return urlparse(self.url).netloc.lower()

    def _is_rate_limited_host(self):
        host = self._host()
        return host == "gofile.io" or host.endswith(".gofile.io")

    def _request_with_retry(self, session, method, **kwargs):
        max_attempts = 4 if self._is_rate_limited_host() else 2
        last_response = None

        for attempt in range(max_attempts):
            response = session.request(method, self.url, **kwargs)
            last_response = response

            if response.status_code != 429:
                return response

            if attempt == max_attempts - 1:
                return response

            retry_after = response.headers.get("retry-after")

            try:
                delay = int(retry_after) if retry_after else 2 ** attempt
            except ValueError:
                delay = 2 ** attempt

            response.close()
            time.sleep(min(delay, 15))

        return last_response

    def _new_session(self):
        session = requests.Session()
        session.headers.update(self.headers)
        return session

    def _validate_response_type(self, response):
        extension = os.path.splitext(self.output_path)[1].lower()
        suspicious_extensions = self._binary_extensions()

        content_type = response.headers.get("content-type", "").lower()

        if extension in suspicious_extensions and (
            "text/html" in content_type
            or "text/plain" in content_type
            or "application/json" in content_type
        ):
            raise Exception(
                "Server mengirim halaman teks/HTML, bukan file asli. "
                "Kemungkinan butuh cookie/session browser."
            )

    def _validate_plausible_size(self, size):
        if not size:
            return

        extension = os.path.splitext(self.output_path)[1].lower()
        minimum_sizes = {
            ".mkv": 1024 * 1024,
            ".mp4": 1024 * 1024,
            ".avi": 1024 * 1024,
            ".mov": 1024 * 1024,
            ".webm": 1024 * 1024,
            ".rar": 1024,
            ".zip": 1024,
            ".7z": 1024,
            ".iso": 1024 * 1024,
            ".exe": 1024,
            ".msi": 1024,
        }
        minimum_size = minimum_sizes.get(extension)

        if minimum_size and size < minimum_size:
            raise Exception(
                f"Ukuran remote terlalu kecil untuk file {extension} "
                f"({size} bytes). Kemungkinan server mengirim halaman HTML/metadata, "
                "bukan file asli."
            )

    @staticmethod
    def _binary_extensions():
        return {
            ".zip",
            ".rar",
            ".7z",
            ".tar",
            ".gz",
            ".bz2",
            ".xz",
            ".iso",
            ".exe",
            ".msi",
            ".apk",
            ".mp3",
            ".wav",
            ".flac",
            ".mp4",
            ".mkv",
            ".avi",
            ".mov",
            ".webm",
        }

    def _validate_output_file(self):
        extension = os.path.splitext(self.output_path)[1].lower()

        if extension not in self._binary_extensions():
            return

        with open(self.output_path, "rb") as file:
            prefix = file.read(512).lstrip().lower()

        if (
            prefix.startswith(b"<!doctype html")
            or prefix.startswith(b"<html")
            or b"<title>" in prefix
        ):
            os.remove(self.output_path)
            raise Exception(
                "Server mengirim halaman HTML, bukan file asli. "
                "Download dibatalkan agar file tidak corrupt."
            )

    @staticmethod
    def filename_from_url(url, fallback="download.bin"):
        parsed = urlparse(url)
        name = os.path.basename(parsed.path.rstrip("/"))
        name = unquote(name).strip()
        name = re.sub(r'[\\/:*?"<>|]+', "_", name)
        return name or fallback

    @staticmethod
    def filename_from_headers(headers):
        disposition = headers.get("content-disposition", "")
        match = re.search(r'filename\*=UTF-8\'\'([^;]+)', disposition, re.I)

        if match:
            return unquote(match.group(1).strip().strip('"'))

        match = re.search(r'filename="?([^";]+)"?', disposition, re.I)

        if match:
            return match.group(1).strip()

        return None

    @staticmethod
    def unique_path(path):
        if not os.path.exists(path):
            return path

        base, ext = os.path.splitext(path)
        counter = 1

        while True:
            candidate = f"{base} ({counter}){ext}"

            if not os.path.exists(candidate):
                return candidate

            counter += 1

    @classmethod
    def output_path_for_url(cls, url, download_dir="downloads", filename=None):
        os.makedirs(download_dir, exist_ok=True)

        if not filename:
            filename = cls.filename_from_url(url)

        filename = re.sub(r'[\\/:*?"<>|]+', "_", filename).strip()
        filename = filename or "download.bin"
        return cls.unique_path(os.path.join(download_dir, filename))

    def _emit_progress(self, downloaded, total):
        if self.progress_callback:
            self.progress_callback(downloaded, total)

    def get_file_size(self):
        session = self._new_session()

        try:
            response = self._request_with_retry(
                session,
                "HEAD",
                allow_redirects=True,
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException:
            return None
        finally:
            session.close()

        size = response.headers.get("content-length")

        if size is None:
            return None

        try:
            return int(size)
        except ValueError:
            return None

    def check_range_support(self):
        session = self._new_session()
        headers = {
            "Range": "bytes=0-1"
        }

        response = self._request_with_retry(
            session,
            "GET",
            headers=headers,
            stream=True,
            allow_redirects=True,
            timeout=20
        )
        response.close()
        session.close()

        return response.status_code == 206

    def download_part(self, part_number, start, end, total_size):
        os.makedirs(self.temp_dir, exist_ok=True)

        part_path = os.path.join(self.temp_dir, f"part_{part_number}")

        downloaded = 0

        if os.path.exists(part_path):
            downloaded = os.path.getsize(part_path)

        if start + downloaded > end:
            return

        headers = {
            "Range": f"bytes={start + downloaded}-{end}"
        }

        session = self._new_session()
        response = self._request_with_retry(
            session,
            "GET",
            headers=headers,
            stream=True,
            allow_redirects=True,
            timeout=30
        )

        try:
            response.raise_for_status()
            self._validate_response_type(response)

            if response.status_code != 206:
                raise Exception(
                    f"Server mengabaikan range request untuk part {part_number}."
                )

            with open(part_path, "ab") as file:
                for chunk in response.iter_content(chunk_size=1024 * 512):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)
                        with self._progress_lock:
                            self._downloaded_bytes += len(chunk)
                            self._emit_progress(self._downloaded_bytes, total_size)

            expected_size = end - start + 1
            actual_size = os.path.getsize(part_path)

            if actual_size != expected_size:
                os.remove(part_path)
                raise Exception(
                    f"Ukuran part {part_number} tidak valid "
                    f"({actual_size} dari {expected_size} bytes)."
                )
        finally:
            response.close()
            session.close()

    def merge_parts(self, file_size):
        merged_size = 0

        with open(self.output_path, "wb") as output:
            for i in range(self.parts):
                part_path = os.path.join(self.temp_dir, f"part_{i}")
                merged_size += os.path.getsize(part_path)

                with open(part_path, "rb") as part_file:
                    output.write(part_file.read())

        if merged_size != file_size or os.path.getsize(self.output_path) != file_size:
            if os.path.exists(self.output_path):
                os.remove(self.output_path)

            raise Exception("Ukuran file hasil merge tidak sesuai. Download dibatalkan.")

        self._validate_output_file()

        for i in range(self.parts):
            part_path = os.path.join(self.temp_dir, f"part_{i}")
            os.remove(part_path)

        os.rmdir(self.temp_dir)

    def download_normal(self, total_size):
        session = self._new_session()
        response = self._request_with_retry(
            session,
            "GET",
            stream=True,
            allow_redirects=True,
            timeout=30
        )

        try:
            response.raise_for_status()
            self._validate_response_type(response)

            if total_size is None:
                size = response.headers.get("content-length")

                if size:
                    try:
                        total_size = int(size)
                    except ValueError:
                        total_size = 0
                else:
                    total_size = 0

            self._validate_plausible_size(total_size)

            downloaded = 0

            with open(self.output_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 512):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)
                        self._emit_progress(downloaded, total_size)

            if total_size and os.path.getsize(self.output_path) != total_size:
                if os.path.exists(self.output_path):
                    os.remove(self.output_path)

                raise Exception("Ukuran file hasil download tidak sesuai.")

            self._validate_output_file()
        finally:
            response.close()
            session.close()

    def _current_downloaded_parts_size(self):
        if not os.path.isdir(self.temp_dir):
            return 0

        downloaded = 0

        for name in os.listdir(self.temp_dir):
            downloaded += os.path.getsize(os.path.join(self.temp_dir, name))

        return downloaded

    def download(self):
        os.makedirs(os.path.dirname(self.output_path) or ".", exist_ok=True)

        if self._is_rate_limited_host():
            print("Host sensitif rate-limit terdeteksi. Download single stream dimulai...")
            self.download_normal(None)
            print("Download selesai.")
            return

        file_size = self.get_file_size()

        if file_size is None:
            print("Server tidak memberikan ukuran file.")
            print("Download biasa dimulai...")
            self.download_normal(None)
            print("Download selesai.")
            return

        self._validate_plausible_size(file_size)
        range_supported = self.check_range_support()

        print(f"Ukuran file: {file_size / 1024 / 1024:.2f} MB")

        if not range_supported or self.parts <= 1:
            print("Server tidak support resume/multi-part.")
            print("Download biasa dimulai...")
            self.download_normal(file_size)
            print("Download selesai.")
            return

        part_size = file_size // self.parts
        ranges = []

        for i in range(self.parts):
            start = i * part_size
            end = start + part_size - 1

            if i == self.parts - 1:
                end = file_size - 1

            ranges.append((i, start, end))

        print(f"Download multi-part dengan {self.parts} bagian...")
        self._downloaded_bytes = self._current_downloaded_parts_size()

        with ThreadPoolExecutor(max_workers=self.parts) as executor:
            futures = []

            for part_number, start, end in ranges:
                future = executor.submit(
                    self.download_part,
                    part_number,
                    start,
                    end,
                    file_size
                )
                futures.append(future)

            for future in futures:
                future.result()

        print("Menggabungkan file...")
        self.merge_parts(file_size)

        print("Download selesai.")
