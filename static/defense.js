/**
 * defense.js — Client-side credential-exfiltration monitor
 * ----------------------------------------------------------
 * Drop this ONE script tag into a page (ideally as the very first
 * <script> in <head>, before any other script runs) and it will:
 *
 *   1. Watch every outgoing fetch() / XMLHttpRequest call.
 *   2. Flag requests whose body contains sensitive-looking field
 *      names (password, pass, pwd, card number, ssn, etc.).
 *   3. Flag requests going to a different origin than the page itself
 *      (a very common sign of data being exfiltrated to an attacker's
 *      server, e.g. http://localhost:5000/log from a page served
 *      elsewhere).
 *   4. Show a visible on-page warning banner naming the destination.
 *   5. Block the request by default (configurable below).
 *
 * This is a DETECTION/TEACHING tool, not a replacement for real
 * security (CSP, server-side validation, etc.) — it only sees what
 * happens in the page's own JS context, and a sufficiently obfuscated
 * attacker script could try to evade it. Good enough for a demo and
 * for the general pattern, not a production control.
 */

(function () {
  'use strict';

  const CONFIG = {
    blockSuspiciousRequests: true, // false = warn only, let it through
    sensitiveFieldNames: [
      'password', 'pass', 'pwd', 'passwd',
      'creditcard', 'credit_card', 'cardnumber', 'card_number',
      'cvv', 'ssn', 'social_security', 'pin'
    ],
    bannerDurationMs: 8000,
  };

  function showWarningBanner(message) {
    let banner = document.getElementById('__defense_banner__');
    if (!banner) {
      banner = document.createElement('div');
      banner.id = '__defense_banner__';
      banner.style.cssText = `
        position:fixed; top:0; left:0; right:0; z-index:999999;
        background:#dc2626; color:#fff; font-family:system-ui,sans-serif;
        font-size:14px; padding:14px 20px; text-align:center;
        box-shadow:0 2px 10px rgba(0,0,0,0.3);
      `;
      document.documentElement.appendChild(banner);
    }
    banner.textContent = message;
    banner.style.display = 'block';
    clearTimeout(banner._hideTimer);
    banner._hideTimer = setTimeout(() => {
      banner.style.display = 'none';
    }, CONFIG.bannerDurationMs);
  }

  function bodyLooksSensitive(bodyText) {
    if (!bodyText) return false;
    const lower = bodyText.toLowerCase();
    return CONFIG.sensitiveFieldNames.some((f) => lower.includes(f));
  }

  function isCrossOrigin(targetUrl) {
    try {
      const target = new URL(targetUrl, window.location.href);
      return target.origin !== window.location.origin;
    } catch (e) {
      return false;
    }
  }

  function handleSuspiciousRequest(url, bodyText) {
    const target = new URL(url, window.location.href);
    showWarningBanner(
      `⚠️ Blocked: this page tried to send sensitive-looking data to ${target.origin}`
    );
    console.warn('[defense.js] Suspicious outgoing request blocked:', {
      url,
      body: bodyText,
    });
  }

  // --- Patch fetch() ---
  const originalFetch = window.fetch;
  window.fetch = function (input, init) {
    const url = typeof input === 'string' ? input : input && input.url;
    const bodyText = init && init.body ? String(init.body) : '';

    if (url && bodyLooksSensitive(bodyText) && isCrossOrigin(url)) {
      handleSuspiciousRequest(url, bodyText);
      if (CONFIG.blockSuspiciousRequests) {
        return Promise.reject(
          new Error('Request blocked by defense.js: looked like credential exfiltration')
        );
      }
    }
    return originalFetch.apply(this, arguments);
  };

  // --- Patch XMLHttpRequest ---
  const OriginalXHR = window.XMLHttpRequest;
  function PatchedXHR() {
    const xhr = new OriginalXHR();
    let _url = '';
    const originalOpen = xhr.open;
    const originalSend = xhr.send;

    xhr.open = function (method, url) {
      _url = url;
      return originalOpen.apply(xhr, arguments);
    };

    xhr.send = function (body) {
      const bodyText = body ? String(body) : '';
      if (_url && bodyLooksSensitive(bodyText) && isCrossOrigin(_url)) {
        handleSuspiciousRequest(_url, bodyText);
        if (CONFIG.blockSuspiciousRequests) {
          return; // swallow the send, request never goes out
        }
      }
      return originalSend.apply(xhr, arguments);
    };

    return xhr;
  }
  window.XMLHttpRequest = PatchedXHR;

  console.log('[defense.js] Credential-exfiltration monitor active.');
})();