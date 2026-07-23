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

  window.Auth = {
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
      submit: async function (url, event, onSuccess) {
        this.error = "";
        this.submitting = true;
        try {
          var response = await Auth.fetch(url, {
            method: "POST",
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
