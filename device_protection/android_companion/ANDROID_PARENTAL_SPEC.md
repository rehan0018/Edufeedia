# EduFeedia Android Parental Companion & Safe Browser Architecture

## 1. Executive Overview
EduFeedia separates **In-App Educational Content Safety** (Layer 1) from **Device-Wide Parental Protection** (Layer 2). While the web/mobile platform protects the internal curated learning experience, the **EduFeedia Android Companion & Safe Browser** provides operating system-level protection when the child leaves the EduFeedia app.

```
+-------------------------------------------------------------------------+
|                  EDUFEEDIA DEVICE-WIDE PROTECTION ECOSYSTEM             |
+-------------------------------------------------------------------------+
|  1. EduFeedia Safe Browser (Dedicated Chromium/GeckoView Kiosk)        |
|  2. Android Companion Service (VpnService + AccessibilityService)       |
|  3. Chrome/Chromium Browser Extension (Manifest V3)                     |
|  4. Cloud Device Protection API (/api/v1/device-protection)             |
+-------------------------------------------------------------------------+
```

---

## 2. Technical Component Architecture

### A. Local Loopback DNS Filter (`android.net.VpnService`)
- **Mechanism:** Runs an on-device local TUN interface (`VpnService.Builder`) intercepting port 53 (DNS) UDP/TCP traffic without routing child data through remote proxy servers.
- **Privacy Assurance:** Zero external logging of innocent traffic; DNS resolution occurs locally against a cached high-trust whitelist and the local EduFeedia blocklist.
- **SafeSearch Enforcement:**
  - Overrides DNS lookups for `google.com` to `forcesafesearch.google.com` (`216.239.38.120`).
  - Overrides `bing.com` to `strict.bing.com` (`204.79.197.220`).
  - Enforces YouTube Restricted Mode via `restrict.youtube.com`.

### B. App & Browser Inspection (`android.accessibilityservice.AccessibilityService`)
- **App Launch Interception:** Listens to `TYPE_WINDOW_STATE_CHANGED` events. When a blacklisted or unapproved application is launched outside allowed screen hours, displays the EduFeedia Bedtime/Curfew lock screen.
- **Third-Party Browser URL Bar Monitoring:** Inspects URL navigation in Chrome, Edge, Brave, and Firefox on Android. If an adult, gambling, or phishing domain is entered, immediately injects the EduFeedia Block Screen and dispatches an alert to `/api/v1/device-protection/report-event`.

### C. Tamper Protection & Parent PIN Protection
- **Device Administrator API:** Prevents unauthorized child uninstallation without entering the 4-digit Parent PIN.
- **Heartbeat & Tamper Watchdog:** Pings the EduFeedia backend `/api/v1/device-protection/policy/{child_id}` every 15 minutes. If VPN or accessibility permissions are revoked, the parent receives an immediate Push Notification via Firebase Cloud Messaging (FCM).

---

## 3. Data Flow

```
[Child opens browser / app]
           │
           ▼
[Android Accessibility / VpnService]
           │
           ├─► Domain in Trusted Educational Whitelist? ──► ALLOW (Zero delay)
           │
           ├─► Domain in Prohibited Categories?
           │         │
           │         ▼
           │     [BLOCK] ──► Redirect to EduFeedia Block Screen
           │                     │
           │                     ▼
           │               Log to SafetyIncident Table
           │                     │
           │                     ▼
           │               Parent Notification Dispatched
           │
           └─► Uncategorized Web ──► Query /api/v1/device-protection/verify-url
```

---

## 4. Summary of Supported Devices & Phased Rollout
1. **Phase 1 (Completed):** EduFeedia Safe Shield Browser Extension (Manifest V3) & Device Protection API.
2. **Phase 2 (Completed):** Backend Real Safety Incident Logging and Verification Gate.
3. **Phase 3:** Android Companion APK utilizing `VpnService` for on-device loopback DNS filtering.
