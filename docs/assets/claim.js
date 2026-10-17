/* Claim-this-page form. Posts one JSON lead to Station's existing intake (the n8n Range relay, which Circle's
   command center pulls on its own schedule). The relay stores: name, business, phone, email, industry, website,
   leak (free text), variant, address, path, ref. We also send source=norman-eats; the relay does not keep that field
   today, so ref and variant carry the tag. No cookies, no analytics, nothing else leaves this page. */
(function () {
  "use strict";
  var ENDPOINT = "https://n8n.srv1748596.hstgr.cloud/webhook/range-lead";
  var forms = document.querySelectorAll("form[data-claim]");
  if (!forms.length) return;
  function sid() {
    try {
      var s = sessionStorage.getItem("neSid");
      if (!s) { s = Math.random().toString(36).slice(2, 10) + Date.now().toString(36); sessionStorage.setItem("neSid", s); }
      return s;
    } catch (e) { return "anon"; }
  }
  function send(obj) {
    var data = JSON.stringify(obj);
    try {
      if (navigator.sendBeacon && navigator.sendBeacon(ENDPOINT, new Blob([data], { type: "text/plain" }))) return;
    } catch (e) {}
    try {
      fetch(ENDPOINT, { method: "POST", body: data, keepalive: true, mode: "no-cors",
                        headers: { "Content-Type": "text/plain" } }).catch(function () {});
    } catch (e) {}
  }
  Array.prototype.forEach.call(forms, function (form) {
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var hp = form.querySelector('input[name="company_url"]');
      if (hp && hp.value) { return; }                   /* a bot filled the hidden field: drop silently */
      var fd = new FormData(form);
      var lead = { ev: "lead", path: location.pathname, sid: sid(), ref: "norman-eats", source: "norman-eats",
                   variant: "norman-eats-claim", consent_url: String(location.href).slice(0, 1000) };
      fd.forEach(function (v, k) {
        if (k === "company_url" || typeof v !== "string") return;
        lead[k] = String(v).slice(0, k === "leak" ? 4000 : 300);
      });
      var role = lead.role || "";
      lead.industry = (lead.industry || "") + (role ? " (" + role + ")" : "");
      lead.leak = "Norman Eats page claim for " + (lead.business || "a place") + (lead.leak ? ". " + lead.leak : "");
      delete lead.role;
      if (!lead.name || !lead.email) { return; }
      send(lead);
      var done = form.parentNode.querySelector(".done");
      form.setAttribute("hidden", "");
      if (done) {
        var mail = done.querySelector("a[data-mail]");
        if (mail) {
          mail.href = "mailto:main@station.solutions?subject=" + encodeURIComponent("Norman Eats claim: " + (lead.business || "")) +
            "&body=" + encodeURIComponent("Name: " + lead.name + "\nEmail: " + lead.email + "\nPhone: " + (lead.phone || "") +
            "\nPlace: " + (lead.business || "") + ", " + (lead.address || "") + "\nRole: " + role + "\nNotes: " + (fd.get("leak") || ""));
        }
        done.setAttribute("data-show", "");
        done.focus && done.focus();
      }
    });
  });
})();
