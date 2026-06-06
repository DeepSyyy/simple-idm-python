# SimpleIDM

SimpleIDM adalah downloader desktop sederhana yang menerima download dari browser, menampilkan progress, speed, path file, dan menyimpan hasil download ke folder default yang bisa dipilih dari aplikasi.

## Instal Aplikasi

1. Download installer `SimpleIDM-Setup.exe` dari halaman release.
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
3. Extension akan mengalihkan download ke SimpleIDM.
4. Progress dan speed akan muncul di window SimpleIDM.

Kamu juga bisa klik kanan link dan pilih `Download with SimpleIDM`.

## Catatan

Jika SimpleIDM belum terbuka, extension akan mengembalikan download ke browser.

Beberapa server tidak mengirim ukuran file (`Content-Length`). Untuk link seperti itu aplikasi tetap download biasa, tetapi progress persentase mungkin tidak tersedia.

Extension browser belum dipublish ke Chrome Web Store atau Firefox Add-ons, jadi pemasangan extension masih manual dari folder installer.
