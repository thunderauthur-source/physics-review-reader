const $ = (s) => document.querySelector(s);
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

const COURSES = {
  qm: { label: '量子力学', outline: 'outline_qm.html', key: 'qm.reader.v2.qm', manifest: 'qm' },
  thermo: { label: '热力学统计物理', outline: 'outline_thermo.html', key: 'qm.reader.v2.thermo', manifest: 'thermo' }
};

const STUDY_KEY = 'phys.study.v1';
const LAYOUT_KEY = 'phys.layout.v1';

let course = 'qm';

const state = {
  docs: [],
  cards: [],
  problems: {},
  docId: null,
  page: 1,
  endPage: 0,
  printed: '',
  zoom: 1,
  preload: new Map()
};

function loadJson(key, fallback) {
  try {
    const v = JSON.parse(localStorage.getItem(key) || 'null');
    return v || fallback;
  } catch (e) { return fallback; }
}

let study = loadJson(STUDY_KEY, { bookmarks: [], notes: {}, highlights: {}, visited: {} });
study.bookmarks = study.bookmarks || [];
study.notes = study.notes || {};
study.highlights = study.highlights || {};
study.visited = study.visited || {};

const layout = loadJson(LAYOUT_KEY, { course: 'qm', width: 0, zoom: 1, focus: false });

function saveStudy() {
  try { localStorage.setItem(STUDY_KEY, JSON.stringify(study)); } catch (e) { /* ignore */ }
}

function saveLayout() {
  const pane = $('#outlinePane');
  try {
    localStorage.setItem(LAYOUT_KEY, JSON.stringify({
      course: course,
      width: parseInt(pane.style.width, 10) || 0,
      zoom: state.zoom,
      focus: document.body.classList.contains('focus')
    }));
  } catch (e) { /* ignore */ }
}

function pageKey(docId, page) {
  return course + '|' + docId + '|' + page;
}

function manifest() {
  return (window.__MANIFESTS__ && window.__MANIFESTS__[COURSES[course].manifest]) || null;
}

function saveProgress() {
  if (!state.docId) return;
  try {
    localStorage.setItem(COURSES[course].key, JSON.stringify({
      doc: state.docId, page: state.page, end: state.endPage, printed: state.printed
    }));
  } catch (e) { /* ignore */ }
}

function loadProgress(c) {
  try {
    let raw = localStorage.getItem(COURSES[c].key);
    if (!raw && c === 'qm') raw = localStorage.getItem('qm.reader.v1');
    const s = JSON.parse(raw || 'null');
    return s && s.doc ? s : null;
  } catch (e) { return null; }
}

/* ---------------- 文档与页面 ---------------- */
function docById(id) {
  return state.docs.find((d) => d.id === id);
}

function pageUrl(doc, page) {
  const name = doc.pagePattern.replace('%04d', String(page).padStart(4, '0'));
  return new URL('../' + doc.pageDir + '/' + name, location.href).href;
}

function buildDocSelect() {
  const sel = $('#docSel');
  const groups = [
    ['教材与解答', state.docs.filter((d) => d.kind === 'book' || d.kind === 'solutions')],
    ['讲义与课件', state.docs.filter((d) => d.kind === 'deck')]
  ];
  sel.innerHTML = '';
  for (const [label, list] of groups) {
    if (!list.length) continue;
    const og = document.createElement('optgroup');
    og.label = label;
    for (const d of list) {
      const opt = document.createElement('option');
      opt.value = d.id;
      opt.textContent = d.title;
      og.appendChild(opt);
    }
    sel.appendChild(og);
  }
  if (state.docId) sel.value = state.docId;
}

function cardForPage(page) {
  const doc = docById(state.docId);
  if (!doc) return null;
  const byDeck = state.cards.find((c) => c.deck === doc.id);
  if (byDeck) return byDeck;
  return state.cards.find((c) =>
    (c.doc === doc.id && page >= c.start && page <= c.end) ||
    (c.bookDoc === doc.id && page >= c.bookStart && page <= c.bookEnd)
  ) || null;
}

function problemForPage(page) {
  let best = null;
  for (const [num, info] of Object.entries(state.problems || {})) {
    const p = info.sol;
    if (p === page) return num;
    if (Math.abs(p - page) <= 1 && !best) best = num;
  }
  return best;
}

