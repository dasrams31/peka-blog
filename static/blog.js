// Peka AI blog client behaviors: theme, progress, terminal copy,
// table-of-contents scrollspy, image lightbox, back-to-top, syntax highlight.
(function () {
  "use strict";

  // Theme toggle (persisted; the initial attribute is set inline in <head>).
  var root = document.documentElement;
  var tbtn = document.getElementById("themebtn");
  function syncThemeBtn() {
    if (tbtn) tbtn.textContent = root.getAttribute("data-theme") === "dark" ? "terang" : "gelap";
  }
  if (tbtn) {
    tbtn.addEventListener("click", function () {
      var dark = root.getAttribute("data-theme") !== "dark";
      if (dark) root.setAttribute("data-theme", "dark");
      else root.removeAttribute("data-theme");
      try { localStorage.setItem("peka-theme", dark ? "dark" : "light"); } catch (e) {}
      syncThemeBtn();
    });
    syncThemeBtn();
  }

  // Reading progress bar + back-to-top visibility, one scroll listener.
  var bar = document.getElementById("progress");
  var toTop = document.getElementById("toTop");
  var ticking = false;
  function onScroll() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    var y = window.scrollY || h.scrollTop;
    if (bar) bar.style.width = (max > 0 ? (y / max) * 100 : 0) + "%";
    if (toTop) toTop.classList.toggle("show", y > 600);
    ticking = false;
  }
  window.addEventListener("scroll", function () {
    if (!ticking) { ticking = true; requestAnimationFrame(onScroll); }
  }, { passive: true });
  onScroll();
  if (toTop) {
    toTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // Terminal copy buttons: copy the code block text, flash feedback.
  document.querySelectorAll(".tcopy").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var term = btn.closest(".term");
      var code = term ? term.querySelector("pre code") : null;
      if (!code) return;
      var text = code.innerText.replace(/\n$/, "");
      function done() {
        btn.textContent = "disalin!";
        setTimeout(function () { btn.textContent = "salin"; }, 1600);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { fallback(); });
      } else {
        fallback();
      }
      function fallback() {
        var ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); } catch (e) {}
        document.body.removeChild(ta);
        done();
      }
    });
  });

  // Table-of-contents scrollspy.
  var tocLinks = document.querySelectorAll("[data-toc]");
  if (tocLinks.length && "IntersectionObserver" in window) {
    var byId = {};
    tocLinks.forEach(function (a) { byId[a.getAttribute("data-toc")] = a; });
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          tocLinks.forEach(function (a) { a.classList.remove("on"); });
          var link = byId[en.target.id];
          if (link) link.classList.add("on");
        }
      });
    }, { rootMargin: "-80px 0px -70% 0px" });
    tocLinks.forEach(function (a) {
      var el = document.getElementById(a.getAttribute("data-toc"));
      if (el) spy.observe(el);
    });
  }

  // Image lightbox for article images (slider images excluded on purpose).
  var lb = document.getElementById("lightbox");
  if (lb) {
    var lbImg = lb.querySelector("img");
    document.querySelectorAll(".body img, img.cover").forEach(function (img) {
      img.addEventListener("click", function () {
        lbImg.src = img.currentSrc || img.src;
        lb.classList.add("open");
      });
    });
    lb.addEventListener("click", function () { lb.classList.remove("open"); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") lb.classList.remove("open");
    });
  }

  // Syntax highlighting when highlight.js arrived from the CDN.
  if (window.hljs) window.hljs.highlightAll();
})();
