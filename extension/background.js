const APP_URL = "http://127.0.0.1:8765/download";
const capturedDownloadIds = new Set();

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "simpleidm-download-link",
    title: "Download with SimpleIDM",
    contexts: ["link"]
  });
});

async function sendToSimpleIDM(url, filename) {
  const response = await fetch(APP_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ url, filename })
  });

  if (!response.ok) {
    throw new Error(`SimpleIDM returned HTTP ${response.status}`);
  }

  return response.json();
}

function notify(title, message) {
  chrome.notifications.create({
    type: "basic",
    iconUrl: "icon.svg",
    title,
    message
  });
}

chrome.contextMenus.onClicked.addListener(async (info) => {
  if (info.menuItemId !== "simpleidm-download-link" || !info.linkUrl) {
    return;
  }

  try {
    await sendToSimpleIDM(info.linkUrl);
    notify("SimpleIDM", "Link dikirim ke aplikasi.");
  } catch (error) {
    notify("SimpleIDM belum aktif", "Jalankan python idm_server.py dulu.");
  }
});

chrome.downloads.onCreated.addListener(async (downloadItem) => {
  if (!downloadItem.url || !downloadItem.url.startsWith("http")) {
    return;
  }

  if (capturedDownloadIds.has(downloadItem.id)) {
    return;
  }

  capturedDownloadIds.add(downloadItem.id);

  try {
    await sendToSimpleIDM(downloadItem.url, downloadItem.filename);
    chrome.downloads.cancel(downloadItem.id);
    chrome.downloads.erase({ id: downloadItem.id });
    notify("SimpleIDM", "Download browser dialihkan ke aplikasi.");
  } catch (error) {
    notify("SimpleIDM belum aktif", "Download tetap berjalan di browser.");
  }
});
