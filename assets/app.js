const providers = {
  aliyun: { name: '阿里云', english: 'ALIBABA CLOUD', mark: 'A' },
  tencent: { name: '腾讯云', english: 'TENCENT CLOUD', mark: 'T' },
  hoody: { name: 'Hoody', mark: 'H' },
  'experiential-labs': { name: 'Experiential Labs', mark: 'E' },
};
const categories = { server: '云服务器', ai: 'AI 工具与模型', agent: 'Agent 部署' };
const state = { provider: 'all', category: 'all', query: '', sort: 'recommended', data: null, links: null };
const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value = '') => String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const dateFormat = new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false });
const formatted = (value) => value ? dateFormat.format(new Date(value)) : '待核对';
const isFresh = (offer) => offer.status === 'verified' && offer.verifiedAt && Date.now() - new Date(offer.verifiedAt).getTime() < 48 * 60 * 60 * 1000;
const outbound = (offer) => state.links[offer.referral] ?? state.data.sources.find((source) => source.id === offer.sourceId).url;
const outboundRel = (offer) => offer.referral ? 'sponsored noopener' : 'noopener';

function card(offer, index) {
  const vendor = providers[offer.provider];
  const current = isFresh(offer);
  // Old observations remain in the dataset, but no stale price is presented as today's offer.
  const price = current ? offer.priceLabel : '查看活动';
  const suffix = current ? offer.priceSuffix : '最新价格待核对';
  let action = offer.referral ? `去${vendor.name}活动会场` : '查看官方定价';
  if (offer.referral === 'workbuddy') action = '查看 WorkBuddy 优惠';
  return `<article class="offer-card" style="animation-delay:${Math.min(index, 7) * 35}ms" data-offer="${escapeHtml(offer.id)}">
    <div class="card-top"><span class="vendor-icon ${offer.provider}">${vendor.mark}</span><div class="vendor-meta"><strong>${vendor.name}</strong>${vendor.english ? `<small>${vendor.english}</small>` : ''}</div><span class="status-label ${current ? '' : 'stale'}">${current ? '已核对' : '待核对'}</span></div>
    <h3>${escapeHtml(offer.title)}</h3><p class="card-description">${escapeHtml(offer.description)}</p><div class="tags">${offer.tags.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}</div>
    <div class="price-row"><strong class="price ${!current || offer.amount === null ? 'benefit' : ''}">${escapeHtml(price)}</strong><span class="price-suffix">${escapeHtml(suffix)}</span></div>
    <div class="card-bottom"><a class="card-cta" href="${escapeHtml(outbound(offer))}" target="_blank" rel="${outboundRel(offer)}">${action}<span aria-hidden="true">↗</span></a><button class="icon-button copy-button" data-copy="${escapeHtml(offer.id)}" aria-label="复制${escapeHtml(offer.title)}优惠入口" title="复制优惠入口">⧉</button></div>
    <button class="detail-button" data-detail="${escapeHtml(offer.id)}">价格条件与来源 · ${formatted(offer.verifiedAt)} ↗</button>
  </article>`;
}

function render() {
  if (!state.data) return;
  const query = state.query.trim().toLowerCase();
  const filtered = state.data.offers.filter((offer) => (state.provider === 'all' || offer.provider === state.provider)
    && (state.category === 'all' || offer.category === state.category)
    && `${offer.title} ${offer.description} ${offer.tags.join(' ')} ${providers[offer.provider].name} ${categories[offer.category]}`.toLowerCase().includes(query));
  filtered.sort(state.sort === 'latest' ? (a, b) => (Date.parse(b.changedAt) || 0) - (Date.parse(a.changedAt) || 0) : (a, b) => a.priority - b.priority);
  $('#offer-grid').innerHTML = filtered.map(card).join('');
  $('#empty-state').hidden = filtered.length > 0;
  $('#result-count').textContent = `${filtered.length} 条优惠`;
  $('#offers-title').textContent = state.category === 'all' ? '值得看看的优惠' : categories[state.category];
  document.querySelectorAll('[data-provider]').forEach((button) => {
    const selected = button.dataset.provider === state.provider;
    button.classList.toggle('selected', selected);
    button.setAttribute('aria-pressed', String(selected));
  });
  document.querySelectorAll('[data-category]').forEach((button) => {
    const selected = button.dataset.category === state.category;
    button.classList.toggle('active', selected);
    button.setAttribute('aria-pressed', String(selected));
  });
}

function renderUpdates() {
  const changes = state.data.changes.slice(0, 5);
  $('#updates-list').innerHTML = changes.length ? changes.map((change) => `<article class="update-row"><time class="update-date" datetime="${escapeHtml(change.at)}">${new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', month: '2-digit', day: '2-digit' }).format(new Date(change.at))}</time><div><h3>${escapeHtml(change.title)}</h3><p>${change.before ? `${escapeHtml(change.before)} <span class="update-arrow">→</span> ${escapeHtml(change.after)}` : `首次收录 · ${escapeHtml(change.after)}`}<span> · ${providers[change.provider].name}</span></p></div></article>`).join('') : '<p class="muted">还没有价格变化记录。下一次采集将持续追踪。</p>';
}