function layoutImage() {
  const img = $('#pageImg');
  const pane = $('#pdfPane');
  const width = Math.max(200, Math.round((pane.clientWidth - 30) * state.zoom));
  img.style.width = width + 'px';
}

function preloadPage(doc, page) {
  if (!doc || page < 1 || page > doc.pages) return;
  const key = doc.id + ':' + page;
  if (state.preload.has(key)) return;
  const img = new Image();
  img.src = pageUrl(doc, page);
  state.preload.set(key, img);
  if (state.preload.size > 8) {
    const first = state.preload.keys().next().value;
    state.preload.delete(first);
  }
}

function openDoc(docId, page, endPage, printed) {
  const doc = docById(docId);
  if (!doc || !doc.pageDir) return;
  state.docId = doc.id;
  state.endPage = endPage || 0;
  state.printed = printed || '';
  const sel = $('#docSel');
  if (sel.querySelector('option[value="' + doc.id + '"]')) sel.value = doc.id;
  $('#pageTotal').textContent = '/ ' + doc.pages;
  $('#docInfo').textContent = doc.title + ' · 共 ' + doc.pages + ' 页';
  const slider = $('#pageSlider');
  slider.max = doc.pages;
  slider.value = page;
  renderPage(page || 1);
}

function renderPage(page) {
  const doc = docById(state.docId);
  if (!doc) return;
  page = clamp(page, 1, doc.pages);
  state.page = page;

  const img = $('#pageImg');
  const url = pageUrl(doc, page);
  $('#loading').classList.add('show');

  img.onload = () => {
    $('#loading').classList.remove('show');
    layoutImage();
    updateIndicators();
    saveProgress();
    renderHighlights();
    updateBookmarkBtn();
    updateNoteForPage();
    const key = pageKey(state.docId, state.page);
    study.visited[key] = (study.visited[key] || 0) + 1;
    saveStudy();
  };
  img.onerror = () => {
    $('#loading').classList.remove('show');
    $('#statusText').textContent = '页面图片加载失败：' + url;
  };
  img.src = url;

  $('#pageSlider').value = page;
  preloadPage(doc, page - 1);
  preloadPage(doc, page + 1);
  updateIndicators();
  updateBookmarkBtn();
}

function updateIndicators() {
  const doc = docById(state.docId);
  $('#pageInput').value = state.page;
  let printed = '';
  if (doc && doc.offset && state.page - doc.offset > 0) {
    printed = '（印刷 ' + (state.page - doc.offset) + '）';
  } else if (state.printed) {
    printed = '（定位 ' + state.printed + '）';
  }
  $('#pageTotal').textContent = '/ ' + (doc ? doc.pages : '–');

  if (state.endPage && state.endPage >= state.page) {
    $('#rangeInfo').textContent = '第 ' + state.page + '–' + state.endPage + ' 页' +
      (doc && doc.offset ? ' · 印刷 ' + (state.page - doc.offset) + '–' + (state.endPage - doc.offset) : '');
  } else {
    $('#rangeInfo').textContent = printed;
  }

  const card = cardForPage(state.page);
  const prob = doc && doc.kind === 'solutions' ? problemForPage(state.page) : null;
  if (prob) {
    $('#statusText').textContent = '对应解答：习题 ' + prob + ' —— 点“定位卡片”回提纲';
  } else if (card) {
    $('#statusText').textContent = '对应卡片：' + card.label + ' —— 点“定位卡片”回到提纲';
  } else {
    $('#statusText').textContent = doc ? doc.title + ' · 第 ' + state.page + ' 页' : '就绪';
  }
  $('#statusbar').dataset.card = card ? card.id : '';
  $('#statusbar').dataset.problem = prob || '';
}

