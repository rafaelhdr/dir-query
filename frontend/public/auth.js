(function () {
  var TOKEN_KEY = "authToken";
  var EMAIL_KEY = "authEmail";

  function getToken() {
    return sessionStorage.getItem(TOKEN_KEY);
  }

  function getEmail() {
    return sessionStorage.getItem(EMAIL_KEY);
  }

  function setSession(token, email) {
    sessionStorage.setItem(TOKEN_KEY, token);
    sessionStorage.setItem(EMAIL_KEY, email);
  }

  function clearSession() {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(EMAIL_KEY);
  }

  function isLoggedIn() {
    return !!getToken();
  }

  function authFetch(url, options) {
    options = options || {};
    var token = getToken();
    if (token) {
      options.headers = Object.assign({}, options.headers, {
        Authorization: "Bearer " + token,
      });
    }
    return fetch(url, options);
  }

  document.addEventListener("htmx:configRequest", function (evt) {
    var token = getToken();
    if (token) {
      evt.detail.headers["Authorization"] = "Bearer " + token;
    }
  });

  window.Auth = {
    getToken: getToken,
    getEmail: getEmail,
    setSession: setSession,
    clearSession: clearSession,
    isLoggedIn: isLoggedIn,
    fetch: authFetch,
  };
})();