function showDetails(id) {
  const offer = state.data.offers.find((item) => item.id === id);
  if (!offer) return;
  const source = state.data.sources.find((item) => item.id === offer.sourceId);
  const action = offer.referral ? `进入${offer.referral === 'workbuddy' ? ' WorkBuddy ' : providers[offer.provider].name}优惠会场` : '查看官方定价';
  $('#dialog-content').innerHTML = `<p class="dialog-provider">${providers[offer.provider].name} / ${categories[offer.category]}</p><h2 id="dialog-title">${escapeHtml(offer.title)}</h2><p class="dialog-price">${escapeHtml(isFresh(offer) ? offer.priceLabel : '最新价格待核对')} <small class="price-suffix">${escapeHtml(isFresh(offer) ? offer.priceSuffix : '')}</small></p><p class="dialog-terms">${escapeHtml(offer.detail)}</p><dl><dt>官方活动原文${isFresh(offer) ? '' : '（上次采集记录）'}</dt><dd>${escapeHtml(offer.evidence || '暂未提取到明确价格，请前往会场查看。')}</dd><dt>采集来源</dt><dd>${escapeHtml(source.name)}<br>${escapeHtml(source.resolvedUrl || source.url)}</dd><dt>上次核对 / 最近检查</dt><dd>${formatted(offer.verifiedAt)} / ${formatted(offer.checkedAt)}</dd></dl><a class="primary-button" href="${escapeHtml(outbound(offer))}" target="_blank" rel="${outboundRel(offer)}">${action} ↗</a>`;
  $('#offer-dialog').showModal();
}

let toastTimer;
function toast(message) {
  clearTimeout(toastTimer);
  $('#toast').textContent = message;
  $('#toast').hidden = false;
  toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 3600);
}

async function copyOffer(id) {
  const offer = state.data.offers.find((item) => item.id === id);
  if (!offer) return;
  try { await navigator.clipboard.writeText(outbound(offer)); toast('优惠链接已复制，可以分享给朋友了。'); }
  catch { showDetails(id); toast('请长按或右键详情里的优惠入口复制链接。'); }
}

document.addEventListener('click', (event) => {
  const category = event.target.closest('[data-category]');
  const provider = event.target.closest('[data-provider]');
  const detail = event.target.closest('[data-detail]');
  const copy = event.target.closest('[data-copy]');
  if (category) { state.category = category.dataset.category; render(); $('#offers').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' }); }
  if (provider) { state.provider = provider.dataset.provider; render(); }
  if (detail) showDetails(detail.dataset.detail);
  if (copy) copyOffer(copy.dataset.copy);
});
$('#search').addEventListener('input', (event) => { state.query = event.target.value; render(); });
$('#sort').addEventListener('change', (event) => { state.sort = event.target.value; render(); });
$('#reset-filters').addEventListener('click', () => { Object.assign(state, { provider: 'all', category: 'all', query: '' }); $('#search').value = ''; render(); });
$('#close-dialog').addEventListener('click', () => $('#offer-dialog').close());
$('#offer-dialog').addEventListener('click', (event) => { if (event.target === $('#offer-dialog')) { const rect = event.target.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) event.target.close(); } });

async function init() {
  try {
    const [dataResponse, linksResponse] = await Promise.all([fetch('./data/offers.json'), fetch('./data/links.json')]);
    if (!dataResponse.ok || !linksResponse.ok) throw new Error('Data unavailable');
    [state.data, state.links] = await Promise.all([dataResponse.json(), linksResponse.json()]);
    $('#offer-count').textContent = state.data.offers.length;
    $('#nav-count').textContent = state.data.offers.length;
    $('#provider-count').textContent = new Set(state.data.offers.map((offer) => offer.provider)).size;
    $('#source-count').textContent = state.data.sources.length;
    const successCount = state.data.sources.filter((source) => source.status === 'ok').length;
    $('#last-check').textContent = `${formatted(state.data.generatedAt)} 更新${successCount < state.data.sources.length ? ' · 部分来源待重试' : ''}`;
    render(); renderUpdates();
  } catch {
    $('#offer-grid').innerHTML = '';
    $('#error-state').hidden = false;
    $('#last-check').textContent = '优惠数据暂时不可用';
    try {
      const response = await fetch('./data/links.json');
      if (!response.ok) return;
      const links = await response.json();
      $('#fallback-links').innerHTML = ['aliyun', 'tencent'].map((provider) => `<a class="secondary-button" target="_blank" rel="sponsored noopener" href="${escapeHtml(links[provider])}">${providers[provider].name}会场 ↗</a>`).join(' ');
    } catch { /* Keep the useful reload instruction if both files are unavailable. */ }
  }
}
init();
