# SimpleIDM

Versi: `1.1.0`

SimpleIDM adalah downloader desktop sederhana yang menerima download dari browser, menampilkan progress, speed, path file, dan menyimpan hasil download ke folder default yang bisa dipilih dari aplikasi.

Format versi memakai `major.minor.fix`, misalnya `1.1.0` berarti rilis major 1, minor 1, dan fix bug 0.

## Instal Aplikasi

1. Download installer `SimpleIDM-Setup-1.1.0.exe` dari halaman release.
2. Jalankan installer.
3. Buka aplikasi `SimpleIDM` dari Start Menu atau desktop shortcut.
4. Klik `Pilih Folder Default` di aplikasi untuk menentukan lokasi penyimpanan download.

Biarkan aplikasi SimpleIDM tetap terbuka saat ingin menangkap download dari browser.

## Pasang Extension Browser

Installer menyertakan folder extension di:

```text
%LOCALAPPDATA%\Programs\SimpleIDM\browser-extensions
```

### Chrome, Edge, Brave

1. Buka `chrome://extensions`.
2. Aktifkan `Developer mode`.
3. Klik `Load unpacked`.
4. Pilih folder:

```text
%LOCALAPPDATA%\Programs\SimpleIDM\browser-extensions\chrome
```

### Firefox

1. Buka `about:debugging#/runtime/this-firefox`.
2. Klik `Load Temporary Add-on`.
3. Pilih file:

```text
%LOCALAPPDATA%\Programs\SimpleIDM\browser-extensions\firefox\manifest.json
```

## Cara Pakai

1. Buka aplikasi SimpleIDM.
2. Mulai download file dari browser seperti biasa.
3. SimpleIDM akan menampilkan konfirmasi file yang akan didownload.
4. Klik `Yes` untuk mengalihkan download ke SimpleIDM.
5. Klik `No` untuk membatalkan download.
6. Progress dan speed akan muncul di window SimpleIDM.

Kamu juga bisa klik kanan link dan pilih `Download with SimpleIDM`.

## Kategori Download

SimpleIDM otomatis menyimpan file ke folder kategori berdasarkan ekstensi file:

- `General`: file yang tidak masuk kategori tertentu.
- `Compressed`: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2`, `.xz`, `.iso`.
- `Documents`: `.pdf`, `.doc`, `.docx`, `.txt`, `.rtf`, `.odt`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.csv`, `.md`.
- `Music`: `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`, `.wma`.
- `Video`: `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`.
- `Programs`: `.exe`, `.msi`, `.apk`, `.dmg`, `.pkg`, `.deb`, `.rpm`, `.appimage`.

Contoh jika folder default adalah `Downloads`, file `.mp4` akan disimpan ke:

```text
Downloads\Video
```

## Catatan

Jika SimpleIDM belum terbuka, extension akan membatalkan download dan menampilkan notifikasi.

Beberapa server tidak mengirim ukuran file (`Content-Length`). Untuk link seperti itu aplikasi tetap download biasa, tetapi progress persentase mungkin tidak tersedia.

Extension membutuhkan permission cookies agar SimpleIDM bisa mendownload file yang membutuhkan session/login browser. Cookies hanya dikirim ke aplikasi lokal di `127.0.0.1`.

Extension browser belum dipublish ke Chrome Web Store atau Firefox Add-ons, jadi pemasangan extension masih manual dari folder installer.
