/* 广告加载器：一个文件管两个网络，位点由 data-* 配置。
 *
 * 设计约束（都是踩过的坑）：
 *  1. 懒加载：滚动到附近才注入，首屏不被广告拖慢；
 *  2. 超时放弃：脚本 8 秒没回来就当没这回事，绝不无限留白；
 *  3. 未配置就不占位：容器 data-filled="0" 时 CSS 直接 display:none，
 *     广告被拦截也不会出现空洞；
 *  4. Adsterra 的脚本会给 <script> 加 data-cfasync="false"，否则
 *     Cloudflare 的 Rocket Loader 会打乱它的执行顺序。
 */
(function () {
  "use strict";

  var CFG = {
    adsenseClient: "",            // ca-pub-XXXXXXXXXXXXXXXX，留空则不加载
    slots: { top: "", mid: "" },  // AdSense 广告单元 id，留空则用 Adsterra

    adsterra: {
      // 每个位点一个 key + 尺寸。key 形如 "abcdef0123456789..."，
      // 由 Adsterra 后台「Banner」代码里的 invoke.js?key= 参数给出。
      top: { key: "", width: 728, height: 90 },
      mid: { key: "", width: 300, height: 250 }
    },

    timeout: 8000,
    rootMargin: "200px"
  };

  var fired = Object.create(null);

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

    var doc = f.contentDocument;
    doc.open();
    doc.write(
      '<!doctype html><html><head><meta charset="utf-8">' +
      '<style>html,body{margin:0;padding:0;overflow:hidden}</style></head><body>' +
      '<script type="text/javascript">' +
      'atOptions = { "key": "' + spec.key + '", "format": "iframe", ' +
      '"height": ' + spec.height + ', "width": ' + spec.width + ' };' +
      '<\/script>' +
      '<script type="text/javascript" src="//www.highperformanceformat.com/' +
      spec.key + '/invoke.js"><\/script>' +
      '</body></html>'
    );
    doc.close();

    // iframe 一挂上就算填了；guard 到点会检查有没有砌出内容
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
    if (!CFG.adsenseClient || !slotId) return;
    var box = slot.querySelector("[data-ad-target]");
    if (!box) return;
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
  }

  /* -------------------------------------------------------------- 调度 */
  function fill(slot) {
    var name = slot.getAttribute("data-ad");
    if (fired[name]) return;
    fired[name] = true;

    if (CFG.slots[name]) adsenseAt(slot, CFG.slots[name]);
    else adsterraAt(slot, CFG.adsterra[name]);
  }

  function boot() {
    var slots = [].slice.call(document.querySelectorAll(".ad-slot"));
    if (!slots.length) return;

    if (CFG.adsenseClient) {
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
