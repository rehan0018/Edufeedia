/**
 * EduFeedia Safe Shield — Background Service Worker
 * Intercepts browser navigations, checks domains against EduFeedia Device Protection API,
 * and enforces SafeSearch parameter rewriting.
 */

const API_BASE = "http://127.0.0.1:8000/api/v1/device-protection";

// Active Protection State
let activeProfile = {
  childId: "c-aarav-07",
  childName: "Aarav",
  safeSearchEnforced: true,
  guardActive: true
};

// Load saved config from extension storage
chrome.storage.local.get(["edufeedia_profile"], (res) => {
  if (res.edufeedia_profile) {
    activeProfile = res.edufeedia_profile;
  }
});

// Intercept navigation
chrome.webNavigation.onBeforeNavigate.addListener(async (details) => {
  if (details.frameId !== 0) return; // Main frame only
  if (!activeProfile.guardActive) return;

  const url = details.url;
  // Ignore internal, extension, or local EduFeedia URLs
  if (url.startsWith("chrome://") || url.startsWith("chrome-extension://") || url.includes("127.0.0.1:5173")) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/verify-url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: url,
        child_id: activeProfile.childId,
        client_type: "browser_extension"
      })
    });

    if (res.ok) {
      const decision = await res.json();
      
      // If SafeSearch rewrite is advised:
      if (decision.safe_search_redirect && decision.safe_search_redirect !== url) {
        chrome.tabs.update(details.tabId, { url: decision.safe_search_redirect });
        return;
      }

      // If blocked:
      if (!decision.allowed) {
        const blockPageUrl = `http://127.0.0.1:5173/?blocked=true&category=${encodeURIComponent(decision.category)}&reason=${encodeURIComponent(decision.reason)}`;
        chrome.tabs.update(details.tabId, { url: blockPageUrl });
      }
    }
  } catch (err) {
    console.warn("[EduFeedia Shield]: Offline fail-closed check error:", err);
  }
});

// Listen to messages from popup or content script
chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
  if (req.type === "GET_STATUS") {
    sendResponse({ profile: activeProfile });
  } else if (req.type === "UPDATE_PROFILE") {
    activeProfile = { ...activeProfile, ...req.profile };
    chrome.storage.local.set({ edufeedia_profile: activeProfile });
    sendResponse({ status: "success" });
  }
  return true;
});