/* ---------------- 课程切换 ---------------- */
function switchCourse(next, restore) {
  if (!COURSES[next]) return;
  if (next === course && state.docId) return;
  saveProgress();
  course = next;
  document.body.classList.toggle('course-thermo', next === 'thermo');

  const mf = manifest() || {};
  state.docs = mf.docs || [];
  state.cards = mf.cards || [];
  state.problems = mf.problems || {};
  state.docId = null;
  state.page = 1;
  state.endPage = 0;
  state.printed = '';

  $('#courseSel').value = next;
  buildDocSelect();

  const frame = $('#outline');
  const src = COURSES[next].outline;
  if (!frame.getAttribute('src') || !frame.getAttribute('src').endsWith(src)) {
    frame.setAttribute('src', src);
  }

  const saved = restore ? loadProgress(next) : null;
  if (saved && docById(saved.doc)) {
    openDoc(saved.doc, saved.page, saved.end || 0, saved.printed || '');
  } else if (state.docs.length) {
    openDoc(state.docs[0].id, 1, 0, '');
  }
  renderBmList();
  renderNoteList();
  renderStat();
  saveLayout();
}

/* ---------------- 书签 / 笔记 / 高亮 ---------------- */
function currentBookmarkIndex() {
  return study.bookmarks.findIndex((b) => b.course === course && b.doc === state.docId && b.page === state.page);
}

function updateBookmarkBtn() {
  const on = currentBookmarkIndex() >= 0;
  $('#bookmarkBtn').classList.toggle('on', on);
  $('#bookmarkBtn').textContent = on ? '★' : '☆';
}

function toggleBookmark() {
  const doc = docById(state.docId);
  if (!doc) return;
  const i = currentBookmarkIndex();
  if (i >= 0) {
    study.bookmarks.splice(i, 1);
  } else {
    study.bookmarks.push({
      course: course, doc: doc.id, page: state.page,
      title: doc.title, ts: Date.now()
    });
  }
  saveStudy();
  updateBookmarkBtn();
  renderBmList();
  renderStat();
}

function jumpToBookmark(b) {
  if (b.course !== course) switchCourse(b.course, false);
  setTimeout(() => openDoc(b.doc, b.page, 0, ''), b.course !== course ? 120 : 0);
}

function renderBmList() {
  const box = $('#bmList');
  const list = study.bookmarks.filter((b) => b.course === course)
    .sort((a, b) => (a.doc === b.doc ? a.page - b.page : a.ts - b.ts));
  box.innerHTML = list.length ? '' : '<div class="hint">还没有书签。翻到某页后点顶栏 ☆ 收藏。</div>';
  for (const b of list) {
    const item = document.createElement('div');
    item.className = 'item';
    item.innerHTML = '<div>' + b.title + ' · 第 ' + b.page + ' 页</div>' +
      '<div class="meta2">' + new Date(b.ts).toLocaleString() + '</div>';
    item.addEventListener('click', () => jumpToBookmark(b));
    box.appendChild(item);
  }
}

function updateNoteForPage() {
  const doc = docById(state.docId);
  $('#notePageLabel').textContent = doc ? doc.title + ' · 第 ' + state.page + ' 页' : '当前页';
  $('#noteText').value = study.notes[pageKey(state.docId, state.page)] || '';
}

function saveNote() {
  const key = pageKey(state.docId, state.page);
  const text = $('#noteText').value.trim();
  if (text) study.notes[key] = text;
  else delete study.notes[key];
  saveStudy();
  renderNoteList();
  renderStat();
  $('#statusText').textContent = text ? '笔记已保存' : '本页笔记已删除';
}

function deleteNote() {
  delete study.notes[pageKey(state.docId, state.page)];
  $('#noteText').value = '';
  saveStudy();
  renderNoteList();
  renderStat();
}

function parsePageKey(key) {
  const parts = key.split('|');
  return { course: parts[0], doc: parts[1], page: Number(parts[2]) };
}

function renderNoteList() {
  const box = $('#noteList');
  const entries = Object.keys(study.notes)
    .filter((k) => k.split('|')[0] === course)
    .sort((a, b) => (study.notes[b] || '').length - (study.notes[a] || '').length);
  box.innerHTML = entries.length ? '' : '<div class="hint">还没有笔记。切到「笔记」标签，给当前页写点东西。</div>';
  for (const key of entries) {
    const p = parsePageKey(key);
    const doc = state.docs.find((d) => d.id === p.doc);
    const item = document.createElement('div');
    item.className = 'item';
    item.innerHTML = '<div>' + (doc ? doc.title : p.doc) + ' · 第 ' + p.page + ' 页</div>' +
      '<div class="meta2">' + study.notes[key].slice(0, 80) + '</div>';
    item.addEventListener('click', () => openDoc(p.doc, p.page, 0, ''));
    box.appendChild(item);
  }
}

