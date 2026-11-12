/* 广告加载器：一个文件管两个网络，位点与尺寸由 CFG 决定。
 *
 * 设计约束（都是踩过的坑）：
 *  1. 懒加载：滚动到附近才注入，首屏不被广告拖慢；
 *  2. 超时放弃：脚本 8 秒没回来就当没这回事，绝不无限留白；
 *  3. 未配置就不占位：容器 data-filled="0" 时 CSS 直接 display:none，
 *     广告被拦截也不会出现空洞；
 *  4. Adsterra 的脚本会给 <script> 加 data-cfasync="false"，否则
 *     Cloudflare 的 Rocket Loader 会打乱它的执行顺序；
 *  5. Adsterra 只出固定尺寸，所以两个位点各按断点准备了一套素材，
 *     窄屏用 320×50，宽屏用 728×90。
 */
(function () {
  "use strict";

  var CFG = {
    adsenseClient: "ca-pub-7074159807555116",
    slots: { top: "", mid: "" },  // AdSense 广告单元 id，留空则用 Adsterra

    adsterra: {
      /* Adsterra 后台给的是 <script src="https://<host>/<path>/<key>"> 形式，
       * host 与 path 会变更，所以拆成两段存，换域名时只改这里。 */
      host: "bellnewyork.org",
      path: "22",

      // 每个位点一套或多套素材。有 desk / mob 两个键时按视口宽度二选一。
      top: {
        desk: { key: "adb21c95e5758a141e436d713e09cc29", width: 728, height: 90 },
        mob:  { key: "51215ba03350c2ec6e01d69c7eccb9ec", width: 320, height: 50 }
      },
      mid: {
        desk: { key: "b2560d6bc632c93c3f4f702d076d09f7", width: 300, height: 250 }
      }
    },

    timeout: 8000,
    rootMargin: "200px"
  };

  var fired = Object.create(null);

  /* 站点是否深色。广告素材的配色改不了，但可以把承载它的画布染成同一色调，
   * 避免深色页面上出现一块刺眼的白底。 */
  function isDark() {
    try {
      return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    } catch (e) { return false; }
  }

  /* 从页面实际计算出的背景色，保证 iframe 底色和站点一致（而不是硬编码） */
  function pageBg() {
    try {
      var v = getComputedStyle(document.documentElement).getPropertyValue("--bg-soft").trim();
      if (v) return v;
      var b = getComputedStyle(document.body).backgroundColor;
      if (b && b !== "rgba(0, 0, 0, 0)" && b !== "transparent") return b;
    } catch (e) { /* 老浏览器兜底 */ }
    return isDark() ? "#0e1013" : "#f6f6f4";
  }

  function el(tag, attrs, text) {
    var n = document.createElement(tag);
    if (attrs) for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (text) n.appendChild(document.createTextNode(text));
    return n;
  }

  function markFilled(slot) {
    if (slot) slot.setAttribute("data-filled", "1");
  }

  /* 超时后把容器还原成隐藏，避免广告脚本没回来但容器撑出大块空白 */
  function guard(slot) {
    var t = setTimeout(function () {
      var child = slot.querySelector("[data-ad-loaded]");
      if (!child) { slot.setAttribute("data-filled", "0"); }
    }, CFG.timeout);
    return function () { clearTimeout(t); };
  }

  function loadScript(src, onload, onerror) {
    var s = document.createElement("script");
    s.src = src;
    s.async = true;
    s.setAttribute("data-cfasync", "false");
    if (onload) s.onload = onload;
    if (onerror) s.onerror = onerror;
    document.head.appendChild(s);
    return s;
  }

  /* 从位点配置里挑一套素材：宽屏优先 desk，没有就退回唯一那套 */
  function pickSpec(cfg, wide) {
    if (!cfg) return null;
    if (cfg.desk || cfg.mob) {
      if (wide && cfg.desk) return cfg.desk;
      if (!wide && cfg.mob) return cfg.mob;
      return cfg.desk || cfg.mob;
    }
    return cfg.key ? cfg : null;
  }

  /* ---------------------------------------------------------- Adsterra */
  function adsterraAt(slot, spec) {
    if (!spec || !spec.key) return;
    var box = slot.querySelector("[data-ad-target]");
    if (!box) return;
    var ok = guard(slot);

    // 用 iframe 包裹，避免广告方样式污染本站（同时防止它改我们的 title）
    var f = el("iframe", {
      title: "广告",
      width: String(spec.width),
      height: String(spec.height),
      style: "border:0;overflow:hidden;max-width:100%",
      scrolling: "no",
      sandbox: "allow-scripts allow-popups allow-same-origin allow-forms"
    });
    box.appendChild(f);
    box.setAttribute("data-ad-loaded", "1");
    markFilled(slot);

    var src = "https://" + CFG.adsterra.host + "/" + CFG.adsterra.path + "/" + spec.key;
    var dark = isDark();
    var bg = pageBg();
    var doc = f.contentDocument;
    doc.open();
    doc.write(
      '<!doctype html><html><head><meta charset="utf-8">' +
      '<meta name="color-scheme" content="' + (dark ? "dark light" : "light dark") + '">' +
      '<style>html,body{margin:0;padding:0;overflow:hidden;background:' + bg + ';' +
      'color-scheme:' + (dark ? "dark light" : "light dark") + '}</style></head><body>' +
      '<script type="text/javascript">' +
      'atOptions = { "key": "' + spec.key + '", "format": "iframe", ' +
      '"height": ' + spec.height + ', "width": ' + spec.width + ', "params": {} };' +
      '<\/script>' +
      '<script type="text/javascript" src="' + src + '"><\/script>' +
      '</body></html>'
    );
    doc.close();

    f.addEventListener("load", function () { ok(); markFilled(slot); });
  }

  /* ----------------------------------------------------------- AdSense */
  var adsenseReady = false;
  var adsenseQueue = [];

  function flushAdsense() {
    adsenseReady = true;
    while (adsenseQueue.length) {
      try { (window.adsbygoogle = window.adsbygoogle || []).push({}); }
      catch (e) { /* 兜底：广告被拦截时 push 会抛，忽略即可 */ }
      adsenseQueue.pop();
    }
  }

  function adsenseAt(slot, slotId) {
    if (!CFG.adsenseClient || !slotId) return false;
    var box = slot.querySelector("[data-ad-target]");
    if (!box) return false;
    guard(slot);

    var ins = el("ins", {
      "class": "adsbygoogle",
      style: "display:block",
      "data-ad-client": CFG.adsenseClient,
      "data-ad-slot": slotId,
      "data-full-width-responsive": "true"
    });
    box.appendChild(ins);
    box.setAttribute("data-ad-loaded", "1");
    markFilled(slot);

    if (adsenseReady) flushAdsense();
    else adsenseQueue.push(ins);
    return true;
  }

  /* -------------------------------------------------------------- 调度 */
  function fill(slot) {
    var name = slot.getAttribute("data-ad");
    if (fired[name]) return;
    fired[name] = true;

    if (adsenseAt(slot, CFG.slots[name])) return;

    var wide = window.innerWidth >= 760;
    adsterraAt(slot, pickSpec(CFG.adsterra[name], wide));
  }

  function boot() {
    var slots = [].slice.call(document.querySelectorAll(".ad-slot"));
    if (!slots.length) return;

    // 只有真的配了广告单元 id 才去拉 AdSense 的脚本；
    // 光有 client 号时不必加载，省一个第三方请求（站点验证走 meta 标签）。
    var hasAdsenseSlot = !!(CFG.slots.top || CFG.slots.mid);
    if (CFG.adsenseClient && hasAdsenseSlot) {
      var s = loadScript(
        "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" +
          encodeURIComponent(CFG.adsenseClient),
        flushAdsense, function () { /* 加载失败就不填 */ }
      );
      s.crossOrigin = "anonymous";
    }

    if (!("IntersectionObserver" in window)) { slots.forEach(fill); return; }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { io.unobserve(e.target); fill(e.target); }
      });
    }, { rootMargin: CFG.rootMargin });

    slots.forEach(function (s) { io.observe(s); });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
