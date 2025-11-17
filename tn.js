// ===============================
// TravelNest · tn.js
// Country Info + Crisis / Safe Mode
// ===============================

(function () {
  const REST_COUNTRIES_BASE = "https://restcountries.com/v3.1/name/";

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
      console.log(
        "Loaded safety data:",
        Object.keys(COUNTRY_SAFETY).length,
        "countries"
      );
    } catch (err) {
      console.error("Error loading safety JSON:", err);
      COUNTRY_SAFETY = {}; // fallback
    }
  }

  function isCoreCountry(code) {
    const safety = COUNTRY_SAFETY[code];
    return safety && safety.is_core_country === true;
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
          (c.alt_names || []).some((alt) => alt.toLowerCase() === lower)
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
    const nameCommon = item.name && item.name.common ? item.name.common : "";
    const code = item.cca2 || "";
    const region = item.region || "";
    const subregion = item.subregion || "";
    const capital =
      Array.isArray(item.capital) && item.capital.length
        ? item.capital[0]
        : "N/A";

    const population = item.population || null;
    const languages = item.languages ? Object.values(item.languages) : [];
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
      currencies,
    };
  }

  function formatPopulation(num) {
    if (!num || isNaN(num)) return "N/A";
    if (num >= 1_000_000_000) return (num / 1_000_000_000).toFixed(1) + "B";
    if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + "M";
    if (num >= 1_000) return (num / 1_000).toFixed(1) + "K";
    return String(num);
  }

  // ---------- UI: Tab switching ----------
  function setupTabs() {
    const tabButtons = $all(".tn-tab-btn");
    const panels = {
      info: $("#tab-info"),
      crisis: $("#tab-crisis"),
    };

    tabButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const tab = btn.getAttribute("data-tab");
        // Update buttons
        tabButtons.forEach((b) => {
          const isActive = b === btn;
          b.classList.toggle("tn-tab-btn-active", isActive);
          b.setAttribute("aria-selected", isActive ? "true" : "false");
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
      const raw = fromDemo ? fromDemo : input.value && input.value.trim();
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

    // Wait for safety data to load if not already loaded
    if (Object.keys(COUNTRY_SAFETY).length === 0) {
      await loadCountrySafetyJson();
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
        "We couldn't get live data for this country. Falling back to demo countries if available."
      );
    }

    if (apiData) {
      // Try to match safety data by code first (most reliable)
      const byCode = COUNTRY_SAFETY[apiData.code] || null;
      if (byCode) {
        safetyData = byCode;
        console.log(
          `✓ Matched by code: ${apiData.code} -> ${safetyData.name}`,
          {
            risk_scores: safetyData.risk_scores,
            overall_risk: safetyData.overall_risk,
            full_data: safetyData,
          }
        );
      } else {
        // Fallback to name matching
        const byName = findFallbackCountryByName(apiData.name);
        if (byName) {
          safetyData = byName;
          console.log(`✓ Matched by name: ${apiData.name} -> ${byName.name}`, {
            risk_scores: safetyData.risk_scores,
            overall_risk: safetyData.overall_risk,
          });
        } else {
          // No match found - this should be rare since we have 250 countries
          console.warn(
            `⚠ No safety data found for ${apiData.name} (${
              apiData.code
            }). Total loaded: ${Object.keys(COUNTRY_SAFETY).length}`
          );
          safetyData = buildGenericSafety(apiData);
        }
      }
    } else {
      const fallbackCountry = findFallbackCountryByName(query);
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
        currencies: [],
      };
      safetyData = fallbackCountry;
    }

    currentCountry = {
      code: apiData.code,
      name: apiData.name,
      api: apiData,
      safety: safetyData,
      usedFallback,
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
        natural_disaster: 3,
      },
      top_risks: [
        "keep valuables close in busy areas",
        "check local news if something feels unusual",
      ],
      emergency_contacts: {
        police: "Local emergency number",
        ambulance: "Local medical emergency number",
        fire: "Local fire emergency number",
        note: "Look up the specific emergency numbers before or right after arrival.",
      },
      mindset_tip:
        "Most trips go well. Keep a basic safety routine, share your itinerary with someone you trust, and stay aware of your surroundings.",
      playbook: {},
    };
  }

  function renderNoCountrySelected() {
    const riskChip = $("#info-risk-chip");
    const introEl = $("#country-profile-intro");
    const regionEl = $("#country-profile-region");
    const metaEl = $("#info-country-meta");
    const riskBars = $("#info-risk-bars");
    const advisory = $("#safety-advisory");
    const crisisOverview = $("#crisis-overview");
    const crisisContacts = $("#crisis-contacts");
    const playbook = $("#crisis-playbook");
    const aiAnswer = $("#crisis-ai-answer");

    if (riskChip) {
      riskChip.className = "tn-badge tn-badge-neutral";
      setText(riskChip, "No country selected");
    }
    if (introEl) {
      setText(
        introEl,
        "Start by searching a country above. We'll show its region, capital, languages, currency, and a short safety-oriented summary tailored to solo travelers."
      );
    }
    if (regionEl) {
      setText(regionEl, "");
    }
    if (metaEl) {
      metaEl.innerHTML = "";
    }
    if (riskBars) {
      setHTML(
        riskBars,
        '<p class="tn-placeholder">Once a country is selected, you\'ll see a simple visual breakdown of four dimensions: crime, political stability, health infrastructure, and natural hazard exposure.</p>'
      );
    }
    if (advisory) {
      setText(
        advisory,
        "When possible, we map to an official travel advisory level (e.g. Level 1–4). If live data is unavailable, we fall back to curated demo values for a few sample countries."
      );
    }
    if (crisisOverview) {
      setHTML(
        crisisOverview,
        '<p class="tn-placeholder">Select a supported country first. For the prototype, try France, Japan or Italy.</p>'
      );
    }
    if (crisisContacts) {
      crisisContacts
        .querySelectorAll("ul")
        .forEach((ul) => (ul.innerHTML = ""));
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

  // =============== Text templates: data -> copy ===============

  // countryMeta 来自 REST Countries 的单个国家对象
  function buildCountryProfileText(countryMeta) {
    if (!countryMeta) {
      return {
        intro:
          "We couldn’t load this country’s profile. Please check your network or try another country.",
        region: "Region information is currently unavailable.",
        facts: {
          capital: "Unknown",
          population: "Unknown",
          languages: "Unknown",
          currency: "Unknown",
        },
      };
    }

    const name = countryMeta.name?.common ?? "this country";
    const region = countryMeta.region ?? "Unknown region";
    const subregion = countryMeta.subregion;
    const pop = countryMeta.population;
    const capital = Array.isArray(countryMeta.capital)
      ? countryMeta.capital[0]
      : countryMeta.capital;

    const languages = countryMeta.languages
      ? Object.values(countryMeta.languages).slice(0, 3)
      : [];

    const currencies = countryMeta.currencies
      ? Object.values(countryMeta.currencies)
          .map((c) => c.name)
          .slice(0, 2)
      : [];

    const populationStr = pop ? `${(pop / 1_000_000).toFixed(1)}M` : "N/A";

    const langStr = languages.length ? languages.join(", ") : "N/A";
    const currencyStr = currencies.length ? currencies.join(", ") : "N/A";
    const regionStr = subregion ? `${region} · ${subregion}` : region;

    return {
      intro: `You’re viewing a country-level brief for ${name}. It combines live country data with a safety-oriented overlay focused on solo travel.`,
      region: `Region: ${regionStr}. This is a high-level orientation rather than a detailed neighborhood map.`,
      facts: {
        capital: capital || "N/A",
        population: populationStr,
        languages: langStr,
        currency: currencyStr,
      },
    };
  }

  // safety 是你从 COUNTRY_SAFETY 里找出来的 JSON（可能为 null）
  function buildSafetySnapshotText(safety) {
    if (!safety) {
      return {
        header:
          "Risk levels are currently unknown for this country in your preset.",
        advisory:
          "Risk levels can vary across regions within the same country, and can change over time. This interface is a simplified, education-oriented view built on top of live country data and your curated safety presets.",
      };
    }

    const parts = [];

    const s = safety; // 方便写

    if (s.crime != null) {
      parts.push(
        `Crime and petty theft are at a level of ${scoreToLabel(
          s.crime
        )} for solo travelers.`
      );
    }
    if (s.politics != null) {
      parts.push(
        `Political environment shows ${scoreToLabel(
          s.politics
        )} sensitivity in terms of protests or policy shifts.`
      );
    }
    if (s.health != null) {
      parts.push(
        `Health infrastructure and access sit around a ${scoreToLabel(
          s.health
        )} level of strain.`
      );
    }
    if (s.natural != null) {
      parts.push(
        `Exposure to natural hazards (e.g. earthquakes, storms) is ${scoreToLabel(
          s.natural
        )}.`
      );
    }

    return {
      header: parts.join(" "),
      advisory:
        "This is a calm, education-focused snapshot. For real-world travel, always cross-check with official travel advisories and local guidance.",
    };
  }

  // 把 1–5 分转成 label
  function scoreToLabel(score) {
    if (score == null) return "no visible";
    if (score <= 2) return "relatively low";
    if (score === 3) return "moderate";
    return "heightened";
  }

  // ---------- Render: Country Info ----------
  function renderCountryInfo(country) {
    if (!country) return;
    const { api, safety, usedFallback } = country;
    console.log(`[DEBUG] renderCountryInfo called for ${api.name}:`, {
      safety,
      safety_risk_scores: safety?.risk_scores,
      safety_overall_risk: safety?.overall_risk,
    });

    const introEl = $("#country-profile-intro");
    const regionEl = $("#country-profile-region");
    const metaEl = $("#info-country-meta");
    const riskChip = $("#info-risk-chip");
    const riskBars = $("#info-risk-bars");
    const advisory = $("#safety-advisory");

    // Summary
    if (introEl) {
      const usedText = usedFallback
        ? `<span class="tn-placeholder">Showing demo profile for ${escapeHtml(
            safety.name || api.name
          )} because live data was not available.</span>`
        : "";

      setHTML(
        introEl,
        `You're viewing a country-level brief for <strong>${escapeHtml(
          api.name
        )}</strong>. It combines live country data with a safety-oriented overlay focused on solo travel. ${usedText}`
      );
    }

    if (regionEl) {
      const regionText = api.region
        ? api.region + (api.subregion ? ` · ${api.subregion}` : "")
        : safety.region || "Region not specified";

      setText(
        regionEl,
        `Region: ${escapeHtml(
          regionText
        )}. This is a high-level orientation rather than a detailed neighborhood map.`
      );
    }

    // Meta list
    if (metaEl) {
      const langs = api.languages.length ? api.languages.join(", ") : "N/A";
      const currs = api.currencies.length ? api.currencies.join(", ") : "N/A";

      metaEl.innerHTML = `
        <ul class="tn-country-meta-list">
          <li class="tn-country-meta-item">
            <span class="tn-meta-label">Capital</span>
            <span class="tn-meta-value">${escapeHtml(api.capital)}</span>
          </li>
          <li class="tn-country-meta-item">
            <span class="tn-meta-label">Population</span>
            <span class="tn-meta-value">${formatPopulation(
              api.population
            )}</span>
          </li>
          <li class="tn-country-meta-item">
            <span class="tn-meta-label">Languages</span>
            <span class="tn-meta-value">${escapeHtml(langs)}</span>
          </li>
          <li class="tn-country-meta-item">
            <span class="tn-meta-label">Currencies</span>
            <span class="tn-meta-value">${escapeHtml(currs)}</span>
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
      console.log(
        `[DEBUG] Rendering risk bars for ${safety.name || api.name}:`,
        {
          scores,
          overall_risk: safety.overall_risk,
          safety_keys: Object.keys(safety),
        }
      );

      const dims = [
        {
          key: "crime",
          label: "Crime / petty theft",
        },
        {
          key: "political",
          label: "Political stability",
        },
        {
          key: "health",
          label: "Health infrastructure",
        },
        {
          key: "natural_disaster",
          label: "Natural hazards",
        },
      ];

      riskBars.innerHTML = dims
        .map((d) => {
          const scoreRaw = scores[d.key];
          console.log(
            `[DEBUG] ${d.key}: scoreRaw=${scoreRaw}, type=${typeof scoreRaw}`
          );
          const score =
            scoreRaw != null ? Math.max(1, Math.min(5, Number(scoreRaw))) : 3;
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
  // ---------- Render: Crisis Info ----------
  function renderCrisisInfo(country) {
    if (!country) return;
    const { api, safety } = country;

    const overview = $("#crisis-overview");
    const contacts = $("#crisis-contacts");
    const playbook = $("#crisis-playbook");
    const aiAnswer = $("#crisis-ai-answer");

    if (!overview || !contacts || !playbook || !aiAnswer) return;

    const name = safety.name || api.name;
    const code = safety.code || api.code;

    // ===== 1. 非核心国家：Basic 模式 =====
    if (!isCoreCountry(code)) {
      setHTML(
        overview,
        `
      <p class="tn-section-text">
        You’re viewing a basic safety view for <strong>${escapeHtml(
          name
        )}</strong>. Detailed risk modelling and crisis playbooks are currently focused on major travel destinations.
      </p>
      <p class="tn-section-text">
        For this country, please check your government's travel advisory, confirm local emergency numbers with your accommodation,
        and use general solo travel safety habits (keep valuables close, stay in well-lit public areas, and share your plans with someone you trust).
      </p>
    `
      );
      // 不展示详细 playbook / contacts，避免假数据
      setHTML(
        playbook,
        '<p class="tn-placeholder">A detailed crisis playbook is not yet available for this country. Use the general guidance above as a baseline.</p>'
      );
      contacts.innerHTML = "";
      setHTML(
        aiAnswer,
        '<p class="tn-placeholder">Describe what is happening, and we’ll generate guidance here once this country has a detailed playbook. For now, follow general safety steps and official advisories.</p>'
      );
      return;
    }

    // ===== 2. 核心国家：Rich 模式 =====

    // 2.1 Overview + advisory excerpt + mindset + top risks
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

    let overviewHtml = `
    <p class="tn-section-text">
      You’re viewing <strong>${escapeHtml(
        name
      )}</strong> in Crisis / Safe Mode. This doesn’t mean something bad will happen; it simply gives you a calm backup plan if it does.
    </p>
    <p class="tn-section-text">
      This view focuses on three things: what risks matter most for solo travelers, what mindset helps, and who you can contact quickly.
    </p>
  `;

    // 来自真实 API 的摘要 + 链接
    if (safety.advisory_excerpt) {
      overviewHtml += `
      <p class="tn-advisory-note">
        Based on the latest advisory:
        <span class="tn-advisory-quote">“${escapeHtml(
          safety.advisory_excerpt
        )}”</span>
        ${
          safety.advisory_link
            ? `<a href="${escapeHtml(
                safety.advisory_link
              )}" target="_blank" rel="noopener" class="tn-advisory-link">
                View full advisory
              </a>`
            : ""
        }
      </p>
    `;
    }

    if (chips) {
      overviewHtml += `<div style="margin-top:4px;">${chips}</div>`;
    }

    overviewHtml += `
    <p class="tn-section-text" style="margin-top:6px;">
      Mindset reminder: ${
        safety.mindset_tip
          ? escapeHtml(safety.mindset_tip)
          : "Move one step at a time, keep your phone charged, and give yourself permission to slow down and make safe choices."
      }
    </p>
  `;

    setHTML(overview, overviewHtml);

    // 2.2 Contacts：对核心国家展示我们精细整理过的号码
    const c = safety.emergency_contacts || {};
    contacts.innerHTML = `
    <ul class="tn-crisis-contacts-list">
      ${
        c.unified
          ? `<li class="tn-crisis-contacts-item">
              <span class="tn-meta-label">Unified</span>
              <span class="tn-meta-value">${escapeHtml(c.unified)}</span>
             </li>`
          : ""
      }
      <li class="tn-crisis-contacts-item">
        <span class="tn-meta-label">Police</span>
        <span class="tn-meta-value">${escapeHtml(
          c.police || "Local police emergency number"
        )}</span>
      </li>
      <li class="tn-crisis-contacts-item">
        <span class="tn-meta-label">Ambulance</span>
        <span class="tn-meta-value">${escapeHtml(
          c.ambulance || "Local medical emergency number"
        )}</span>
      </li>
      <li class="tn-crisis-contacts-item">
        <span class="tn-meta-label">Fire</span>
        <span class="tn-meta-value">${escapeHtml(
          c.fire || "Local fire emergency number"
        )}</span>
      </li>
      <li class="tn-crisis-contacts-item">
        <span class="tn-meta-label">Note</span>
        <span class="tn-meta-value">${escapeHtml(
          c.note ||
            "Save these numbers in your phone and on paper before you need them."
        )}</span>
      </li>
    </ul>
  `;

    // 2.3 Playbook（用你已有的结构，只是搬过来）
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
            .map((s) => `<li class="tn-playbook-item">${escapeHtml(s)}</li>`)
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

    // 2.4 AI Q&A placeholder（核心国家）
    setHTML(
      aiAnswer,
      '<p class="tn-placeholder">Describe what is happening, and we’ll generate a short paragraph using this country’s playbook. This is all client-side for now, but mirrors an AI assistant UX.</p>'
    );
  }

  // ---------- Crisis Q&A (mock AI) ----------
  function setupCrisisQnA() {
    const form = $("#crisis-question-form");
    const input = $("#crisis-question-input");
    const answerEl = $("#crisis-ai-answer");

    if (!form || !input || !answerEl) return;

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const text = input.value && input.value.trim();
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

      const resp = generateMockGuidance(currentCountry, text);
      setHTML(answerEl, `<p class="tn-section-text">${escapeHtml(resp)}</p>`);
    });
  }

  function generateMockGuidance(country, question) {
    const { api, safety } = country;
    const q = question.toLowerCase();
    const name = safety.name || api.name;

    const pb = safety.playbook || {};
    let scenarioKey = null;

    if (/passport|id|identity|visa/.test(q)) {
      scenarioKey = pb.lost_passport
        ? "lost_passport"
        : pb.theft
        ? "theft"
        : null;
    } else if (/theft|stolen|pickpocket|robbed|bag/.test(q)) {
      scenarioKey = pb.theft
        ? "theft"
        : pb.lost_passport
        ? "lost_passport"
        : null;
    } else if (/protest|demonstration|strike|riot|unrest/.test(q)) {
      scenarioKey = pb.protest_or_strike ? "protest_or_strike" : null;
    } else if (/earthquake|shake|tremor|quake/.test(q)) {
      scenarioKey = pb.earthquake ? "earthquake" : null;
    } else if (/heat|hot|sun|sunburn/.test(q)) {
      scenarioKey = pb.heat_wave ? "heat_wave" : null;
    } else if (/sick|ill|fever|injury|hurt|hospital/.test(q)) {
      scenarioKey = pb.health_issue ? "health_issue" : null;
    }

    if (scenarioKey && pb[scenarioKey]) {
      const sc = pb[scenarioKey];
      const step1 = sc.steps?.[0] || "";
      const step2 = sc.steps?.[1] || "";
      const step3 = sc.steps?.[2] || "";
      return `You’re in ${name}, and it sounds like you’re going through a situation similar to “${
        sc.label
      }”. First, ${step1} Then, ${step2} If you still feel unsafe or unsure after these first steps, ${
        step3 ||
        "move to a busier, well-lit place and consider calling local emergency services or your embassy for support"
      } Remember you don’t need to solve everything at once – just one safe next step at a time is enough.`;
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

  // ---------- USC Support Demo ----------
  const USC_SUPPORT_DEMO = {
    intro:
      "When the traveler is a USC student, TravelSafe can attach USC-specific safety resources on top of the country view.",
    emergency: "+1 (213) 740-4321 (USC Department of Public Safety, demo)",
    insurance: "USC Student Health Insurance (demo link)",
    providers:
      "Pre-approved international medical providers list (demo placeholder).",
    embassy:
      "Nearest U.S. embassy / consulate contact details based on destination city (future integration).",
    advisories:
      "Region-specific advisories sourced from official government travel pages.",
    travelerReg:
      "USC / U.S. State Department traveler registration (e.g. STEP).",
    note: "This is a demo card using static USC-style data. In production, it can be wired to OIS / USC APIs and updated automatically.",
  };

  function renderUSCSupportDemo() {
    const data = USC_SUPPORT_DEMO;

    const introEl = $("#usc-layer-intro");
    const emerEl = $("#usc-emergency");
    const insEl = $("#usc-insurance");
    const provEl = $("#usc-providers");
    const embEl = $("#usc-embassy");
    const advEl = $("#usc-advisories");
    const regEl = $("#usc-traveler-reg");
    const noteEl = $("#usc-layer-note");

    if (!introEl) return; // 卡片不存在就直接返回，防止报错

    setText(introEl, data.intro);
    setText(emerEl, data.emergency);
    setText(insEl, data.insurance);
    setText(provEl, data.providers);
    setText(embEl, data.embassy);
    setText(advEl, data.advisories);
    setText(regEl, data.travelerReg);
    setText(noteEl, data.note);
  }

  // ---------- Init ----------
  document.addEventListener("DOMContentLoaded", () => {
    loadCountrySafetyJson()
      .catch((e) => console.error(e))
      .finally(() => {
        setupTabs();
        setupSearch();
        setupCrisisQnA();
        renderNoCountrySelected();
        renderUSCSupportDemo();
      });
  });
})();
