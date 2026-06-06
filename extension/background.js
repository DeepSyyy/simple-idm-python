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
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(payload.error || `SimpleIDM returned HTTP ${response.status}`);
  }

  return payload;
}

function notify(title, message) {
  chrome.notifications.create({
    type: "basic",
    iconUrl: "icon.svg",
    title,
    message
  });
}

function downloadAction(action, ...args) {
  return new Promise((resolve, reject) => {
    chrome.downloads[action](...args, (...callbackArgs) => {
      const error = chrome.runtime.lastError;

      if (error) {
        reject(new Error(error.message));
        return;
      }

      resolve(callbackArgs[0]);
    });
  });
}

async function pauseBrowserDownload(downloadId) {
  try {
    await downloadAction("pause", downloadId);
    return true;
  } catch (error) {
    return false;
  }
}

async function resumeBrowserDownload(downloadId) {
  try {
    await downloadAction("resume", downloadId);
  } catch (error) {
    // If the browser cannot resume, keep the notification as the source of truth.
  }
}

async function cancelBrowserDownload(downloadId) {
  await downloadAction("cancel", downloadId);

  try {
    await downloadAction("erase", { id: downloadId });
  } catch (error) {
    // Some browsers keep cancelled download history entries. That is harmless.
  }
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

  const paused = await pauseBrowserDownload(downloadItem.id);

  try {
    await sendToSimpleIDM(downloadItem.url, downloadItem.filename);
    await cancelBrowserDownload(downloadItem.id);
    notify("SimpleIDM", "Download browser dialihkan ke aplikasi.");
  } catch (error) {
    if (paused) {
      await resumeBrowserDownload(downloadItem.id);
    }

    notify("SimpleIDM", `${error.message} Download tetap berjalan di browser.`);
  }
});
