# SimpleIDM Python

Downloader Python sederhana dengan multi-part download, resume per part, dan receiver lokal agar link dari browser bisa otomatis dikirim ke aplikasi.

## Jalankan Aplikasi

Aktifkan virtual environment yang sudah ada:

```bash
source venv/bin/activate
```

Jalankan GUI desktop:

```bash
python main.py --gui
```

Atau jalankan executable yang sudah dibuat:

```bash
./dist/SimpleIDM
```

Di GUI, download dari extension browser langsung diarahkan ke SimpleIDM dan disimpan ke folder default. Window utama menampilkan status, progress, path, dan kecepatan download. Centang `Tanya lokasi simpan sebelum download` kalau ingin memilih path untuk download tertentu.

Jalankan mode receiver:

```bash
python main.py --server
```

Kalau ingin setiap download dari browser langsung menanyakan lokasi simpan seperti IDM:

```bash
python main.py --server --ask-path
```

Default-nya aplikasi hidup di:

```text
http://127.0.0.1:8765
```

File akan disimpan ke folder `downloads/`.

Lihat progress download dengan progress bar di browser:

```text
http://127.0.0.1:8765/
```

Dashboard juga menampilkan kecepatan download, misalnya `3.2 MB/s`.

Pilih folder default penyimpanan saat menjalankan server:

```bash
python main.py --server --dir /home/user/Downloads
```

Kalau server dijalankan dengan `--ask-path`, download otomatis dari extension akan membuka dialog `Save As`. Jika dialog dibatalkan, download bawaan browser tidak akan dicancel.

Atau isi kolom `Folder tujuan opsional` di dashboard untuk memakai folder khusus tanpa memunculkan dialog.

## Build Executable

Install dependency:

```bash
pip install -r requirements.txt
```

Build executable:

```bash
python build_executable.py
```

Hasil build ada di:

```text
dist/SimpleIDM
```

Catatan: executable harus dibuild di OS target. Build dari Linux/WSL menghasilkan binary Linux. Untuk file `.exe` Windows, jalankan build di Windows.

## Build Installer Windows

Installer membuat user tidak perlu install Python. Installer membundel:

- `SimpleIDM.exe`
- folder `extension/`
- `README.md`
- shortcut Start Menu/Desktop

Langkah di Windows:

1. Install Python Windows.
2. Install Inno Setup: `https://jrsoftware.org/isinfo.php`
3. Build executable:

```powershell
python -m venv venv-win
venv-win\Scripts\activate
pip install -r requirements.txt
python build_executable.py
```

4. Build installer dengan Inno Setup:

```powershell
iscc installer\SimpleIDM.iss
```

Hasil installer:

```text
installer-output\SimpleIDM-Setup.exe
```

Catatan extension: browser modern tidak mengizinkan installer biasa memasang extension secara diam-diam. Setelah install aplikasi, user tetap perlu load extension dari folder install:

```text
C:\Program Files\SimpleIDM\extension
```

Untuk distribusi yang benar-benar sekali klik, extension harus dipublish ke Chrome Web Store / Firefox Add-ons, lalu README installer cukup mengarahkan user ke link extension tersebut.

## Install Extension Browser

Untuk Chrome, Edge, Brave, atau browser Chromium lain:

1. Buka `chrome://extensions`.
2. Aktifkan `Developer mode`.
3. Klik `Load unpacked`.
4. Pilih folder `extension/` di repo ini.
5. Pastikan GUI sedang berjalan lewat `./dist/SimpleIDM` atau `python main.py --gui`.

Setelah itu:

- Klik kanan link, lalu pilih `Download with SimpleIDM`.
- Atau mulai download biasa dari browser. Extension akan mencoba mengirim link ke aplikasi lokal dan membatalkan download browser jika berhasil.

Kalau aplikasi lokal belum aktif, download tetap berjalan di browser.

Jika file di folder `extension/` berubah, klik tombol reload pada extension di halaman extension browser.

## Install Extension Firefox

Firefox belum memakai `background.service_worker` seperti Chrome, jadi gunakan manifest khusus Firefox:

```bash
cp extension/manifest.firefox.json extension/manifest.json
```

Lalu:

1. Buka `about:debugging#/runtime/this-firefox`.
2. Klik `Load Temporary Add-on`.
3. Pilih `extension/manifest.json`.
4. Pastikan GUI sedang berjalan lewat `./dist/SimpleIDM` atau `python main.py --gui`.

Kalau ingin kembali ke Chrome/Edge:

```bash
cp extension/manifest.chrome.json extension/manifest.json
```

## Download Manual

Mode lama tetap bisa dipakai:

```bash
python main.py
```

Atau atur jumlah koneksi:

```bash
python main.py --parts 16
```

## API Lokal

Kirim download secara manual:

```bash
curl -X POST http://127.0.0.1:8765/download \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/file.zip","download_dir":"/home/user/Downloads"}'
```

Cek daftar task:

```bash
curl http://127.0.0.1:8765/tasks
```

## Catatan

Ini bukan crack IDM dan tidak membuka fitur berbayar IDM. Ini alternatif downloader buatan sendiri yang menerima link dari browser, lalu mendownload file dengan koneksi paralel jika server mendukung HTTP Range.

Beberapa server tidak mengirim ukuran file (`Content-Length`). Untuk link seperti itu aplikasi akan tetap download biasa, tetapi tidak memakai multi-part karena pembagian part membutuhkan ukuran total file.
