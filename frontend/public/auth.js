(function () {
  var TOKEN_KEY = "authToken";
  var EMAIL_KEY = "authEmail";

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function getEmail() {
    return localStorage.getItem(EMAIL_KEY);
  }

  function setSession(token, email) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(EMAIL_KEY, email);
  }

  function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(EMAIL_KEY);
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

  window.Auth = {
    TOKEN_KEY: TOKEN_KEY,
    getToken: getToken,
    getEmail: getEmail,
    setSession: setSession,
    clearSession: clearSession,
    isLoggedIn: isLoggedIn,
    fetch: authFetch,
  };

  window.apiForm = function () {
    return {
      error: "",
      submitting: false,
      submit: async function (url, event, onSuccess, method) {
        this.error = "";
        this.submitting = true;
        try {
          var response = await Auth.fetch(url, {
            method: method || "POST",
            body: new FormData(event.target),
          });
          var data;
          try {
            data = await response.json();
          } catch (e) {
            this.error = await response.text();
            return;
          }
          if (response.ok) {
            onSuccess(data);
          } else {
            this.error = data.detail || response.statusText;
          }
        } finally {
          this.submitting = false;
        }
      },
    };
  };
})();