function currentHighlights() {
  return study.highlights[pageKey(state.docId, state.page)] || [];
}

function renderHighlights() {
  const layer = $('#hlLayer');
  layer.innerHTML = '';
  currentHighlights().forEach((r, i) => {
    const div = document.createElement('div');
    div.className = 'hl';
    div.style.left = (r.x * 100) + '%';
    div.style.top = (r.y * 100) + '%';
    div.style.width = (r.w * 100) + '%';
    div.style.height = (r.h * 100) + '%';
    div.dataset.index = i;
    layer.appendChild(div);
  });
}

function toggleHighlightMode() {
  const on = !document.body.classList.contains('hl-mode');
  document.body.classList.toggle('hl-mode', on);
  $('#hlBtn').classList.toggle('on', on);
  $('#statusText').textContent = on ? '高亮模式：在页面上拖拽框选；点已有高亮可删除' : '已退出高亮模式';
}

function clearHighlights() {
  delete study.highlights[pageKey(state.docId, state.page)];
  saveStudy();
  renderHighlights();
  renderStat();
}

function bindHighlightDrag() {
  const layer = $('#hlLayer');
  let dragging = false;
  let start = null;
  let temp = null;

  layer.addEventListener('pointerdown', (e) => {
    if (!document.body.classList.contains('hl-mode')) return;
    if (e.target.classList && e.target.classList.contains('hl')) {
      const idx = Number(e.target.dataset.index);
      const arr = currentHighlights();
      arr.splice(idx, 1);
      if (arr.length) study.highlights[pageKey(state.docId, state.page)] = arr;
      else delete study.highlights[pageKey(state.docId, state.page)];
      saveStudy();
      renderHighlights();
      e.stopPropagation();
      return;
    }
    const rect = layer.getBoundingClientRect();
    start = { x: (e.clientX - rect.left) / rect.width, y: (e.clientY - rect.top) / rect.height };
    dragging = true;
    temp = document.createElement('div');
    temp.className = 'hl';
    layer.appendChild(temp);
    try { layer.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
    e.preventDefault();
  });

  layer.addEventListener('pointermove', (e) => {
    if (!dragging || !temp) return;
    const rect = layer.getBoundingClientRect();
    const x = clamp((e.clientX - rect.left) / rect.width, 0, 1);
    const y = clamp((e.clientY - rect.top) / rect.height, 0, 1);
    const left = Math.min(start.x, x), top = Math.min(start.y, y);
    const w = Math.abs(x - start.x), h = Math.abs(y - start.y);
    temp.style.left = (left * 100) + '%';
    temp.style.top = (top * 100) + '%';
    temp.style.width = (w * 100) + '%';
    temp.style.height = (h * 100) + '%';
  });

  const finish = () => {
    if (!dragging || !temp) return;
    dragging = false;
    const w = parseFloat(temp.style.width) / 100;
    const h = parseFloat(temp.style.height) / 100;
    temp.remove();
    temp = null;
    if (w > 0.01 && h > 0.01) {
      const arr = currentHighlights();
      arr.push({
        x: parseFloat(start.x.toFixed(4)),
        y: parseFloat(start.y.toFixed(4)),
        w: parseFloat(w.toFixed(4)),
        h: parseFloat(h.toFixed(4))
      });
      study.highlights[pageKey(state.docId, state.page)] = arr;
      saveStudy();
      renderHighlights();
      renderStat();
    }
  };
  layer.addEventListener('pointerup', finish);
  layer.addEventListener('pointercancel', finish);
}

/* ---------------- 学习统计 / 备份 ---------------- */
function renderStat() {
  const bm = study.bookmarks.filter((b) => b.course === course).length;
  const noteKeys = Object.keys(study.notes).filter((k) => k.split('|')[0] === course);
  let hl = 0;
  for (const k of Object.keys(study.highlights)) {
    if (k.split('|')[0] === course) hl += (study.highlights[k] || []).length;
  }
  const visited = Object.keys(study.visited).filter((k) => k.split('|')[0] === course).length;
  const doc = docById(state.docId);
  $('#statBox').innerHTML =
    '<div class="list">' +
    '<div class="item"><b>' + COURSES[course].label + '</b><div class="meta2">' +
    (doc ? doc.title + ' · 第 ' + state.page + ' / ' + doc.pages + ' 页' : '') + '</div></div>' +
    '<div class="item">书签 <b>' + bm + '</b> 个</div>' +
    '<div class="item">笔记 <b>' + noteKeys.length + '</b> 页</div>' +
    '<div class="item">高亮 <b>' + hl + '</b> 处</div>' +
    '<div class="item">已访问页面 <b>' + visited + '</b> 页</div>' +
    '</div>';
}

function downloadBlob(blob, name) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}

