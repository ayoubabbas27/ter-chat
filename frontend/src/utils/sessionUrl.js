const SESSION_PARAM = "session";

export function getSessionIdFromUrl() {
  const value = new URLSearchParams(window.location.search).get(SESSION_PARAM);
  return value?.trim() || null;
}

/** Update the URL without reloading the page. Pass null to clear the session param. */
export function setSessionIdInUrl(sessionId) {
  const url = new URL(window.location.href);
  if (sessionId) {
    url.searchParams.set(SESSION_PARAM, sessionId);
  } else {
    url.searchParams.delete(SESSION_PARAM);
  }
  window.history.replaceState({}, "", url);
}
