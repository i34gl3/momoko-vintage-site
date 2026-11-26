/* Momoko Vintage online shop: language switch, filters, photo counter, email link. */
(function () {
  var html = document.documentElement;

  /* ---------- hu / en ---------- */
  var btn = document.getElementById('langBtn');
  var nodes = document.querySelectorAll('[data-en]');
  var labels = document.querySelectorAll('[data-en-label]');
  nodes.forEach(function (n) { n.setAttribute('data-hu', n.innerHTML); });
  labels.forEach(function (n) { n.setAttribute('data-hu-label', n.getAttribute('aria-label') || ''); });
  function apply(l) {
    nodes.forEach(function (n) { n.innerHTML = n.getAttribute(l === 'en' ? 'data-en' : 'data-hu'); });
    labels.forEach(function (n) { n.setAttribute('aria-label', n.getAttribute(l === 'en' ? 'data-en-label' : 'data-hu-label')); });
    html.lang = l;
    if (btn) {
      btn.textContent = l === 'en' ? 'hu' : 'en';
      btn.setAttribute('aria-label', l === 'en' ? 'Váltás magyarra' : 'Switch to English');
    }
    var t = document.querySelector('meta[name="title-' + l + '"]');
    if (t) document.title = t.content;
    try { localStorage.setItem('mv-lang', l); } catch (e) {}
    document.dispatchEvent(new CustomEvent('mv-lang'));
  }
  var saved = null;
  try { saved = localStorage.getItem('mv-lang'); } catch (e) {}
  var bot = /bot|crawl|spider|slurp|google|bing|yandex|duckduck|facebookexternalhit/i.test(navigator.userAgent || '');
  var lang = saved || (!bot && (navigator.language || '').toLowerCase().indexOf('hu') !== 0 ? 'en' : 'hu');
  if (lang === 'en') apply('en');
  if (btn) btn.addEventListener('click', function () { lang = html.lang === 'en' ? 'hu' : 'en'; apply(lang); });

  var y = document.getElementById('year');
  if (y) y.textContent = new Date().getFullYear();
  document.querySelectorAll('.js-mail').forEach(function (a) {
    var m = a.getAttribute('data-u') + '@' + a.getAttribute('data-d');
    a.href = 'mailto:' + m; if (!a.hasAttribute('data-keep')) a.textContent = m;
  });

  /* ---------- grid filters ---------- */
  var grid = document.getElementById('grid');
  if (grid) {
    var state = { g: 'all', c: 'all' };
    var cards = Array.prototype.slice.call(grid.children);
    var count = document.getElementById('count'), empty = document.getElementById('empty');
    function render() {
      var n = 0;
      cards.forEach(function (c) {
        var ok = (state.g === 'all' || c.dataset.g === state.g || c.dataset.g === 'unisex') &&
                 (state.c === 'all' || c.dataset.c === state.c);
        c.hidden = !ok;
        if (ok && !c.classList.contains('sold')) n++;
      });
      var en = html.lang === 'en';
      count.textContent = en ? n + (n === 1 ? ' piece available' : ' pieces available') : n + ' elérhető darab';
      empty.hidden = n > 0 || cards.some(function (c) { return !c.hidden; });
    }
    document.querySelectorAll('.f-btn').forEach(function (b) {
      b.addEventListener('click', function () {
        var k = b.dataset.k;
        state[k] = b.dataset.v;
        document.querySelectorAll('.f-btn[data-k="' + k + '"]').forEach(function (x) {
          x.setAttribute('aria-pressed', x === b ? 'true' : 'false');
        });
        render();
      });
    });
    document.addEventListener('mv-lang', render);
    render();
  }

  /* ---------- product photos: counter on phones ---------- */
  var pics = document.getElementById('pics'), pc = document.getElementById('picCount');
  if (pics && pc) {
    var total = pics.children.length;
    function upd() {
      var w = pics.firstElementChild.getBoundingClientRect().width + 8;
      pc.textContent = Math.min(total, Math.round(pics.scrollLeft / w) + 1) + ' / ' + total;
    }
    pics.addEventListener('scroll', function () { requestAnimationFrame(upd); }, { passive: true });
    pics.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      var w = pics.firstElementChild.getBoundingClientRect().width + 8;
      pics.scrollBy({ left: e.key === 'ArrowRight' ? w : -w, behavior: 'smooth' });
    });
    upd();
  }
})();
