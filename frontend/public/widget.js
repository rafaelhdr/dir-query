// Embeddable Dir Query widget. Loaded via a <script> tag on a third-party
// page (see the "Make a widget for your website" modal on the ask page).
//
// Widget mode (default) - floating launcher bubble:
//   <script src="https://<origin>/widget.js" data-workspace="acme-corp"
//           data-position="bottom-right"></script>
//
// Inline mode - chat panel mounted directly into a container on the page:
//   <div id="dirquery-widget"></div>
//   <script src="https://<origin>/widget.js" data-workspace="acme-corp"
//           data-mode="inline" data-target="dirquery-widget"></script>
//
// Optional, either mode - customize the placeholder shown before the first
// question is asked (defaults to "Ask a question to get started."):
//   <script src="https://<origin>/widget.js" data-workspace="acme-corp"
//           data-empty-state-text="Ask me about my CV."></script>
//
// Runs inside an IIFE and renders into a single Shadow DOM host so neither
// the host page's styles leak in, nor this widget's styles leak onto the
// host page. Both modes share every behavior except how the panel is
// mounted: fetching the workspace name, submitting questions,
// streaming/rendering answers, conversation continuity, and attribution are
// identical code paths regardless of mode.
(function () {
  "use strict";

  var VALID_POSITIONS = ["bottom-right", "bottom-left"];
  var HISTORY_RENDER_THROTTLE_MS = 80;

  var currentScript = document.currentScript;
  if (!currentScript) {
    return;
  }

  var slug = currentScript.getAttribute("data-workspace");
  if (!slug) {
    console.error("Dir Query widget: missing data-workspace attribute");
    return;
  }

  var mode = currentScript.getAttribute("data-mode") === "inline" ? "inline" : "widget";

  var targetEl = null;
  if (mode === "inline") {
    var targetId = currentScript.getAttribute("data-target");
    targetEl = targetId ? document.getElementById(targetId) : null;
    if (!targetEl) {
      console.error(
        'Dir Query widget: data-target "' +
          (targetId || "") +
          '" does not match any element on the page; inline widget was not mounted'
      );
      return;
    }
  }

  var position = currentScript.getAttribute("data-position");
  if (VALID_POSITIONS.indexOf(position) === -1) {
    position = "bottom-right";
  }

  var emptyStateText =
    currentScript.getAttribute("data-empty-state-text") || "Ask a question to get started.";

  var origin = new URL(currentScript.src, window.location.href).origin;

  function apiUrl(path) {
    return origin + "/api" + path;
  }

  // marked/DOMPurify are vendored on the Dir Query origin, not guaranteed to
  // exist on the host page. Reuse them if the host page already loaded a
  // copy under those names; otherwise load our own and never overwrite an
  // existing global.
  var markdownReadyPromise = null;
  function loadMarkdownSupport() {
    if (markdownReadyPromise) {
      return markdownReadyPromise;
    }
    if (window.marked && window.DOMPurify) {
      markdownReadyPromise = Promise.resolve();
      return markdownReadyPromise;
    }
    function loadScript(src) {
      return new Promise(function (resolve, reject) {
        var script = document.createElement("script");
        script.src = src;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
      });
    }
    markdownReadyPromise = Promise.all([
      window.marked ? Promise.resolve() : loadScript(origin + "/marked.min.js"),
      window.DOMPurify ? Promise.resolve() : loadScript(origin + "/purify.min.js"),
    ]).catch(function (error) {
      console.error("Dir Query widget: failed to load markdown support", error);
    });
    return markdownReadyPromise;
  }

  var MARKDOWN_ALLOWED_TAGS = [
    "p",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "br",
    "code",
    "pre",
    "blockquote",
    "a",
  ];
  var MARKDOWN_ALLOWED_ATTR = ["href", "target", "rel"];

  function renderAnswer(text) {
    if (!window.marked || !window.DOMPurify) {
      // Markdown support failed to load: fall back to escaped plain text
      // rather than showing nothing.
      var div = document.createElement("div");
      div.textContent = text;
      return div.innerHTML;
    }
    var rawHtml = window.marked.parse(text);
    return window.DOMPurify.sanitize(rawHtml, {
      ALLOWED_TAGS: MARKDOWN_ALLOWED_TAGS,
      ALLOWED_ATTR: MARKDOWN_ALLOWED_ATTR,
    });
  }

  // Parses one SSE frame the same way the ask page does.
  function parseSseFrame(frame) {
    if (!frame || frame.startsWith(":")) {
      return null;
    }
    var eventType = "message";
    var dataLines = [];
    frame.split("\n").forEach(function (line) {
      if (line.startsWith("event:")) {
        eventType = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trim());
      }
    });
    if (dataLines.length === 0) {
      return null;
    }
    return { type: eventType, data: JSON.parse(dataLines.join("\n")) };
  }

  // Widget mode: fixed-size panel, hidden until the launcher reveals it.
  // Inline mode: panel fills its host container and is visible immediately.
  var panelSizingCss =
    mode === "inline"
      ? "position: static; width: 100%; height: 100%; display: flex;"
      : "position: fixed; bottom: 88px; " +
        (position === "bottom-left" ? "left: 20px;" : "right: 20px;") +
        " width: 320px; max-width: calc(100vw - 40px); height: 440px; max-height: calc(100vh - 120px);" +
        " display: none;";

  var CSS =
    "" +
    ":host { all: initial; }" +
    (mode === "inline" ? ":host { display: block; width: 100%; height: 100%; }" : "") +
    "* { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }" +
    (mode === "widget"
      ? ".launcher {" +
        "  position: fixed; bottom: 20px; " +
        (position === "bottom-left" ? "left: 20px;" : "right: 20px;") +
        "  width: 56px; height: 56px; border-radius: 50%;" +
        "  background: #2f3336; color: #fff; border: none; cursor: pointer;" +
        "  box-shadow: 0 2px 10px rgba(0,0,0,0.25); z-index: 2147483000;" +
        "  display: flex; align-items: center; justify-content: center;" +
        "}" +
        ".launcher svg { width: 26px; height: 26px; }"
      : "") +
    ".panel {" +
    "  " +
    panelSizingCss +
    "  background: #fff; border: 1px solid #e2e2e2;" +
    (mode === "widget" ? "  border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.2);" : "") +
    "  flex-direction: column; overflow: hidden; z-index: 2147483000;" +
    "}" +
    (mode === "widget" ? ".panel.open { display: flex; }" : "") +
    ".panel-header {" +
    "  padding: 12px 14px; background: #2f3336; color: #fff;" +
    "  display: flex; align-items: center; justify-content: space-between; font-size: 14px; font-weight: 600;" +
    "}" +
    ".panel-header button {" +
    "  background: none; border: none; color: #fff; cursor: pointer; font-size: 18px; line-height: 1; padding: 0 4px;" +
    "}" +
    ".messages { flex: 1; overflow-y: auto; padding: 12px; font-size: 13px; color: #26282a; }" +
    ".exchange { margin-bottom: 14px; }" +
    ".exchange-question { font-weight: 600; margin-bottom: 4px; }" +
    ".exchange-answer p { margin: 0 0 8px; }" +
    ".exchange-answer p:last-child { margin-bottom: 0; }" +
    ".exchange-loading, .exchange-error { color: #767676; font-style: italic; }" +
    ".exchange-error { color: #b3261e; }" +
    ".exchange-sources { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 6px; }" +
    ".exchange-sources a {" +
    "  font-size: 11px; color: #444; text-decoration: none; background: #f2f2f2;" +
    "  border-radius: 10px; padding: 2px 8px; border: 1px solid #e2e2e2;" +
    "}" +
    ".exchange-sources a:hover { background: #e8e8e8; }" +
    ".empty-state { color: #767676; font-size: 13px; }" +
    ".panel-form { display: flex; border-top: 1px solid #e2e2e2; padding: 8px; gap: 6px; }" +
    ".panel-form input {" +
    "  flex: 1; border: 1px solid #d5d5d5; border-radius: 6px; padding: 8px 10px; font-size: 13px; outline: none;" +
    "}" +
    ".panel-form button {" +
    "  border: none; background: #2f3336; color: #fff; border-radius: 6px; padding: 0 14px; cursor: pointer; font-size: 13px;" +
    "}" +
    ".panel-form button:disabled { opacity: 0.5; cursor: default; }" +
    ".footer { padding: 6px 10px; text-align: center; border-top: 1px solid #f0f0f0; }" +
    ".footer a { font-size: 11px; color: #9a9a9a; text-decoration: none; }" +
    ".footer a:hover { text-decoration: underline; }";

  var host = document.createElement("div");
  if (mode === "inline") {
    targetEl.appendChild(host);
  } else {
    document.body.appendChild(host);
  }
  var shadow = host.attachShadow({ mode: "open" });

  var style = document.createElement("style");
  style.textContent = CSS;
  shadow.appendChild(style);

  var launcher = null;
  if (mode === "widget") {
    launcher = document.createElement("button");
    launcher.className = "launcher";
    launcher.setAttribute("aria-label", "Open chat widget");
    launcher.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
      '<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>' +
      "</svg>";
    shadow.appendChild(launcher);
  }

  var panel = document.createElement("div");
  panel.className = "panel";
  panel.innerHTML =
    '<div class="panel-header">' +
    '<span class="workspace-name">Loading…</span>' +
    (mode === "widget"
      ? '<button type="button" class="close-btn" aria-label="Close">&times;</button>'
      : "") +
    "</div>" +
    '<div class="messages"><p class="empty-state"></p></div>' +
    '<form class="panel-form">' +
    '<input type="text" placeholder="Ask a question" required />' +
    '<button type="submit">Ask</button>' +
    "</form>" +
    '<div class="footer"><a href="' +
    origin +
    '" target="_blank" rel="noopener noreferrer">Powered by Dir Query</a></div>';
  shadow.appendChild(panel);
  panel.querySelector(".empty-state").textContent = emptyStateText;

  var workspaceNameEl = panel.querySelector(".workspace-name");
  var messagesEl = panel.querySelector(".messages");
  var formEl = panel.querySelector(".panel-form");
  var inputEl = formEl.querySelector("input");
  var submitButtonEl = formEl.querySelector("button");
  var closeButtonEl = panel.querySelector(".close-btn");

  var isOpen = false;
  var workspaceLoaded = false;
  var conversationId = null;

  function setOpen(open) {
    isOpen = open;
    panel.classList.toggle("open", open);
    if (open && !workspaceLoaded) {
      loadWorkspace();
    }
  }

  if (mode === "widget") {
    launcher.addEventListener("click", function () {
      setOpen(!isOpen);
    });
    closeButtonEl.addEventListener("click", function () {
      setOpen(false);
    });
  } else {
    // Inline mode has no launcher to reveal the panel: it's visible
    // immediately, so load the workspace right away.
    loadWorkspace();
  }

  function loadWorkspace() {
    workspaceLoaded = true;
    fetch(apiUrl("/workspaces/" + slug))
      .then(function (response) {
        if (!response.ok) {
          throw new Error("workspace not found");
        }
        return response.json();
      })
      .then(function (workspace) {
        workspaceNameEl.textContent = workspace.name;
      })
      .catch(function () {
        workspaceNameEl.textContent = "Unavailable";
        messagesEl.innerHTML =
          '<p class="exchange-error">This widget is currently unavailable.</p>';
        inputEl.disabled = true;
        submitButtonEl.disabled = true;
      });
  }

  function clearEmptyState() {
    var emptyState = messagesEl.querySelector(".empty-state");
    if (emptyState) {
      emptyState.remove();
    }
  }

  formEl.addEventListener("submit", function (event) {
    event.preventDefault();
    var question = inputEl.value.trim();
    if (!question) {
      return;
    }
    inputEl.value = "";
    submitQuestion(question);
  });

  function submitQuestion(question) {
    clearEmptyState();

    var exchangeEl = document.createElement("div");
    exchangeEl.className = "exchange";
    exchangeEl.innerHTML =
      '<p class="exchange-question"></p>' +
      '<p class="exchange-loading">Thinking…</p>';
    exchangeEl.querySelector(".exchange-question").textContent = question;
    messagesEl.appendChild(exchangeEl);
    messagesEl.scrollTop = messagesEl.scrollHeight;

    var formData = new FormData();
    formData.set("question", question);
    if (conversationId) {
      formData.set("conversation_id", conversationId);
    }

    inputEl.disabled = true;
    submitButtonEl.disabled = true;

    fetch(apiUrl("/w/" + slug + "/ask"), { method: "POST", body: formData })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("request failed");
        }
        return streamAnswer(exchangeEl, response);
      })
      .catch(function () {
        showError(exchangeEl, "Something went wrong asking your question. Please try again.");
      })
      .finally(function () {
        inputEl.disabled = false;
        submitButtonEl.disabled = false;
        inputEl.focus();
      });
  }

  function showError(exchangeEl, message) {
    var loading = exchangeEl.querySelector(".exchange-loading");
    if (loading) {
      loading.remove();
    }
    var errorEl = exchangeEl.querySelector(".exchange-error");
    if (!errorEl) {
      errorEl = document.createElement("p");
      errorEl.className = "exchange-error";
      exchangeEl.appendChild(errorEl);
    }
    errorEl.textContent = message;
  }

  function renderSources(exchangeEl, sources) {
    if (!sources.length) {
      return;
    }
    var sourcesEl = document.createElement("p");
    sourcesEl.className = "exchange-sources";
    sources.forEach(function (source) {
      var link = document.createElement("a");
      link.href = source.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = source.name;
      sourcesEl.appendChild(link);
    });
    exchangeEl.appendChild(sourcesEl);
  }

  function streamAnswer(exchangeEl, response) {
    return loadMarkdownSupport().then(function () {
      var loadingEl = exchangeEl.querySelector(".exchange-loading");
      var answerEl = null;
      var reader = response.body.getReader();
      var decoder = new TextDecoder();
      var buffer = "";
      var accumulated = "";
      var lastRenderedAt = 0;
      var sawToken = false;

      function ensureAnswerEl() {
        if (loadingEl) {
          loadingEl.remove();
          loadingEl = null;
        }
        if (!answerEl) {
          answerEl = document.createElement("div");
          answerEl.className = "exchange-answer";
          exchangeEl.appendChild(answerEl);
        }
        return answerEl;
      }

      function renderThrottled(force) {
        var now = Date.now();
        if (!force && now - lastRenderedAt < HISTORY_RENDER_THROTTLE_MS) {
          return;
        }
        lastRenderedAt = now;
        ensureAnswerEl().innerHTML = renderAnswer(accumulated);
        messagesEl.scrollTop = messagesEl.scrollHeight;
      }

      function pump() {
        return reader.read().then(function (chunk) {
          if (chunk.done) {
            if (!sawToken) {
              showError(
                exchangeEl,
                "Something went wrong asking your question. Please try again."
              );
            }
            return;
          }
          buffer += decoder.decode(chunk.value, { stream: true });

          var separatorIndex;
          while ((separatorIndex = buffer.indexOf("\n\n")) !== -1) {
            var frame = buffer.slice(0, separatorIndex);
            buffer = buffer.slice(separatorIndex + 2);
            var parsed = parseSseFrame(frame);
            if (!parsed) {
              continue;
            }

            if (parsed.type === "token") {
              sawToken = true;
              accumulated += parsed.data;
              renderThrottled(false);
            } else if (parsed.type === "done") {
              accumulated = parsed.data.answer;
              renderThrottled(true);
              renderSources(exchangeEl, parsed.data.sources || []);
              conversationId = parsed.data.conversation_id;
              return;
            } else if (parsed.type === "error") {
              showError(
                exchangeEl,
                (parsed.data && parsed.data.detail) ||
                  "Something went wrong answering your question. Please try again."
              );
              return;
            }
          }

          return pump();
        });
      }

      return pump();
    });
  }
})();