function exportCurrentPage() {
  const img = $('#pageImg');
  if (!img.complete || !img.naturalWidth) return;
  const canvas = document.createElement('canvas');
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;
  canvas.getContext('2d').drawImage(img, 0, 0);
  canvas.toBlob((blob) => {
    if (blob) downloadBlob(blob, (state.docId || 'page') + '_p' + state.page + '.png');
  }, 'image/png');
}

function backupData() {
  const data = {};
  for (const k of ['qm.reader.v2.qm', 'qm.reader.v2.thermo', 'qm.reader.v1', STUDY_KEY, LAYOUT_KEY]) {
    const v = localStorage.getItem(k);
    if (v !== null) data[k] = v;
  }
  downloadBlob(new Blob([JSON.stringify(data, null, 1)], { type: 'application/json' }),
    '物理提纲学习备份_' + new Date().toISOString().slice(0, 10) + '.json');
  $('#statusText').textContent = '备份已导出';
}

function restoreData(file) {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const data = JSON.parse(reader.result);
      for (const k of Object.keys(data)) localStorage.setItem(k, data[k]);
      location.reload();
    } catch (e) {
      $('#statusText').textContent = '备份文件解析失败：' + e.message;
    }
  };
  reader.readAsText(file);
}

/* ---------------- 目录 ---------------- */
function buildToc() {
  const box = $('#tocList');
  box.innerHTML = '';
  const groups = new Map();

  const add = (docId, start, end, printed, label, cardId) => {
    if (!docId || !start) return;
    if (!groups.has(docId)) groups.set(docId, []);
    groups.get(docId).push({ start: start, end: end || start, printed: printed || '', label: label, cardId: cardId });
  };

  for (const c of state.cards) {
    if (c.bookDoc) add(c.bookDoc, c.bookStart, c.bookEnd, c.bookPrinted, c.label, c.id);
    if (c.doc) add(c.doc, c.start, c.end, c.printed, c.label, c.id);
    else if (c.deck) add(c.deck, c.deckStart || 1, c.deckEnd || c.deckStart || 1, '', c.label, c.id);
  }

  for (const [docId, items] of groups) {
    const doc = docById(docId);
    const head = document.createElement('div');
    head.className = 'toc-group';
    head.textContent = doc ? doc.title : docId;
    box.appendChild(head);
    for (const it of items) {
      const item = document.createElement('div');
      item.className = 'item';
      let pageText = '第 ' + it.start + '–' + it.end + ' 页';
      if (doc && doc.offset) {
        pageText += '（印刷 ' + (it.start - doc.offset) + '–' + (it.end - doc.offset) + '）';
      }
      item.innerHTML = '<div>' + it.label + '</div><div class="meta2">' + pageText + '</div>';
      item.addEventListener('click', () => {
        closeToc();
        openDoc(docId, it.start, it.end, it.printed || '');
        postToOutline({ type: 'reveal-card', card: it.cardId });
      });
      box.appendChild(item);
    }
  }
}

function openToc() {
  buildToc();
  $('#tocModal').classList.add('open');
}
function closeToc() { $('#tocModal').classList.remove('open'); }

