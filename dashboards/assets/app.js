/* ==========================================================================
   RetailFlow Executive Business Intelligence Dashboard — client runtime.

   The Gold layer is embedded as dictionary-encoded, base64 typed arrays
   (window.__RETAILFLOW__). Every filter change re-aggregates the fact rows
   in a single pass and re-renders the KPI cards and all nine visuals, so the
   whole page cross-filters like a Power BI report without a server.
   ========================================================================== */

(function () {
  "use strict";

  var PAYLOAD = window.__RETAILFLOW__;
  var DIMS = PAYLOAD.dims;
  var META = PAYLOAD.meta;
  var N = PAYLOAD.n;

  // Chart geometry comes from shared/chart_theme.json, embedded at build time.
  // app/figures.py reads the same file, so the two front-ends cannot drift.
  var T = PAYLOAD.theme;

  /* ---------------------------------------------------------- decoding --
     Each column arrives as {t: "u8"|"u16"|"u32", d: base64}. The builder
     widens the type with the data, so the sentinel for "attribute unknown"
     is always the maximum value of whichever type was chosen. */

  var CTORS = { u8: Uint8Array, u16: Uint16Array, u32: Uint32Array };
  var SENTINELS = { u8: 255, u16: 65535, u32: 4294967295 };

  var COL = {};
  var NONE = {};

  function decode(b64, Ctor) {
    var bin = atob(b64);
    var bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return new Ctor(bytes.buffer, 0, bin.length / Ctor.BYTES_PER_ELEMENT);
  }

  Object.keys(PAYLOAD.cols).forEach(function (name) {
    var spec = PAYLOAD.cols[name];
    COL[name] = decode(spec.d, CTORS[spec.t]);
    NONE[name] = SENTINELS[spec.t];
  });

  /* ------------------------------------------------------------- state -- */

  var METRICS = {
    Revenue: { key: "rev", money: true, css: "--revenue", unit: "" },
    Profit: { key: "prof", money: true, css: "--profit", unit: "" },
    Quantity: { key: "qty", money: false, css: "--quantity", unit: " units" }
  };

  var state = {
    metric: "Revenue",
    filters: {
      year: "", month: "", category: "", brand: "",
      payment: "", gender: "", status: "", city: ""
    },
    cityQuery: "",
    cityNoMatch: false
  };

  /* ------------------------------------------------------- formatting  -- */

  function compact(v) {
    var abs = Math.abs(v);
    if (abs >= 1e9) return (v / 1e9).toFixed(2).replace(/\.?0+$/, "") + "B";
    if (abs >= 1e6) return (v / 1e6).toFixed(abs >= 1e8 ? 0 : 1) + "M";
    if (abs >= 1e3) return (v / 1e3).toFixed(abs >= 1e5 ? 0 : 1) + "K";
    return v.toFixed(abs < 10 && v % 1 !== 0 ? 2 : 0);
  }

  function money(v) { return "£" + compact(v); }

  function moneyFull(v) {
    return "£" + v.toLocaleString("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function count(v) { return v.toLocaleString("en-GB"); }

  function metricLabel(v) {
    return METRICS[state.metric].money ? money(v) : compact(v);
  }

  function metricFull(v) {
    return METRICS[state.metric].money ? moneyFull(v) : count(v) + " units";
  }

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function metricColor() { return cssVar(METRICS[state.metric].css); }

  /* ----------------------------------------------------------- buckets -- */

  function mkBucket(size) {
    return {
      rev: new Float64Array(size),
      prof: new Float64Array(size),
      qty: new Float64Array(size),
      cnt: new Float64Array(size)
    };
  }

  var MONTHS = DIMS.month;
  var TIME_SLOTS = DIMS.year.length * 12;

  function aggregate() {
    var f = state.filters;
    var fYear = f.year === "" ? -1 : +f.year;
    var fMonth = f.month === "" ? -1 : +f.month;
    var fCategory = f.category === "" ? -1 : +f.category;
    var fBrand = f.brand === "" ? -1 : +f.brand;
    var fPayment = f.payment === "" ? -1 : +f.payment;
    var fGender = f.gender === "" ? -1 : +f.gender;
    var fStatus = f.status === "" ? -1 : +f.status;
    var fCity = f.city === "" ? -1 : +f.city;

    var out = {
      rows: 0, rev: 0, prof: 0, qty: 0,
      brand: mkBucket(DIMS.brand.length),
      category: mkBucket(DIMS.category.length),
      city: mkBucket(DIMS.city.length),
      gender: mkBucket(DIMS.gender.length),
      payment: mkBucket(DIMS.payment.length),
      status: mkBucket(DIMS.status.length),
      customer: mkBucket(DIMS.customer.length),
      time: mkBucket(TIME_SLOTS),
      seenCustomer: new Uint8Array(DIMS.customer.length),
      seenProduct: new Uint8Array(META.productCount),
      seenCity: new Uint8Array(DIMS.city.length),
      customers: 0, products: 0, cities: 0
    };

    // Nothing can match an unresolvable city name.
    if (state.cityNoMatch) return out;

    var year = COL.year, month = COL.month, cat = COL.category, brand = COL.brand,
        pay = COL.payment, gen = COL.gender, st = COL.status, city = COL.city,
        cust = COL.customer, prod = COL.product, rev = COL.revenue, prof = COL.profit,
        qty = COL.quantity;

    for (var i = 0; i < N; i++) {
      var y = year[i];
      if (fYear >= 0 && y !== fYear) continue;
      var m = month[i];
      if (fMonth >= 0 && m !== fMonth) continue;
      var c = cat[i];
      if (fCategory >= 0 && c !== fCategory) continue;
      var b = brand[i];
      if (fBrand >= 0 && b !== fBrand) continue;
      var p = pay[i];
      if (fPayment >= 0 && p !== fPayment) continue;
      var g = gen[i];
      if (fGender >= 0 && g !== fGender) continue;
      var s = st[i];
      if (fStatus >= 0 && s !== fStatus) continue;
      var ct = city[i];
      if (fCity >= 0 && ct !== fCity) continue;

      var r = rev[i] / 100;
      var pf = prof[i] / 100;
      var q = qty[i];

      out.rows++;
      out.rev += r;
      out.prof += pf;
      out.qty += q;

      if (b !== NONE.brand) { out.brand.rev[b] += r; out.brand.prof[b] += pf; out.brand.qty[b] += q; out.brand.cnt[b]++; }
      if (c !== NONE.category) { out.category.rev[c] += r; out.category.prof[c] += pf; out.category.qty[c] += q; out.category.cnt[c]++; }
      if (g !== NONE.gender) { out.gender.rev[g] += r; out.gender.prof[g] += pf; out.gender.qty[g] += q; out.gender.cnt[g]++; }
      if (p !== NONE.payment) { out.payment.rev[p] += r; out.payment.prof[p] += pf; out.payment.qty[p] += q; out.payment.cnt[p]++; }
      if (s !== NONE.status) { out.status.rev[s] += r; out.status.prof[s] += pf; out.status.qty[s] += q; out.status.cnt[s]++; }

      if (ct !== NONE.city) {
        out.city.rev[ct] += r; out.city.prof[ct] += pf; out.city.qty[ct] += q; out.city.cnt[ct]++;
        if (!out.seenCity[ct]) { out.seenCity[ct] = 1; out.cities++; }
      }

      var cu = cust[i];
      if (cu !== NONE.customer) {
        out.customer.rev[cu] += r; out.customer.prof[cu] += pf; out.customer.qty[cu] += q; out.customer.cnt[cu]++;
        if (!out.seenCustomer[cu]) { out.seenCustomer[cu] = 1; out.customers++; }
      }

      var pr = prod[i];
      if (pr !== NONE.product && !out.seenProduct[pr]) { out.seenProduct[pr] = 1; out.products++; }

      if (y !== NONE.year && m > 0) {
        var slot = y * 12 + (m - 1);
        out.time.rev[slot] += r; out.time.prof[slot] += pf;
        out.time.qty[slot] += q; out.time.cnt[slot]++;
      }
    }

    return out;
  }

  /* ------------------------------------------------------- chart theme -- */

  function baseLayout(extra) {
    var layout = {
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: {
        family: T.font.family,
        size: T.font.size,
        color: cssVar("--text-secondary")
      },
      margin: { l: 8, r: 16, t: 10, b: 28 },
      showlegend: false,
      hoverlabel: {
        bgcolor: cssVar("--surface"),
        bordercolor: cssVar("--border-strong"),
        font: { color: cssVar("--text-primary"), size: 12 }
      },
      dragmode: false
    };
    Object.keys(extra || {}).forEach(function (k) { layout[k] = extra[k]; });
    return layout;
  }

  var CONFIG = {
    displaylogo: false,
    responsive: true,
    displayModeBar: "hover",
    modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d", "zoomIn2d", "zoomOut2d"],
    toImageButtonOptions: { format: "png", scale: 2, filename: "retailflow-chart" }
  };

  /* --------------------------------------------------------- chart specs */

  // Horizontal bar: labels on the left, values written on the mark, no x-axis.
  function hBarChart(rows, color, formatter, plotHeight) {
    var labels = rows.map(function (r) { return r.label; });
    var values = rows.map(function (r) { return r.value; });
    var text = rows.map(function (r) { return formatter(r.value); });
    var colors = rows.map(function (r) { return r.color || color; });
    var max = Math.max.apply(null, values.concat([0])) || 1;

    // Bar width is in category units, so cap it when the chart has few rows.
    var height = plotHeight || 300;
    var width = rows.length ? Math.min(0.65, (T.bar.maxThicknessPx * rows.length) / height) : 0.65;

    return {
      data: [{
        type: "bar",
        orientation: "h",
        x: values,
        y: labels,
        width: width,
        marker: { color: colors, cornerradius: T.bar.cornerRadius, line: { width: 0 } },
        text: text,
        textposition: "outside",
        cliponaxis: false,
        textfont: { color: cssVar("--text-secondary"), size: T.font.labelSize },
        customdata: rows.map(function (r) { return r.hover; }),
        hovertemplate: "<b>%{y}</b><br>%{customdata}<extra></extra>"
      }],
      layout: baseLayout({
        bargap: T.bar.gap,
        margin: T.bar.margin,
        xaxis: { visible: false, range: [0, max * T.bar.headroom], fixedrange: true },
        yaxis: {
          automargin: true,
          ticklabelposition: "outside",
          tickfont: { color: cssVar("--text-secondary"), size: T.font.size },
          showgrid: false,
          zeroline: false,
          showline: false,
          ticks: "",
          fixedrange: true
        }
      })
    };
  }

  function vBarChart(x, y, color, hover) {
    return {
      data: [{
        type: "bar",
        x: x,
        y: y,
        marker: { color: color, cornerradius: T.column.cornerRadius, line: { width: 0 } },
        customdata: hover,
        hovertemplate: "<b>%{x|%b %Y}</b><br>%{customdata}<extra></extra>"
      }],
      layout: baseLayout({
        bargap: T.column.gap,
        margin: T.column.margin,
        hovermode: "x unified",
        xaxis: {
          type: "date", tickformat: T.axis.dateTickFormat, showgrid: false, zeroline: false,
          linecolor: cssVar("--axis"), tickfont: { color: cssVar("--text-muted"), size: T.font.tickSize },
          fixedrange: true, nticks: T.axis.maxTicks
        },
        yaxis: {
          showgrid: true, gridcolor: cssVar("--grid"), gridwidth: 1, zeroline: false,
          tickfont: { color: cssVar("--text-muted"), size: T.font.tickSize },
          tickformat: T.axis.valueTickFormat, fixedrange: true, rangemode: "tozero"
        }
      })
    };
  }

  function lineChart(x, y, color, prefix) {
    return {
      data: [{
        type: "scatter",
        mode: "lines+markers",
        x: x,
        y: y,
        line: { color: color, width: T.line.width }, // linear: a spline invents months
        marker: {
          size: T.line.markerSize, color: color,
          line: { width: T.line.markerRing, color: cssVar("--surface") }
        },
        fill: "tozeroy",
        fillcolor: hexToRgba(color, T.line.fillOpacity),
        hovertemplate: "%{y:,.0f}<extra></extra>"
      }],
      layout: baseLayout({
        margin: T.line.margin,
        hovermode: "x unified",
        xaxis: {
          type: "date", tickformat: T.axis.dateTickFormat, showgrid: false, zeroline: false,
          linecolor: cssVar("--axis"), tickfont: { color: cssVar("--text-muted"), size: T.font.tickSize },
          fixedrange: true, nticks: T.axis.maxTicks, showspikes: true, spikemode: "across",
          spikethickness: 1, spikedash: "dot", spikecolor: cssVar("--axis")
        },
        yaxis: {
          showgrid: true, gridcolor: cssVar("--grid"), gridwidth: 1, zeroline: false,
          tickprefix: prefix, tickformat: T.axis.valueTickFormat, rangemode: "tozero",
          tickfont: { color: cssVar("--text-muted"), size: T.font.tickSize }, fixedrange: true
        }
      })
    };
  }

  function hexToRgba(hex, alpha) {
    var h = hex.replace("#", "").trim();
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    var n = parseInt(h, 16);
    return "rgba(" + ((n >> 16) & 255) + "," + ((n >> 8) & 255) + "," + (n & 255) + "," + alpha + ")";
  }

  /* --------------------------------------------------------- rendering -- */

  function topRows(bucket, names, key, limit) {
    var rows = [];
    for (var i = 0; i < names.length; i++) {
      if (bucket.cnt[i] === 0) continue;
      rows.push({ label: names[i], value: bucket[key][i], orders: bucket.cnt[i] });
    }
    rows.sort(function (a, b) { return b.value - a.value; });
    if (limit) rows = rows.slice(0, limit);
    return rows;
  }

  function withHover(rows, total) {
    return rows.map(function (r) {
      var share = total > 0 ? ((r.value / total) * 100).toFixed(1) + "% of total" : "";
      r.hover = metricFull(r.value) + "<br>" + count(r.orders) + " orders · " + share;
      return r;
    });
  }

  // Plotly draws horizontal bars bottom-up, so reverse for "largest at the top".
  function forPlot(rows) { return rows.slice().reverse(); }

  function draw(id, build) {
    var el = document.getElementById(id);
    if (el.classList.contains("empty")) {
      // Coming back from the empty state: drop its message, or Plotly.react
      // renders the chart underneath a stale text node.
      el.classList.remove("empty");
      el.textContent = "";
    }
    var spec = typeof build === "function" ? build(el.clientHeight || 300) : build;
    Plotly.react(el, spec.data, spec.layout, CONFIG);
  }

  function hBar(rows, color, formatter) {
    return function (height) { return hBarChart(rows, color, formatter, height); };
  }

  function drawEmpty(id) {
    var el = document.getElementById(id);
    Plotly.purge(el);
    el.classList.add("empty");
    el.textContent = "No records match the current filters.";
  }

  var STATUS_COLOUR = {
    Delivered: "--status-good",
    Shipped: "--status-neutral",
    Pending: "--status-warning",
    Returned: "--status-serious",
    Cancelled: "--status-critical"
  };

  function timeSeries(agg, key) {
    var x = [], y = [];
    for (var slot = 0; slot < TIME_SLOTS; slot++) {
      if (agg.time.cnt[slot] === 0) continue;
      var year = DIMS.year[Math.floor(slot / 12)];
      var month = (slot % 12) + 1;
      x.push(year + "-" + (month < 10 ? "0" : "") + month + "-01");
      y.push(agg.time[key][slot]);
    }
    return { x: x, y: y };
  }

  var lastAgg = null;

  function render() {
    var agg = aggregate();
    lastAgg = agg;
    var m = METRICS[state.metric];
    var colour = metricColor();
    var ordersColour = cssVar("--orders");
    var totals = { rev: agg.rev, prof: agg.prof, qty: agg.qty };
    var metricTotal = totals[m.key];

    renderKpis(agg);
    renderSummary(agg);

    if (agg.rows === 0) {
      renderTitles({});
      ["plot-trend", "plot-brands", "plot-category", "plot-city", "plot-gender",
       "plot-payment", "plot-status", "plot-customers", "plot-orders"].forEach(drawEmpty);
      return;
    }

    // Row 1 — the three visuals executives open first.
    var ts = timeSeries(agg, m.key);
    draw("plot-trend", lineChart(ts.x, ts.y, colour, m.money ? "£" : ""));

    var brandRows = withHover(topRows(agg.brand, DIMS.brand, m.key, 10), metricTotal);
    draw("plot-brands", hBar(forPlot(brandRows), colour, metricLabel));

    draw("plot-category", hBar(
      forPlot(withHover(topRows(agg.category, DIMS.category, m.key), metricTotal)),
      colour, metricLabel));

    // Row 2
    var cityRows = withHover(topRows(agg.city, DIMS.city, m.key, 10), metricTotal);
    draw("plot-city", hBar(forPlot(cityRows), colour, metricLabel));

    draw("plot-gender", hBar(
      forPlot(withHover(topRows(agg.gender, DIMS.gender, m.key), metricTotal)),
      colour, metricLabel));

    draw("plot-payment", hBar(
      forPlot(withHover(topRows(agg.payment, DIMS.payment, m.key), metricTotal)),
      colour, metricLabel));

    // Row 3 — order-count visuals keep their own colour so they never read as £.
    var statusRows = topRows(agg.status, DIMS.status, "cnt").map(function (r) {
      r.color = cssVar(STATUS_COLOUR[r.label] || "--status-neutral");
      r.hover = count(r.value) + " orders · " +
        ((r.value / agg.rows) * 100).toFixed(1) + "% of selection";
      return r;
    });
    draw("plot-status", hBar(forPlot(statusRows), ordersColour, count));

    var custRows = withHover(topRows(agg.customer, DIMS.customer, m.key, 10), metricTotal);
    draw("plot-customers", hBar(forPlot(custRows), colour, metricLabel));

    var orders = timeSeries(agg, "cnt");
    draw("plot-orders", vBarChart(orders.x, orders.y, ordersColour,
      orders.y.map(function (v) { return count(v) + " orders"; })));

    renderTitles({ brands: brandRows.length, city: cityRows.length, customers: custRows.length });
  }

  /* -------------------------------------------------------------- KPIs -- */

  var KPI_DEFS = [
    { id: "kpi-revenue", accent: "--revenue" },
    { id: "kpi-profit", accent: "--profit" },
    { id: "kpi-orders", accent: "--orders" },
    { id: "kpi-customers", accent: "--profit" },
    { id: "kpi-products", accent: "--quantity" },
    { id: "kpi-aov", accent: "--revenue" },
    { id: "kpi-margin", accent: "--profit" },
    { id: "kpi-cities", accent: "--orders" }
  ];

  function setKpi(id, value, sub) {
    document.querySelector("#" + id + " .kpi-value").textContent = value;
    document.querySelector("#" + id + " .kpi-sub").innerHTML = '<span class="dot"></span>' + sub;
  }

  function renderKpis(agg) {
    var orders = agg.rows;
    var aov = orders ? agg.rev / orders : 0;
    var margin = agg.rev ? (agg.prof / agg.rev) * 100 : 0;

    setKpi("kpi-revenue", money(agg.rev), moneyFull(agg.rev));
    setKpi("kpi-profit", money(agg.prof), margin.toFixed(1) + "% margin");
    setKpi("kpi-orders", compact(orders), count(orders) + " order lines");
    setKpi("kpi-customers", compact(agg.customers), count(agg.customers) + " active buyers");
    setKpi("kpi-products", compact(agg.products), count(agg.products) + " SKUs sold");
    setKpi("kpi-aov", orders ? moneyFull(aov) : "£0.00", "per order");
    setKpi("kpi-margin", margin.toFixed(1) + "%", money(agg.prof) + " on " + money(agg.rev));
    setKpi("kpi-cities", compact(agg.cities), count(agg.cities) + " UK locations");
  }

  /* ---------------------------------------------------------- chrome  --- */

  var TITLES = {
    "title-trend": function (m) { return m + " Trend"; },
    "title-brands": function () { return "Top Products by Brand"; },
    "title-category": function (m) { return m + " by Category"; },
    "title-city": function (m) { return m + " by City"; },
    "title-gender": function (m) { return m + " by Gender"; },
    "title-payment": function () { return "Payment Methods"; },
    "title-status": function () { return "Order Status"; },
    "title-customers": function () { return "Top Customers"; },
    "title-orders": function () { return "Monthly Orders"; }
  };

  // "Top 10" is a cap, not a promise — say how many rows actually survived.
  var SUBTITLES = {
    "sub-brands": function (m, n) { return ranked("brands", n.brands, m); },
    "sub-city": function (m, n) { return ranked("cities", n.city, m); },
    "sub-payment": function (m) { return m + " by payment method"; },
    "sub-customers": function (m, n) { return ranked("customers", n.customers, m); }
  };

  function ranked(noun, shown, metric) {
    var head = shown ? "Top " + shown + " " + noun : noun.charAt(0).toUpperCase() + noun.slice(1);
    return head + " by " + metric.toLowerCase();
  }

  function renderTitles(counts) {
    var m = state.metric;
    var n = counts || {};
    Object.keys(TITLES).forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.textContent = TITLES[id](m);
    });
    Object.keys(SUBTITLES).forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.textContent = SUBTITLES[id](m, n);
    });
  }

  var FILTER_LABELS = {
    year: "Year", month: "Month", category: "Category", brand: "Brand",
    payment: "Payment", gender: "Gender", status: "Status", city: "City"
  };

  function renderSummary(agg) {
    var parts = [];
    Object.keys(state.filters).forEach(function (k) {
      var v = state.filters[k];
      if (v === "") return;
      var name = k === "month" ? MONTHS[+v - 1] : DIMS[k][+v];
      parts.push("<b>" + FILTER_LABELS[k] + ":</b> " + name);
    });
    if (state.cityNoMatch) parts.push('<b>City:</b> "' + state.cityQuery + '" — no match');

    var pct = N ? ((agg.rows / N) * 100).toFixed(1) : "0.0";
    var scope = parts.length ? parts.join(" &nbsp;·&nbsp; ") : "No filters applied — full dataset";
    document.getElementById("filter-summary").innerHTML =
      scope + " &nbsp;→&nbsp; <b>" + count(agg.rows) + "</b> of " + count(N) +
      " order lines (" + pct + "%)";
  }

  /* -------------------------------------------------------- interaction */

  function option(value, label) {
    var o = document.createElement("option");
    o.value = value;
    o.textContent = label;
    return o;
  }

  function fillSelect(id, values, allLabel) {
    var sel = document.getElementById(id);
    sel.appendChild(option("", allLabel));
    values.forEach(function (v, i) { sel.appendChild(option(String(i), v)); });
    return sel;
  }

  function bindFilters() {
    fillSelect("f-year", DIMS.year, "All years");
    var monthSel = document.getElementById("f-month");
    monthSel.appendChild(option("", "All months"));
    MONTHS.forEach(function (name, i) { monthSel.appendChild(option(String(i + 1), name)); });
    fillSelect("f-category", DIMS.category, "All categories");
    fillSelect("f-brand", DIMS.brand, "All brands");
    fillSelect("f-payment", DIMS.payment, "All methods");
    fillSelect("f-gender", DIMS.gender, "All genders");
    fillSelect("f-status", DIMS.status, "All statuses");

    ["year", "month", "category", "brand", "payment", "gender", "status"].forEach(function (key) {
      var sel = document.getElementById("f-" + key);
      sel.addEventListener("change", function () {
        state.filters[key] = sel.value;
        sel.classList.toggle("is-active", sel.value !== "");
        render();
      });
    });

    // City has ~4k values — a datalist keeps it type-ahead rather than a 4k-row menu.
    var list = document.getElementById("city-options");
    var cityIndex = {};
    DIMS.city.forEach(function (name, i) {
      cityIndex[name.toLowerCase()] = i;
      list.appendChild(option(name, ""));
    });

    var cityInput = document.getElementById("f-city");
    cityInput.addEventListener("input", function () {
      var raw = cityInput.value.trim();
      state.cityQuery = raw;
      if (raw === "") {
        state.filters.city = "";
        state.cityNoMatch = false;
      } else if (Object.prototype.hasOwnProperty.call(cityIndex, raw.toLowerCase())) {
        state.filters.city = String(cityIndex[raw.toLowerCase()]);
        state.cityNoMatch = false;
      } else {
        state.filters.city = "";
        state.cityNoMatch = true;
      }
      cityInput.classList.toggle("is-active", raw !== "");
      render();
    });
  }

  function bindMetric() {
    var buttons = Array.prototype.slice.call(document.querySelectorAll("[data-metric]"));
    var bar = document.getElementById("metric-switch");

    function apply(metric) {
      state.metric = metric;
      bar.style.setProperty("--seg-accent", cssVar(METRICS[metric].css));
      buttons.forEach(function (b) {
        b.setAttribute("aria-pressed", String(b.dataset.metric === metric));
      });
      render();
    }

    buttons.forEach(function (b) {
      b.addEventListener("click", function () { apply(b.dataset.metric); });
    });
    apply(state.metric);
  }

  function bindReset() {
    document.getElementById("btn-reset").addEventListener("click", function () {
      Object.keys(state.filters).forEach(function (k) { state.filters[k] = ""; });
      state.cityQuery = "";
      state.cityNoMatch = false;
      document.querySelectorAll(".filters select").forEach(function (s) {
        s.value = "";
        s.classList.remove("is-active");
      });
      var city = document.getElementById("f-city");
      city.value = "";
      city.classList.remove("is-active");
      render();
    });
  }

  function bindTheme() {
    var btn = document.getElementById("btn-theme");
    var stored = null;
    try { stored = localStorage.getItem("retailflow-theme"); } catch (e) { /* private mode */ }
    if (stored) document.documentElement.setAttribute("data-theme", stored);
    sync();

    function current() {
      var attr = document.documentElement.getAttribute("data-theme");
      if (attr) return attr;
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }

    function sync() {
      btn.textContent = current() === "dark" ? "☀ Light" : "☾ Dark";
    }

    btn.addEventListener("click", function () {
      var next = current() === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      try { localStorage.setItem("retailflow-theme", next); } catch (e) { /* ignore */ }
      sync();
      var bar = document.getElementById("metric-switch");
      bar.style.setProperty("--seg-accent", cssVar(METRICS[state.metric].css));
      render();
    });
  }

  /* --------------------------------------------------------- CSV export */

  function csvEscape(v) {
    var s = String(v);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  function exportCsv() {
    if (!lastAgg) return;
    var agg = lastAgg;
    var lines = ["visual,label,revenue_gbp,profit_gbp,quantity,orders"];

    function push(visual, names, bucket, limit) {
      var rows = [];
      for (var i = 0; i < names.length; i++) {
        if (bucket.cnt[i] === 0) continue;
        rows.push({ i: i, v: bucket.rev[i] });
      }
      rows.sort(function (a, b) { return b.v - a.v; });
      if (limit) rows = rows.slice(0, limit);
      rows.forEach(function (r) {
        lines.push([visual, csvEscape(names[r.i]), bucket.rev[r.i].toFixed(2),
          bucket.prof[r.i].toFixed(2), bucket.qty[r.i], bucket.cnt[r.i]].join(","));
      });
    }

    push("brand", DIMS.brand, agg.brand, 10);
    push("category", DIMS.category, agg.category);
    push("city", DIMS.city, agg.city, 10);
    push("gender", DIMS.gender, agg.gender);
    push("payment", DIMS.payment, agg.payment);
    push("status", DIMS.status, agg.status);
    push("customer", DIMS.customer, agg.customer, 10);

    for (var slot = 0; slot < TIME_SLOTS; slot++) {
      if (agg.time.cnt[slot] === 0) continue;
      var label = MONTHS[slot % 12] + " " + DIMS.year[Math.floor(slot / 12)];
      lines.push(["month", csvEscape(label), agg.time.rev[slot].toFixed(2),
        agg.time.prof[slot].toFixed(2), agg.time.qty[slot], agg.time.cnt[slot]].join(","));
    }

    var blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "retailflow-selection.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  /* -------------------------------------------------------------- boot -- */

  function boot() {
    document.getElementById("meta-generated").textContent = META.generated;
    document.getElementById("meta-rows").textContent = count(META.rowCount);
    bindFilters();
    bindReset();
    bindTheme();
    document.getElementById("btn-export").addEventListener("click", exportCsv);
    bindMetric(); // triggers the first render
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
