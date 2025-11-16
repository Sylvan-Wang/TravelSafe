// ===============================
// TravelNest · tn.js
// Country Info + Crisis / Safe Mode
// ===============================

(function () {
  const REST_COUNTRIES_BASE =
    "https://restcountries.com/v3.1/name/";

  // ---------- Demo / fallback country metadata ----------
  // risk_scores: 1 (low) – 5 (high)

  let COUNTRY_SAFETY = {};
  async function loadCountrySafetyJson() {
  try {
    const resp = await fetch("country_safety.json"); // 🔥 文件名要和你目录一致
    if (!resp.ok) {
      throw new Error("Failed to load country_safety.json");
    }
    COUNTRY_SAFETY = await resp.json();
    console.log("Loaded safety data:", Object.keys(COUNTRY_SAFETY).length, "countries");
  } catch (err) {
    console.error("Error loading safety JSON:", err);
    COUNTRY_SAFETY = {}; // fallback
  }
}


  // Helper to find fallback by name (case-insensitive)
  function findFallbackCountryByName(name) {
    if (!name) return null;
    const lower = name.trim().toLowerCase();
    const entries = Object.values(COUNTRY_SAFETY);
    return (
      entries.find(
        (c) =>
          c.name.toLowerCase() === lower ||
          (c.alt_names || []).some(
            (alt) => alt.toLowerCase() === lower
          )
      ) || null
    );
  }

  // ---------- State ----------
  let currentCountry = null; // { code, name, apiData, safety }

  // ---------- DOM helpers ----------
  function $(selector) {
    return document.querySelector(selector);
  }
  function $all(selector) {
    return Array.from(document.querySelectorAll(selector));
  }

  function setText(el, text) {
    if (!el) return;
    el.textContent = text;
  }

  function setHTML(el, html) {
    if (!el) return;
    el.innerHTML = html;
  }

  // ---------- REST Countries API ----------
  async function fetchCountryFromApi(query) {
    if (!query) throw new Error("Empty query");
    const trimmed = query.trim();
    const url =
      REST_COUNTRIES_BASE +
      encodeURIComponent(trimmed) +
      "?fullText=true&fields=name,cca2,region,subregion,capital,population,languages,currencies";

    const fallbackUrl =
      REST_COUNTRIES_BASE +
      encodeURIComponent(trimmed) +
      "?fields=name,cca2,region,subregion,capital,population,languages,currencies";

    // Try fullText first, then fallback to fuzzy search
    let res = await fetch(url);
    if (!res.ok) {
      res = await fetch(fallbackUrl);
      if (!res.ok) {
        throw new Error("Country not found in REST Countries");
      }
    }
    const data = await res.json();
    const item = Array.isArray(data) ? data[0] : data;

    return normalizeApiCountry(item);
  }

  function normalizeApiCountry(item) {
    if (!item) return null;
    const nameCommon =
      item.name && item.name.common ? item.name.common : "";
    const code = item.cca2 || "";
    const region = item.region || "";
    const subregion = item.subregion || "";
    const capital =
      Array.isArray(item.capital) && item.capital.length
        ? item.capital[0]
        : "N/A";

    const population = item.population || null;
    const languages = item.languages
      ? Object.values(item.languages)
      : [];
    const currencies = item.currencies
      ? Object.values(item.currencies).map((c) => c.name)
      : [];

    return {
      code,
      name: nameCommon,
      region,
      subregion,
      capital,
      population,
      languages,
      currencies
    };
  }

  function formatPopulation(num) {
    if (!num || isNaN(num)) return "N/A";
    if (num >= 1_000_000_000)
      return (num / 1_000_000_000).toFixed(1) + "B";
    if (num >= 1_000_000)
      return (num / 1_000_000).toFixed(1) + "M";
    if (num >= 1_000)
      return (num / 1_000).toFixed(1) + "K";
    return String(num);
  }

  // ---------- UI: Tab switching ----------
  function setupTabs() {
    const tabButtons = $all(".tn-tab-btn");
    const panels = {
      info: $("#tab-info"),
      crisis: $("#tab-crisis")
    };

    tabButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const tab = btn.getAttribute("data-tab");
        // Update buttons
        tabButtons.forEach((b) => {
          const isActive = b === btn;
          b.classList.toggle("tn-tab-btn-active", isActive);
          b.setAttribute(
            "aria-selected",
            isActive ? "true" : "false"
          );
        });
        // Update panels
        Object.entries(panels).forEach(([key, panel]) => {
          if (!panel) return;
          if (key === tab) {
            panel.hidden = false;
            panel.classList.add("tn-tab-panel-active");
          } else {
            panel.hidden = true;
            panel.classList.remove("tn-tab-panel-active");
          }
        });
      });
    });
  }

  // ---------- UI: Search + demo chips ----------
  function setupSearch() {
    const input = $("#country-search-input");
    const btn = $("#country-search-button");
    const errorEl = $("#country-search-error");
    const demoChips = $all(".tn-demo-country");

    async function triggerSearch(fromDemo) {
      const raw = fromDemo
        ? fromDemo
        : input.value && input.value.trim();
      if (!raw) {
        setText(
          errorEl,
          "Please type a country name (e.g. France, Japan, Italy)."
        );
        return;
      }
      setText(errorEl, "");
      await loadCountry(raw);
    }

    if (btn) {
      btn.addEventListener("click", () => {
        triggerSearch();
      });
    }

    if (input) {
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          triggerSearch();
        }
      });
    }

    demoChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        const country = chip.getAttribute("data-country");
        if (input && country) {
          input.value = country;
        }
        triggerSearch(country);
      });
    });
  }

  // ---------- Loading & merging country data ----------
  async function loadCountry(query) {
    const riskChip = $("#info-risk-chip");
    const summaryEl = $("#info-country-summary");
    const crisisOverview = $("#crisis-overview");
    const errorEl = $("#country-search-error");

    if (riskChip) {
      riskChip.className =
        "tn-badge tn-badge-neutral";
      setText(riskChip, "Loading…");
    }
    if (summaryEl) {
      setHTML(
        summaryEl,
        '<p class="tn-placeholder">Fetching country profile…</p>'
      );
    }
    if (crisisOverview) {
      setHTML(
        crisisOverview,
        '<p class="tn-placeholder">Preparing safety overview…</p>'
      );
    }

    let apiData = null;
    let safetyData = null;
    let usedFallback = false;

    try {
      apiData = await fetchCountryFromApi(query);
    } catch (err) {
      console.warn("REST Countries error:", err);
      setText(
        errorEl,
        "We couldn’t get live data for this country. Falling back to demo countries if available."
      );
    }

    if (apiData) {
      // Try to match safety data by code or name
      const byCode =
        COUNTRY_SAFETY[apiData.code] || null;
      const byName = findFallbackCountryByName(
        apiData.name
      );
      safetyData = byCode || byName || null;

      if (!safetyData) {
        // No specific safety profile, build a generic shell
        safetyData = buildGenericSafety(apiData);
      }
    } else {
      const fallbackCountry = findFallbackCountryByName(
        query
      );
      if (!fallbackCountry) {
        // No demo data, show generic error & stop
        renderNoCountrySelected();
        return;
      }
      usedFallback = true;
      apiData = {
        code: fallbackCountry.code,
        name: fallbackCountry.name,
        region: fallbackCountry.region,
        subregion: "",
        capital: "N/A",
        population: null,
        languages: [],
        currencies: []
      };
      safetyData = fallbackCountry;
    }

    currentCountry = {
      code: apiData.code,
      name: apiData.name,
      api: apiData,
      safety: safetyData,
      usedFallback
    };

    renderCountryInfo(currentCountry);
    renderCrisisInfo(currentCountry);
  }

  function buildGenericSafety(apiData) {
    return {
      code: apiData.code || "",
      name: apiData.name || "",
      region: apiData.region || "",
      overall_risk: "unknown",
      risk_scores: {
        crime: 3,
        political: 3,
        health: 3,
        natural_disaster: 3
      },
      top_risks: [
        "keep valuables close in busy areas",
        "check local news if something feels unusual"
      ],
      emergency_contacts: {
        police: "Local emergency number",
        ambulance: "Local medical emergency number",
        fire: "Local fire emergency number",
        note:
          "Look up the specific emergency numbers before or right after arrival."
      },
      mindset_tip:
        "Most trips go well. Keep a basic safety routine, share your itinerary with someone you trust, and stay aware of your surroundings.",
      playbook: {}
    };
  }

  function renderNoCountrySelected() {
    const riskChip = $("#info-risk-chip");
    const summaryEl = $("#info-country-summary");
    const metaEl = $("#info-country-meta");
    const riskBars = $("#info-risk-bars");
    const advisory = $("#info-advisory-text");
    const crisisOverview = $("#crisis-overview");
    const crisisContacts = $("#crisis-contacts");
    const playbook = $("#crisis-playbook");
    const aiAnswer = $("#crisis-ai-answer");

    if (riskChip) {
      riskChip.className =
        "tn-badge tn-badge-neutral";
      setText(riskChip, "No country selected");
    }
    if (summaryEl) {
      setHTML(
        summaryEl,
        '<p class="tn-placeholder">We couldn’t match this query to any live or demo country. Please try a different spelling, or use France / Japan / Italy for the demo.</p>'
      );
    }
    if (metaEl) {
      metaEl.innerHTML = "";
    }
    if (riskBars) {
      setHTML(
        riskBars,
        '<p class="tn-placeholder">Risk bars will appear once a supported country is loaded.</p>'
      );
    }
    if (advisory) {
      setText(
        advisory,
        "We could not map this query to a supported country. Try a different spelling or another example."
      );
    }
    if (crisisOverview) {
      setHTML(
        crisisOverview,
        '<p class="tn-placeholder">Select a supported country first. For the prototype, try France, Japan or Italy.</p>'
      );
    }
    if (crisisContacts) {
      crisisContacts.querySelectorAll("ul").forEach(
        (ul) => (ul.innerHTML = "")
      );
    }
    if (playbook) {
      setHTML(
        playbook,
        '<p class="tn-placeholder">Safety scenarios and steps will appear here once a country is selected.</p>'
      );
    }
    if (aiAnswer) {
      setHTML(
        aiAnswer,
        '<p class="tn-placeholder">Your answer will appear here as a short paragraph. In this prototype, it is generated on the client side using the offline safety JSON, but the UX is already shaped for a real AI backend.</p>'
      );
    }
  }

  // ---------- Render: Country Info ----------
  function renderCountryInfo(country) {
    if (!country) return;
    const { api, safety, usedFallback } = country;
    const summaryEl = $("#info-country-summary");
    const metaEl = $("#info-country-meta");
    const riskChip = $("#info-risk-chip");
    const riskBars = $("#info-risk-bars");
    const advisory = $("#info-advisory-text");

    // Summary
    if (summaryEl) {
      const regionText = api.region
        ? api.region +
          (api.subregion ? ` · ${api.subregion}` : "")
        : safety.region || "Region not specified";

      const usedText = usedFallback
        ? `<span class="tn-placeholder">Showing demo profile for ${escapeHtml(
            safety.name || api.name
          )} because live data was not available.</span>`
        : "";

      setHTML(
        summaryEl,
        `
        <p class="tn-section-text">
          You’re viewing a country-level brief for <strong>${escapeHtml(
            api.name
          )}</strong>. It combines live country data with a safety-oriented overlay focused on solo travel.
        </p>
        <p class="tn-section-text">
          Region: ${escapeHtml(
            regionText
          )}. This is a high-level orientation rather than a detailed neighborhood map.
        </p>
        ${usedText}
      `
      );
    }

    // Meta list
    if (metaEl) {
      const langs = api.languages.length
        ? api.languages.join(", ")
        : "N/A";
      const currs = api.currencies.length
        ? api.currencies.join(", ")
        : "N/A";

      metaEl.innerHTML = `
        <ul class="tn-country-meta-list">
          <li class="tn-country-meta-item">
            <span class="tn-meta-label">Capital</span>
            <span class="tn-meta-value">${escapeHtml(
              api.capital
            )}</span>
          </li>
          <li class="tn-country-meta-item">
            <span class="tn-meta-label">Population</span>
            <span class="tn-meta-value">${formatPopulation(
              api.population
            )}</span>
          </li>
          <li class="tn-country-meta-item">
            <span class="tn-meta-label">Languages</span>
            <span class="tn-meta-value">${escapeHtml(
              langs
            )}</span>
          </li>
          <li class="tn-country-meta-item">
            <span class="tn-meta-label">Currencies</span>
            <span class="tn-meta-value">${escapeHtml(
              currs
            )}</span>
          </li>
        </ul>
      `;
    }

    // Risk chip
    if (riskChip) {
      const overall = safety.overall_risk || "unknown";
      let label = "Risk: Unknown";
      let cls = "tn-badge tn-badge-neutral";
      if (overall === "low") {
        label = "Risk: Low for most trips";
        cls = "tn-badge tn-badge-low";
      } else if (overall === "medium") {
        label = "Risk: Mixed · stay aware";
        cls = "tn-badge tn-badge-medium";
      } else if (overall === "high") {
        label = "Risk: High · check advisories";
        cls = "tn-badge tn-badge-high";
      }
      riskChip.className = cls;
      setText(riskChip, label);
    }

    // Risk bars
    if (riskBars) {
      const scores = safety.risk_scores || {};
      const dims = [
        {
          key: "crime",
          label: "Crime / petty theft"
        },
        {
          key: "political",
          label: "Political stability"
        },
        {
          key: "health",
          label: "Health infrastructure"
        },
        {
          key: "natural_disaster",
          label: "Natural hazards"
        }
      ];

      riskBars.innerHTML = dims
        .map((d) => {
          const scoreRaw = scores[d.key] || 3;
          const score = Math.max(
            1,
            Math.min(5, scoreRaw)
          );
          const pct = (score / 5) * 100;
          return `
          <div class="tn-country-meta-item">
            <span class="tn-meta-label">${d.label}</span>
            <span class="tn-meta-value">
              <span style="
                display:inline-block;
                width:90px;
                height:6px;
                border-radius:999px;
                background:linear-gradient(90deg, rgba(0,122,255,0.1), rgba(0,122,255,0.5));
                position:relative;
                overflow:hidden;
                margin-right:6px;
              ">
                <span style="
                  position:absolute;
                  left:0;
                  top:0;
                  bottom:0;
                  width:${pct}%;
                  background:rgba(0,122,255,0.9);
                "></span>
              </span>
              ${score}/5
            </span>
          </div>
        `;
        })
        .join("");
    }

    // Advisory text
    if (advisory) {
      const name = safety.name || api.name;
      const risk = safety.overall_risk || "unknown";
      let riskSentence = "";
      if (risk === "low") {
        riskSentence = `${name} is generally considered low-risk for most visitors, especially in everyday situations.`;
      } else if (risk === "medium") {
        riskSentence = `${name} is usually fine for tourism, but certain situations or locations may need extra awareness.`;
      } else if (risk === "high") {
        riskSentence = `${name} can involve higher levels of risk, so checking current advisories before you go is important.`;
      } else {
        riskSentence =
          "Risk levels can vary across regions within the same country, and can change over time.";
      }

      setText(
        advisory,
        `${riskSentence} This interface is a simplified, education-oriented view built on top of live country data and your curated safety presets.`
      );
    }
  }

  // ---------- Render: Crisis Info ----------
  function renderCrisisInfo(country) {
    if (!country) return;
    const { api, safety } = country;

    const overview = $("#crisis-overview");
    const contacts = $("#crisis-contacts");
    const playbook = $("#crisis-playbook");
    const aiAnswer = $("#crisis-ai-answer");

    const name = safety.name || api.name;

    // Overview
    if (overview) {
      const risks = safety.top_risks || [];
      const chips = risks
        .slice(0, 3)
        .map(
          (r) =>
            `<span class="tn-chip tn-chip-soft" style="margin-right:4px;">${escapeHtml(
              r
            )}</span>`
        )
        .join("");

      setHTML(
        overview,
        `
        <p class="tn-section-text">
          You’re viewing <strong>${escapeHtml(
            name
          )}</strong> in Crisis / Safe Mode. This doesn’t mean something bad will happen; it simply gives you a plan if it does.
        </p>
        <p class="tn-section-text">
          Keep in mind that conditions can vary a lot between cities and regions. This view focuses on three things: what risks matter most for solo travelers, what mindset helps, and who you can contact quickly.
        </p>
        ${
          chips
            ? `<div style="margin-top:4px;">${chips}</div>`
            : ""
        }
        <p class="tn-section-text" style="margin-top:6px;">
          Mindset reminder: ${
            safety.mindset_tip
              ? escapeHtml(safety.mindset_tip)
              : "Move one step at a time, keep your phone charged, and give yourself permission to slow down and make safe choices."
          }
        </p>
      `
      );
    }

    // Contacts
    if (contacts) {
      const listId = "crisis-contacts-list";
      let ul = contacts.querySelector(
        "#" + listId
      );
      if (!ul) {
        ul = document.createElement("ul");
        ul.id = listId;
        ul.className = "tn-crisis-contacts-list";
        contacts.appendChild(ul);
      }
      const e = safety.emergency_contacts || {};
      ul.innerHTML = `
        <li class="tn-crisis-contacts-item">
          <span class="tn-meta-label">Police</span>
          <span class="tn-meta-value">${escapeHtml(
            e.police || "Check local emergency number"
          )}</span>
        </li>
        <li class="tn-crisis-contacts-item">
          <span class="tn-meta-label">Ambulance</span>
          <span class="tn-meta-value">${escapeHtml(
            e.ambulance ||
              "Check local medical emergency number"
          )}</span>
        </li>
        <li class="tn-crisis-contacts-item">
          <span class="tn-meta-label">Fire</span>
          <span class="tn-meta-value">${escapeHtml(
            e.fire ||
              "Check local fire emergency number"
          )}</span>
        </li>
        <li class="tn-crisis-contacts-item">
          <span class="tn-meta-label">Note</span>
          <span class="tn-meta-value">${escapeHtml(
            e.note ||
              "Save these numbers in your phone and on paper before you need them."
          )}</span>
        </li>
      `;
    }

    // Playbook
    if (playbook) {
      const pb = safety.playbook || {};
      const entries = Object.values(pb);
      if (!entries.length) {
        setHTML(
          playbook,
          '<p class="tn-placeholder">We don’t have scenario-specific steps for this country yet. For the demo, try France, Japan or Italy.</p>'
        );
      } else {
        playbook.innerHTML = entries
          .slice(0, 3)
          .map((scenario) => {
            const steps = (scenario.steps || [])
              .map(
                (s) =>
                  `<li class="tn-playbook-item">${escapeHtml(
                    s
                  )}</li>`
              )
              .join("");
            return `
            <div class="tn-section-block">
              <div class="tn-playbook-scenario-title">${escapeHtml(
                scenario.label
              )}</div>
              <ul class="tn-playbook-list">
                ${steps}
              </ul>
            </div>
          `;
          })
          .join("");
      }
    }

    // Reset AI answer placeholder
    if (aiAnswer) {
      setHTML(
        aiAnswer,
        '<p class="tn-placeholder">Describe what is happening, and we’ll generate a short paragraph using this country’s playbook. This is all client-side for now, but mirrors an AI assistant UX.</p>'
      );
    }
  }

  // ---------- Crisis Q&A (mock AI) ----------
  function setupCrisisQnA() {
    const form = $("#crisis-question-form");
    const input = $("#crisis-question-input");
    const answerEl = $("#crisis-ai-answer");

    if (!form || !input || !answerEl) return;

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const text =
        input.value && input.value.trim();
      if (!currentCountry) {
        setHTML(
          answerEl,
          '<p class="tn-section-text">Please search a country first so we can use the right safety playbook. For the demo, try France, Japan or Italy.</p>'
        );
        return;
      }
      if (!text) {
        setHTML(
          answerEl,
          '<p class="tn-section-text">Try to briefly describe what is happening – for example “I lost my passport and I am alone at the station”.</p>'
        );
        return;
      }

      const resp = generateMockGuidance(
        currentCountry,
        text
      );
      setHTML(
        answerEl,
        `<p class="tn-section-text">${escapeHtml(
          resp
        )}</p>`
      );
    });
  }

  function generateMockGuidance(country, question) {
    const { api, safety } = country;
    const q = question.toLowerCase();
    const name = safety.name || api.name;

    const pb = safety.playbook || {};
    let scenarioKey = null;

    if (
      /passport|id|identity|visa/.test(q)
    ) {
      scenarioKey =
        pb.lost_passport
          ? "lost_passport"
          : pb.theft
          ? "theft"
          : null;
    } else if (
      /theft|stolen|pickpocket|robbed|bag/.test(
        q
      )
    ) {
      scenarioKey =
        pb.theft
          ? "theft"
          : pb.lost_passport
          ? "lost_passport"
          : null;
    } else if (
      /protest|demonstration|strike|riot|unrest/.test(
        q
      )
    ) {
      scenarioKey =
        pb.protest_or_strike
          ? "protest_or_strike"
          : null;
    } else if (
      /earthquake|shake|tremor|quake/.test(
        q
      )
    ) {
      scenarioKey = pb.earthquake
        ? "earthquake"
        : null;
    } else if (
      /heat|hot|sun|sunburn/.test(q)
    ) {
      scenarioKey = pb.heat_wave
        ? "heat_wave"
        : null;
    } else if (
      /sick|ill|fever|injury|hurt|hospital/.test(
        q
      )
    ) {
      scenarioKey = pb.health_issue
        ? "health_issue"
        : null;
    }

    if (scenarioKey && pb[scenarioKey]) {
      const sc = pb[scenarioKey];
      const step1 = sc.steps?.[0] || "";
      const step2 = sc.steps?.[1] || "";
      const step3 = sc.steps?.[2] || "";
      return `You’re in ${name}, and it sounds like you’re going through a situation similar to “${sc.label}”. First, ${step1} Then, ${step2} If you still feel unsafe or unsure after these first steps, ${step3 ||
        "move to a busier, well-lit place and consider calling local emergency services or your embassy for support"} Remember you don’t need to solve everything at once – just one safe next step at a time is enough.`;
    }

    // Generic fallback
    return `Thanks for explaining what’s happening. Because this situation doesn’t match one of the preset scenarios for ${name}, start with the basics: move to a place that feels physically safe, make sure your phone has enough battery, and let at least one trusted person know where you are. If you feel in immediate danger, contact local emergency services or head into a hotel, café, or public transport hub to ask for help. You can also keep notes of time, place, and people involved for any later reports or insurance claims.`;
  }

  // ---------- Utils ----------
  function escapeHtml(str) {
    if (str == null) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // ---------- Init ----------
document.addEventListener("DOMContentLoaded", () => {
  loadCountrySafetyJson()   // 🔥 先加载 JSON
    .finally(() => {        // 无论成功失败，都继续初始化 UI
      setupTabs();
      setupSearch();
      setupCrisisQnA();
      renderNoCountrySelected();
    });
});

})();
