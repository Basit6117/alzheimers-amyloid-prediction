(() => {
  function initPrediction() {
    const form = document.querySelector("#predict-form");
    if (!form) return;

    const featureOrder = ["pT217_F", "AB42_AB40_F", "GFAP_Q", "APOE4", "AGE", "SEX"];
    const displayNames = { pT217_F: "pT217_F", AB42_AB40_F: "Aβ42/Aβ40 ratio", GFAP_Q: "GFAP_Q", AGE: "Age", APOE4: "APOE ε4", SEX: "Sex" };
    const fields = [...form.querySelectorAll("input, select")];
    const submitButton = form.querySelector('button[type="submit"]');
    const resetButton = document.querySelector("#reset-button");
    const entryView = document.querySelector("#entry-view");
    const resultsView = document.querySelector("#results-view");
    const factorList = document.querySelector("#factor-list");
    const submittedValues = document.querySelector("#submitted-values");

    function validationMessage(field) {
      if (field.validity.valueMissing) return "This field is required.";
      if (field.validity.rangeUnderflow || field.validity.rangeOverflow) return `Enter a value from ${field.min} to ${field.max}.`;
      if (field.validity.badInput) return "Enter a numeric value.";
      if (field.validity.stepMismatch) return "Enter a whole number (0 or 1).";
      return "";
    }

    function validateField(field) {
      const error = document.querySelector(`#${field.name}-error`);
      const message = validationMessage(field);
      field.setAttribute("aria-invalid", String(Boolean(message)));
      error.textContent = message;
      return !message;
    }

    fields.forEach((field) => {
      field.addEventListener("blur", () => validateField(field));
      field.addEventListener("input", () => { if (field.getAttribute("aria-invalid") === "true") validateField(field); });
    });

    function setLoading(isLoading) {
      submitButton.disabled = isLoading;
      resetButton.disabled = isLoading;
      submitButton.textContent = isLoading ? "Predicting..." : "Predict screening result";
    }

    function categoryMeaning(category) {
      return {
        Low: "The model estimates a lower Amyloid Positive probability within its training-cohort range.",
        Moderate: "The model estimates a middle-range Amyloid Positive probability within its training-cohort range.",
        Elevated: "The model estimates a higher Amyloid Positive probability within its training-cohort range.",
      }[category];
    }

    function renderFactors(factors) {
      factorList.replaceChildren();
      const maximum = Math.max(...factors.map((item) => Math.abs(item.contribution)), 0);
      factors.forEach((factor) => {
        const row = document.createElement("div");
        row.className = "factor-row";
        const header = document.createElement("div");
        header.className = "factor-row__header";
        const name = document.createElement("span");
        name.textContent = displayNames[factor.feature] || factor.feature;
        const direction = document.createElement("span");
        direction.className = factor.contribution >= 0 ? "factor-row__increase" : "factor-row__decrease";
        direction.textContent = `${factor.contribution >= 0 ? "Increases" : "Decreases"} model score (${factor.contribution.toFixed(3)})`;
        header.append(name, direction);
        const track = document.createElement("div");
        track.className = "factor-row__track";
        const bar = document.createElement("div");
        bar.className = `factor-row__bar ${factor.contribution >= 0 ? "factor-row__bar--increase" : "factor-row__bar--decrease"}`;
        bar.style.width = `${maximum ? (Math.abs(factor.contribution) / maximum) * 100 : 0}%`;
        track.append(bar);
        row.append(header, track);
        factorList.append(row);
      });
    }

    function renderSubmittedValues(payload) {
      submittedValues.replaceChildren();
      featureOrder.forEach((feature) => {
        const row = document.createElement("tr");
        const label = document.createElement("th");
        label.scope = "row";
        label.textContent = displayNames[feature];
        const value = document.createElement("td");
        value.textContent = feature === "APOE4" ? (payload[feature] ? "1 - carrier" : "0 - non-carrier") : feature === "SEX" ? (payload[feature] ? "1 - male" : "0 - female") : payload[feature];
        row.append(label, value);
        submittedValues.append(row);
      });
    }

    function showPrediction(data, payload) {
      const percentage = data.probability * 100;
      document.querySelector("#dashboard-probability").textContent = `${percentage.toFixed(1)}%`;
      const category = document.querySelector("#dashboard-category");
      category.textContent = `${data.category} probability`;
      category.className = `risk-badge risk-badge--${data.category.toLowerCase()}`;
      document.querySelector("#dashboard-meaning").textContent = categoryMeaning(data.category);
      document.querySelector("#results-summary-text").textContent = `${data.category} Amyloid Positive probability: ${percentage.toFixed(1)}%.`;
      const progress = document.querySelector("#gauge-progress");
      progress.style.strokeDasharray = `${Math.max(0, Math.min(1, data.probability)) * 251.33} 251.33`;
      progress.setAttribute("class", `gauge-progress gauge-progress--${data.category.toLowerCase()}`);
      renderFactors(data.top_factors);
      renderSubmittedValues(payload);
      entryView.hidden = true;
      resultsView.hidden = false;
      document.dispatchEvent(new CustomEvent("chat-panel:move", { detail: "results" }));
      resultsView.focus();
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!fields.map(validateField).every(Boolean)) {
        fields.find((field) => field.getAttribute("aria-invalid") === "true")?.focus();
        return;
      }
      const payload = Object.fromEntries(featureOrder.map((feature) => [feature, Number(form.elements[feature].value)]));
      setLoading(true);
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 10000);
      try {
        const response = await fetch("/api/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload), signal: controller.signal });
        if (!response.ok) throw new Error(`Prediction request failed with status ${response.status}`);
        showPrediction(await response.json(), payload);
      } catch (error) {
        console.error("Prediction request failed", error);
        window.alert(error.name === "AbortError" ? "The prediction request took too long. Please try again." : "The server could not produce a prediction. Check the values and try again.");
      } finally {
        window.clearTimeout(timeout);
        setLoading(false);
      }
    });

    resetButton.addEventListener("click", () => {
      form.reset();
      fields.forEach((field) => { field.setAttribute("aria-invalid", "false"); document.querySelector(`#${field.name}-error`).textContent = ""; });
    });

    document.querySelector("#new-screening-button").addEventListener("click", () => {
      resultsView.hidden = true;
      entryView.hidden = false;
      document.dispatchEvent(new CustomEvent("chat-panel:move", { detail: "entry" }));
      form.reset();
      entryView.querySelector("h1").focus();
    });
  }

  function initChat() {
    const chatPanel = document.querySelector("#chat-panel");
    const entryHost = document.querySelector("#entry-chat-host");
    const resultsHost = document.querySelector("#result-chat-host");
    const chatForm = document.querySelector("#chat-form");
    const messageField = document.querySelector("#chat-message");
    const sendButton = document.querySelector("#chat-send");
    const chatLog = document.querySelector("#chat-log");
    const chatHistory = [];
    const generalPrefix = "General Gemini information (not from the loaded literature): ";

    function movePanel(destination) {
      (destination === "results" ? resultsHost : entryHost).append(chatPanel);
    }

    function displayDocumentName(documentName) {
      if (/^BloodBiomarkerstoDetectAlzheimerDisease/i.test(documentName)) {
        return "Blood biomarkers & Alzheimer's";
      }
      const readable = documentName
        .replace(/\.pdf$/i, "")
        .replace(/([a-z])([A-Z])/g, "$1 $2")
        .replace(/\s+/g, " ")
        .trim();
      return readable.length > 30 ? `${readable.slice(0, 29).trimEnd()}…` : readable;
    }

    function groupedSources(sources) {
      const groups = new Map();
      sources.forEach((source) => {
        const pages = groups.get(source.doc) || [];
        if (!pages.includes(source.page)) pages.push(source.page);
        groups.set(source.doc, pages);
      });
      return [...groups.entries()].map(([documentName, pages]) => ({
        documentName,
        pages: pages.sort((left, right) => left - right),
      }));
    }

    function addMessage(role, text, sources = []) {
      const message = document.createElement("article");
      message.className = `chat-message chat-message--${role}`;
      const paragraph = document.createElement("p");
      const isGeneralGeminiAnswer = role === "assistant" && text.startsWith(generalPrefix);
      paragraph.textContent = isGeneralGeminiAnswer ? text.slice(generalPrefix.length) : text;
      message.append(paragraph);
      if (sources.length) {
        const sourceList = document.createElement("div");
        sourceList.className = "source-chips";
        sourceList.setAttribute("aria-label", "Sources from the loaded literature");
        groupedSources(sources).forEach((source) => {
          const reference = document.createElement("span");
          reference.className = "source-reference";
          const pageLabel = source.pages.length === 1 ? "p." : "pp.";
          reference.textContent = `Source · ${displayDocumentName(source.documentName)} · ${pageLabel} ${source.pages.join(", ")}`;
          reference.title = `${source.documentName} · ${pageLabel} ${source.pages.join(", ")}`;
          sourceList.append(reference);
        });
        message.append(sourceList);
      }
      if (isGeneralGeminiAnswer) {
        const provenance = document.createElement("p");
        provenance.className = "chat-message__provenance";
        provenance.textContent = "General Gemini information — not from the loaded literature.";
        message.append(provenance);
      }
      chatLog.append(message);
      chatLog.scrollTop = chatLog.scrollHeight;
    }

    function setChatLoading(isLoading) {
      sendButton.disabled = isLoading;
      messageField.disabled = isLoading;
      sendButton.textContent = isLoading ? "Sending..." : "Send";
      chatForm.setAttribute("aria-busy", String(isLoading));
      const existingIndicator = document.querySelector("#chat-typing");
      if (isLoading && !existingIndicator) {
        const indicator = document.createElement("p");
        indicator.id = "chat-typing";
        indicator.className = "chat-typing";
        indicator.textContent = "Searching the literature...";
        chatLog.append(indicator);
        chatLog.scrollTop = chatLog.scrollHeight;
      }
      if (!isLoading) existingIndicator?.remove();
    }

    async function sendMessage(question) {
      const message = question.trim();
      if (!message) {
        messageField.focus();
        return;
      }
      const history = chatHistory.slice();
      addMessage("user", message);
      chatHistory.push({ role: "user", content: message });
      messageField.value = "";
      setChatLoading(true);
      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message, history }),
        });
        if (!response.ok) throw new Error(`Chat request failed with status ${response.status}`);
        const data = await response.json();
        addMessage("assistant", data.answer, data.sources || []);
        chatHistory.push({ role: "assistant", content: data.answer });
      } catch (error) {
        console.error("Chat request failed", error);
        const fallback = "The educational chatbot is unavailable right now. Please try again shortly.";
        addMessage("assistant", fallback);
      } finally {
        setChatLoading(false);
        messageField.focus();
      }
    }

    chatForm.addEventListener("submit", (event) => {
      event.preventDefault();
      sendMessage(messageField.value);
    });
    document.querySelectorAll("[data-chat-question]").forEach((button) => button.addEventListener("click", () => {
      messageField.value = button.dataset.chatQuestion;
      messageField.focus();
    }));
    document.addEventListener("chat-panel:move", (event) => movePanel(event.detail));
    movePanel("entry");
  }

  initPrediction();
  initChat();
})();