/* ---------------- 全局搜索 ---------------- */
function searchEntries(q) {
  const index = window.__SEARCH_INDEX__ || [];
  q = q.trim().toLowerCase();
  if (!q) return index.slice(0, 14);
  const scored = [];
  for (const e of index) {
    const title = (e.title || '').toLowerCase();
    const sec = (e.sec || '').toLowerCase();
    const text = (e.text || '').toLowerCase();
    let score = 0;
    if (title.includes(q)) score += 6;
    if (sec.includes(q)) score += 4;
    if (text.includes(q)) score += 2;
    if (score) scored.push({ e, score });
  }
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, 28).map((x) => x.e);
}

function renderSearchResults(q) {
  const box = $('#searchResults');
  const list = searchEntries(q);
  box.innerHTML = list.length ? '' : '<div class="hint">没有匹配结果</div>';
  for (const e of list) {
    const item = document.createElement('div');
    item.className = 'item';
    const pageInfo = e.bookDoc
      ? ('教材 pp.' + e.bookPrinted + (e.doc ? ' · 讲义 pp.' + e.printed : ''))
      : (e.doc ? (e.start + '–' + e.end + ' 页') : '无页码');
    item.innerHTML = '<div><span class="tag2">' + e.courseTitle + '</span>' +
      (e.sec ? e.sec + ' ' : '') + (e.title || '') + '</div>' +
      '<div class="meta2">' + pageInfo + ' · ' + (e.text || '').slice(0, 90) + '</div>';
    item.addEventListener('click', () => goEntry(e));
    box.appendChild(item);
  }
  $('#searchHint').textContent = '共 ' + list.length + ' 条';
}

function goEntry(e) {
  closeSearch();
  const delay = e.course !== course ? 160 : 0;
  if (e.course !== course) switchCourse(e.course, false);
  const docId = e.bookDoc || e.doc;
  const start = e.bookDoc ? e.bookStart : e.start;
  const end = e.bookDoc ? e.bookEnd : e.end;
  const printed = e.bookDoc ? e.bookPrinted : e.printed;
  setTimeout(() => {
    if (docId) openDoc(docId, start || 1, end || 0, printed || '');
    postToOutline({ type: 'reveal-card', card: e.id });
  }, delay);
}

function openSearch() {
  $('#searchModal').classList.add('open');
  const input = $('#searchInput');
  input.value = '';
  renderSearchResults('');
  setTimeout(() => input.focus(), 30);
}
function closeSearch() { $('#searchModal').classList.remove('open'); }

/* ---------------- 抽屉 ---------------- */
function openDrawer(tab) {
  $('#drawer').classList.add('open');
  if (tab) setDrawerTab(tab);
  updateNoteForPage();
  renderBmList();
  renderNoteList();
  renderStat();
}
function closeDrawer() { $('#drawer').classList.remove('open'); }
function setDrawerTab(tab) {
  document.querySelectorAll('.drawer-tabs button').forEach((b) => b.classList.toggle('on', b.dataset.tab === tab));
  document.querySelectorAll('.tabpane').forEach((p) => p.classList.toggle('on', p.id === 'tab-' + tab));
}

function toggleFocus() {
  const on = !document.body.classList.contains('focus');
  document.body.classList.toggle('focus', on);
  $('#focusBtn').classList.toggle('on', on);
  saveLayout();
  layoutImage();
}

/* ---------------- 与提纲通信 ---------------- */
function postToOutline(msg) {
  const frame = $('#outline');
  if (frame && frame.contentWindow) frame.contentWindow.postMessage(msg, '*');
}

window.addEventListener('message', (ev) => {
  const data = ev.data || {};
  if (data.type === 'theme') {
    document.body.classList.toggle('dark', !!data.dark);
    return;
  }
  if (data.type !== 'open-doc') return;
  if (!docById(data.doc)) {
    const target = String(data.doc).indexOf('thermo') === 0 ? 'thermo' : 'qm';
    if (target !== course) switchCourse(target, false);
  }
  openDoc(data.doc, Number(data.page) || 1, Number(data.end) || 0, data.printed || '');
});

