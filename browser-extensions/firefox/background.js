const APP_URL = "http://127.0.0.1:8765/download";
const extensionApi = typeof browser !== "undefined" ? browser : chrome;
const capturedDownloadIds = new Set();

extensionApi.runtime.onInstalled.addListener(() => {
  extensionApi.contextMenus.create({
    id: "simpleidm-download-link",
    title: "Download with SimpleIDM",
    contexts: ["link"]
  });
});

async function sendToSimpleIDM(url, filename, referrer) {
  const cleanFilename = filename ? filename.split(/[\\/]/).pop() : undefined;
  const response = await fetch(APP_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ url, filename: cleanFilename, referrer })
  });
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(payload.error || `SimpleIDM returned HTTP ${response.status}`);
  }

  return payload;
}

function notify(title, message) {
  extensionApi.notifications.create({
    type: "basic",
    iconUrl: "icon.svg",
    title,
    message
  });
}

function downloadAction(action, ...args) {
  if (typeof browser !== "undefined") {
    return extensionApi.downloads[action](...args);
  }

  return new Promise((resolve, reject) => {
    extensionApi.downloads[action](...args, (...callbackArgs) => {
      const error = extensionApi.runtime.lastError;

      if (error) {
        reject(new Error(error.message));
        return;
      }

      resolve(callbackArgs[0]);
    });
  });
}

async function cancelBrowserDownload(downloadId) {
  await downloadAction("cancel", downloadId);

  try {
    await downloadAction("erase", { id: downloadId });
  } catch (error) {
    // Some browsers keep cancelled download history entries. That is harmless.
  }
}

extensionApi.contextMenus.onClicked.addListener(async (info) => {
  if (info.menuItemId !== "simpleidm-download-link" || !info.linkUrl) {
    return;
  }

  try {
    await sendToSimpleIDM(info.linkUrl, undefined, info.pageUrl);
    notify("SimpleIDM", "Link dikirim ke aplikasi.");
  } catch (error) {
    notify("SimpleIDM belum aktif", "Jalankan aplikasi SimpleIDM dulu.");
  }
});

extensionApi.downloads.onCreated.addListener(async (downloadItem) => {
  if (!downloadItem.url || !downloadItem.url.startsWith("http")) {
    return;
  }

  if (capturedDownloadIds.has(downloadItem.id)) {
    return;
  }

  capturedDownloadIds.add(downloadItem.id);

  try {
    await cancelBrowserDownload(downloadItem.id);
  } catch (error) {
    notify("SimpleIDM", `Gagal mengambil alih download browser: ${error.message}`);
    return;
  }

  try {
    await sendToSimpleIDM(
      downloadItem.url,
      downloadItem.filename,
      downloadItem.referrer
    );
    notify("SimpleIDM", "Download browser dialihkan ke aplikasi.");
  } catch (error) {
    notify("SimpleIDM", `${error.message} Download dibatalkan.`);
  }
});