function locateCard() {
  const card = cardForPage(state.page);
  if (card) {
    postToOutline({ type: 'reveal-card', card: card.id });
    $('#statusText').textContent = '已在提纲中定位：' + card.label;
    return;
  }
  const doc = docById(state.docId);
  const prob = doc && doc.kind === 'solutions' ? problemForPage(state.page) : null;
  if (prob) {
    postToOutline({ type: 'reveal-card', card: 'ex' });
    postToOutline({ type: 'flash-text', text: '习题 ' + prob });
    $('#statusText').textContent = '已在提纲“考点与习题归类”中定位习题 ' + prob;
    return;
  }
  $('#statusText').textContent = '当前页没有绑定的提纲卡片';
}

/* ---------------- UI 事件 ---------------- */
function wireUI() {
  $('#courseSel').addEventListener('change', (e) => switchCourse(e.target.value, true));
  $('#prevBtn').addEventListener('click', () => renderPage(state.page - 1));
  $('#nextBtn').addEventListener('click', () => renderPage(state.page + 1));
  $('#pageInput').addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return;
    const n = parseInt(e.target.value, 10);
    if (Number.isFinite(n)) renderPage(n);
    e.target.blur();
  });
  $('#pageSlider').addEventListener('input', (e) => renderPage(Number(e.target.value)));
  $('#zoomIn').addEventListener('click', () => {
    state.zoom = clamp(state.zoom * 1.2, 0.4, 4);
    $('#fitBtn').classList.remove('on');
    layoutImage();
    saveLayout();
  });
  $('#zoomOut').addEventListener('click', () => {
    state.zoom = clamp(state.zoom / 1.2, 0.4, 4);
    $('#fitBtn').classList.remove('on');
    layoutImage();
    saveLayout();
  });
  $('#fitBtn').addEventListener('click', () => {
    state.zoom = 1;
    $('#fitBtn').classList.add('on');
    layoutImage();
    saveLayout();
  });
  $('#locateBtn').addEventListener('click', locateCard);
  $('#statusText').addEventListener('click', locateCard);
  $('#bookmarkBtn').addEventListener('click', toggleBookmark);
  $('#hlBtn').addEventListener('click', toggleHighlightMode);
  $('#studyBtn').addEventListener('click', () => openDrawer('bm'));
  $('#tocBtn').addEventListener('click', openToc);
  $('#searchBtn').addEventListener('click', openSearch);
  $('#focusBtn').addEventListener('click', toggleFocus);

  $('#drawerClose').addEventListener('click', closeDrawer);
  document.querySelectorAll('.drawer-tabs button').forEach((b) => {
    b.addEventListener('click', () => setDrawerTab(b.dataset.tab));
  });
  $('#bmClear').addEventListener('click', () => {
    study.bookmarks = study.bookmarks.filter((b) => b.course !== course);
    saveStudy();
    renderBmList();
    renderStat();
    updateBookmarkBtn();
  });
  $('#noteSave').addEventListener('click', saveNote);
  $('#noteClear').addEventListener('click', deleteNote);
  $('#exportPage').addEventListener('click', exportCurrentPage);
  $('#clearHl').addEventListener('click', clearHighlights);
  $('#backupBtn').addEventListener('click', backupData);
  $('#restoreBtn').addEventListener('click', () => $('#restoreFile').click());
  $('#restoreFile').addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) restoreData(e.target.files[0]);
  });

  $('#searchClose').addEventListener('click', closeSearch);
  $('#searchInput').addEventListener('input', (e) => renderSearchResults(e.target.value));
  $('#searchInput').addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeSearch();
    if (e.key === 'Enter') {
      const first = $('#searchResults .item');
      if (first) first.click();
    }
  });
  $('#outlineSearchBtn').addEventListener('click', () => {
    closeSearch();
    postToOutline({ type: 'focus-search' });
  });
  $('#tocClose').addEventListener('click', closeToc);

  document.querySelectorAll('.modal').forEach((m) => {
    m.addEventListener('click', (e) => {
      if (e.target === m) m.classList.remove('open');
    });
  });

  document.addEventListener('keydown', (e) => {
    const tag = (e.target.tagName || '').toUpperCase();
    const typing = tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA';
    if (e.key === 'Escape') {
      closeSearch(); closeToc(); closeDrawer();
      if (document.body.classList.contains('hl-mode')) toggleHighlightMode();
      return;
    }
    if (typing) return;

    if ((e.ctrlKey || e.metaKey) && e.key === '1') { e.preventDefault(); switchCourse('qm', true); }
    if ((e.ctrlKey || e.metaKey) && e.key === '2') { e.preventDefault(); switchCourse('thermo', true); }
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openSearch(); }
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'f') { e.preventDefault(); openSearch(); }

    if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); renderPage(state.page - 1); }
    if (e.key === 'ArrowRight' || e.key === 'PageDown') { e.preventDefault(); renderPage(state.page + 1); }
    if (e.key === '[' || e.key === ']') {
      const i = state.docs.findIndex((d) => d.id === state.docId);
      const n = i + (e.key === ']' ? 1 : -1);
      if (n >= 0 && n < state.docs.length) openDoc(state.docs[n].id, 1, 0, '');
    }
    if (e.key === 'g' || e.key === 'G') {
      const v = prompt('跳到第几页？');
      const n = parseInt(v, 10);
      if (Number.isFinite(n)) renderPage(n);
    }
    if (e.key === '+' || e.key === '=') { state.zoom = clamp(state.zoom * 1.2, 0.4, 4); $('#fitBtn').classList.remove('on'); layoutImage(); saveLayout(); }
    if (e.key === '-') { state.zoom = clamp(state.zoom / 1.2, 0.4, 4); $('#fitBtn').classList.remove('on'); layoutImage(); saveLayout(); }
    if (e.key === '0') { state.zoom = 1; $('#fitBtn').classList.add('on'); layoutImage(); saveLayout(); }
    if (e.key === 'f' || e.key === 'F') toggleFocus();
    if (e.key === 'b' || e.key === 'B') toggleBookmark();
    if (e.key === 'n' || e.key === 'N') openDrawer('note');
    if (e.key === 't' || e.key === 'T') openToc();
    if (e.key === 'h' || e.key === 'H') toggleHighlightMode();
    if (e.key === '/') { e.preventDefault(); openSearch(); }
  });

  // 分栏拖动
  const splitter = $('#splitter');
  let dragging = false;

  const onDragMove = (e) => {
    if (!dragging) return;
    const rect = $('#main').getBoundingClientRect();
    const w = clamp(e.clientX - rect.left, 320, rect.width - 340);
    $('#outlinePane').style.width = w + 'px';
  };

  const endDrag = (e) => {
    if (!dragging) return;
    dragging = false;
    document.body.classList.remove('dragging');
    try {
      if (e && splitter.hasPointerCapture(e.pointerId)) {
        splitter.releasePointerCapture(e.pointerId);
      }
    } catch (err) { /* ignore */ }
    layoutImage();
    saveLayout();
  };

  splitter.addEventListener('pointerdown', (e) => {
    dragging = true;
    document.body.classList.add('dragging');
    try { splitter.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
    e.preventDefault();
  });
  splitter.addEventListener('pointermove', onDragMove);
  splitter.addEventListener('pointerup', endDrag);
  splitter.addEventListener('pointercancel', endDrag);
  splitter.addEventListener('lostpointercapture', () => endDrag(null));
  window.addEventListener('blur', () => endDrag(null));

  window.addEventListener('resize', () => {
    if (state.zoom === 1) layoutImage();
  });

  $('#outline').addEventListener('load', () => {
    postToOutline({ type: 'request-theme' });
    const card = cardForPage(state.page);
    if (card) postToOutline({ type: 'reveal-card', card: card.id, silent: true });
    renderBmList();
    renderNoteList();
    renderStat();
  });
}

/* ---------------- 启动 ---------------- */
function boot() {
  try {
    wireUI();
    bindHighlightDrag();

    if (layout.width) $('#outlinePane').style.width = layout.width + 'px';
    if (layout.zoom) state.zoom = layout.zoom;
    $('#fitBtn').classList.toggle('on', state.zoom === 1);
    if (layout.focus) {
      document.body.classList.add('focus');
      $('#focusBtn').classList.add('on');
    }
    const startCourse = layout.course === 'thermo' ? 'thermo' : 'qm';
    switchCourse(startCourse, true);
    updateNoteForPage();
    renderBmList();
    renderNoteList();
    renderStat();
  } catch (err) {
    $('#statusText').textContent = '初始化失败：' + err.message;
    $('#loading').classList.remove('show');
  }
}

boot();
