
const COLORS = {
  Person: '#6d7cff', Film: '#23c4ff', Genre: '#f5b94c', Award: '#f87171', Platform: '#34d399',
  Country: '#a78bfa', Language: '#14b8a6', Decade: '#94a3b8', AudienceSegment: '#fb923c', Theme: '#38bdf8'
};
const CORE_NODE_TYPES = new Set(['Person', 'Film', 'Platform']);
let showAllNodeTypes = false;
const FOCUS_TYPES = {
  Person: [320, 140], Film: [100, 280], Genre: [560, 120], Award: [700, 240], Platform: [520, 460],
  Country: [180, 460], Language: [760, 420], Decade: [860, 120], AudienceSegment: [960, 300], Theme: [1160, 220]
};
let data, svg, width, height, simulation, linkSel, nodeSel, labelSel, selectedId = null, visibleNodes = [], visibleLinks = [], currentFilters = {}, currentSearch = '', motionMode = 'smooth', displayMode = 'full';
const typeOrder = ['Person','Film','Genre','Award','Platform','Language','Decade','AudienceSegment','Theme'];

function el(id){ return document.getElementById(id); }
function safe(v){ return (v === undefined || v === null || v === '') ? '—' : v; }
function norm(s){ return String(s || '').toLowerCase(); }
function splitPipe(value){ return String(value || '').split('|').map(s => s.trim()).filter(Boolean); }
function decadeFromYear(y){ const n = Number(y); return Number.isFinite(n) ? `${Math.floor(n/10)*10}s` : ''; }
function labelFor(n){ return n.label || n.title || n.name || n.id; }
function isChinese(v){ return /china|hong kong|taiwan|macau|malaysia/i.test(String(v || '')); }
function isAmerican(v){ return /united states|usa|u\.s\.?/i.test(String(v || '')); }
function countMatches(nodes, fn){ return nodes.filter(fn).length; }
function isRenderableNode(n){ return n && (showAllNodeTypes || CORE_NODE_TYPES.has(n.type)); }

function buildMetrics(meta){
  const nodeById = new Map(data.nodes.map(n => [n.id, n]));
  const peopleCount = countMatches(data.nodes, n => n.type === 'Person');
  const filmCount = countMatches(data.nodes, n => n.type === 'Film');
  const relationshipCount = data.links.filter(l => isRenderableNode(nodeById.get(resolveId(l.source))) && isRenderableNode(nodeById.get(resolveId(l.target)))).length;
  const chineseCreators = countMatches(data.nodes, n => n.type === 'Person' && isChinese(n.country || n.country_or_region || n.region));
  const americanCreators = countMatches(data.nodes, n => n.type === 'Person' && isAmerican(n.country || n.country_or_region || n.region));
  const cards = [
    ['People nodes', peopleCount, 'Creators in the interactive graph'],
    ['Films', filmCount, 'Works in the graph'],
    ['Relationships', relationshipCount, 'Edges across the network'],
    ['Chinese creators', chineseCreators, 'Chinese / Chinese-language talent'],
    ['American creators', americanCreators, 'U.S.-based talent'],
    ['Most connected person', meta.metrics.most_connected_person, 'Highest degree'],
    ['Most connected director', meta.metrics.most_connected_director, 'Director with highest degree'],
    ['Bridge-like creator', meta.metrics.bridge_like_creator, 'Highest cross-market score']
  ];
  el('metricGrid').innerHTML = cards.map(([label, value, sub]) => `
    <div class="metric"><div class="label">${label}</div><div class="value">${value}</div><div class="sub">${sub}</div></div>
  `).join('');
}

function setMetricSelection(){
  document.querySelectorAll('.metric').forEach(card => {
    const label = card.querySelector('.label')?.textContent || '';
    card.classList.toggle('selected', ['People nodes','Films','Relationships','Chinese creators','American creators'].includes(label));
  });
}

function setModeButtons(active){
  ['spotlightBtn','exploreBtn','peopleBtn','fullBtn'].forEach(id => {
    const btn = el(id);
    if (!btn) return;
    btn.classList.toggle('active', id.replace('Btn','') === active);
  });
}

function setTaxonomyButton(){
  const btn = el('taxonomyBtn');
  if (!btn) return;
  btn.textContent = showAllNodeTypes ? 'All node types' : 'Core nodes only';
  btn.classList.toggle('active', showAllNodeTypes);
}

function buildLegend(){
  el('legend').innerHTML = typeOrder.filter(t => showAllNodeTypes || CORE_NODE_TYPES.has(t)).map(t => `<div class="key"><span class="dot" style="background:${COLORS[t]}"></span>${t}</div>`).join('');
}

function buildFilters(nodes){
  const countrySet = new Set();
  const roleSet = new Set();
  const genreSet = new Set();
  const decadeSet = new Set();
  const marketSet = new Set();
  const platformSet = new Set();
  nodes.forEach(n => {
    if (n.country_or_region) countrySet.add(n.country_or_region);
    if (n.primary_role) roleSet.add(n.primary_role);
    if (n.genres) splitPipe(n.genres).forEach(g => genreSet.add(g));
    if (n.active_decades) splitPipe(n.active_decades).forEach(d => decadeSet.add(d));
    if (n.market_type) marketSet.add(n.market_type);
    if (n.platforms) splitPipe(n.platforms).forEach(p => platformSet.add(p));
    if (n.language) platformSet.add(n.language);
    if (n.type === 'Film' && n.year) decadeSet.add(decadeFromYear(n.year));
  });
  const configs = [
    ['country', 'Country / region', [...countrySet].sort()],
    ['role', 'Role', [...roleSet].sort()],
    ['genre', 'Genre', [...genreSet].sort()],
    ['decade', 'Decade', [...decadeSet].sort()],
    ['market', 'Market type', [...marketSet].sort()],
    ['platform', 'Platform / language', [...platformSet].sort()],
  ];
  el('filters').innerHTML = configs.map(([key, label, opts]) => `
    <label class="pill active">${label}
      <select data-filter="${key}" style="margin-left:8px;background:transparent;color:inherit;border:none;outline:none;max-width:180px">
        <option value="">All</option>
        ${opts.filter(Boolean).map(v => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join('')}
      </select>
    </label>
  `).join('');
  document.querySelectorAll('select[data-filter]').forEach(sel => {
    sel.addEventListener('change', e => {
      currentFilters[e.target.dataset.filter] = e.target.value;
      updateGraph();
    });
  });
}

function escapeHtml(s){
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[c]));
}

function nodeMatchesFilters(n){
  if (currentSearch && !norm(labelFor(n)).includes(currentSearch)) return false;
  if (currentFilters.country) {
    const match = norm(n.country_or_region).includes(norm(currentFilters.country)) || splitPipe(n.country_or_region).some(x => norm(x) === norm(currentFilters.country));
    if (!match) return false;
  }
  if (currentFilters.role && !norm(n.primary_role).includes(norm(currentFilters.role))) return false;
  if (currentFilters.genre) {
    const genres = splitPipe(n.genres || n.themes || '');
    const ok = genres.some(g => norm(g) === norm(currentFilters.genre) || norm(g).includes(norm(currentFilters.genre)));
    if (!ok) return false;
  }
  if (currentFilters.decade) {
    const decades = splitPipe(n.active_decades || '')
      .concat(n.year ? [decadeFromYear(n.year)] : [])
      .filter(Boolean);
    const ok = decades.some(d => norm(d) === norm(currentFilters.decade));
    if (!ok) return false;
  }
  if (currentFilters.market && !norm(n.market_type).includes(norm(currentFilters.market))) return false;
  if (currentFilters.platform) {
    const plats = splitPipe(n.platforms || '').concat(n.language ? [n.language] : []);
    const ok = plats.some(p => norm(p) === norm(currentFilters.platform) || norm(p).includes(norm(currentFilters.platform)));
    if (!ok) return false;
  }
  return true;
}

function resolveId(v){ return typeof v === 'object' && v ? v.id : v; }

function buildVisibility(){
  const nodeById = new Map(data.nodes.map(n => [n.id, n]));
  const matched = data.nodes.filter(n => isRenderableNode(n) && nodeMatchesFilters(n));
  const matchedIds = new Set(matched.map(d => d.id));
  const visible = new Set();
  const rank = data.nodes.filter(isRenderableNode).sort((a,b) => (b.importance || b.degree || 0) - (a.importance || a.degree || 0));

  if (displayMode === 'people') {
    const peopleNodes = currentSearch || Object.values(currentFilters).some(Boolean)
      ? matched.filter(n => n.type === 'Person')
      : data.nodes.filter(n => n.type === 'Person');
    peopleNodes.forEach(n => visible.add(n.id));
    if (selectedId) visible.add(selectedId);
    visibleNodes = data.nodes.filter(n => visible.has(n.id) && n.type === 'Person' && isRenderableNode(n));
    visibleLinks = data.links.filter(l => {
      const s = resolveId(l.source), t = resolveId(l.target);
      const sn = nodeById.get(s), tn = nodeById.get(t);
      return visible.has(s) && visible.has(t) && sn?.type === 'Person' && tn?.type === 'Person' && isRenderableNode(sn) && isRenderableNode(tn);
    });
    return visible;
  }

  const pickTopByType = (type, quota) => rank.filter(d => d.type === type).slice(0, quota).map(d => d.id);
  const seedBudget = displayMode === 'spotlight' ? 22 : displayMode === 'explore' ? 56 : rank.length;
  const seededTypes = displayMode === 'spotlight'
    ? { Person: 10, Film: 5, Award: 2, Platform: 2, Genre: 2, Language: 1 }
    : displayMode === 'explore'
      ? { Person: 18, Film: 10, Award: 6, Platform: 6, Genre: 6, Language: 4, Theme: 4, AudienceSegment: 2 }
      : {};
  const seedIds = new Set();
  if (displayMode !== 'full') {
    Object.entries(seededTypes).forEach(([type, quota]) => pickTopByType(type, quota).forEach(id => seedIds.add(id)));
    for (const node of rank) {
      if (seedIds.size >= seedBudget) break;
      seedIds.add(node.id);
    }
  } else {
    rank.forEach(n => seedIds.add(n.id));
  }
  const anchorIds = [selectedId, data.meta?.metrics?.bridge_like_creator, data.meta?.metrics?.most_connected_person, data.meta?.metrics?.most_connected_director]
    .filter(Boolean)
    .flatMap(v => {
      if (typeof v === 'string' && v.startsWith('Person:')) return [v];
      const found = data.nodes.find(n => labelFor(n) === v || n.id === v);
      return found ? [found.id] : [];
    });

  if (currentSearch || Object.values(currentFilters).some(Boolean)) {
    matchedIds.forEach(id => visible.add(id));
    data.links.forEach(l => {
      const s = resolveId(l.source), t = resolveId(l.target);
      if (matchedIds.has(s) || matchedIds.has(t)) { visible.add(s); visible.add(t); }
    });
  } else {
    seedIds.forEach(id => visible.add(id));
    anchorIds.forEach(id => visible.add(id));
    data.links.forEach(l => {
      const s = resolveId(l.source), t = resolveId(l.target);
      if (visible.has(s) || visible.has(t)) { visible.add(s); visible.add(t); }
    });

    if (displayMode !== 'full') {
      const cap = displayMode === 'spotlight' ? 26 : 44;
      const prioritized = [...visible].sort((a, b) => {
        const na = nodeById.get(a), nb = nodeById.get(b);
        return (nb?.importance || nb?.degree || 0) - (na?.importance || na?.degree || 0);
      });
      const keep = new Set([...seedIds, ...anchorIds].filter(Boolean));
      for (const id of prioritized) {
        if (keep.size >= cap) break;
        keep.add(id);
      }
      visible.clear();
      keep.forEach(id => visible.add(id));
    }
  }

  if (selectedId) {
    visible.add(selectedId);
    data.links.forEach(l => {
      const s = resolveId(l.source), t = resolveId(l.target);
      if (s === selectedId || t === selectedId) { visible.add(s); visible.add(t); }
    });
  }

  if (displayMode === 'full' && !(currentSearch || Object.values(currentFilters).some(Boolean))) {
    data.nodes.filter(isRenderableNode).forEach(n => visible.add(n.id));
  }

  visibleNodes = data.nodes.filter(n => visible.has(n.id) && isRenderableNode(n));
  visibleLinks = data.links.filter(l => {
    const s = resolveId(l.source), t = resolveId(l.target);
    const sn = nodeById.get(s), tn = nodeById.get(t);
    return visible.has(s) && visible.has(t) && isRenderableNode(sn) && isRenderableNode(tn);
  });
  return visible;
}

function renderList(container, rows, kind){
  el(container).innerHTML = rows.map((r, idx) => {
    const title = r.name || r.title;
    const meta = kind === 'people'
      ? `${r.role || 'Talent'} · ${safe(r.country)} · degree ${r.degree} · cross-market ${r.cross_market_score || 0}`
      : `${safe(r.country)} · ${safe(r.year)} · ${safe(r.market_type)} · degree ${r.degree}`;
    return `<div class="item" data-jump="${escapeHtml(title)}"><div class="name">${idx+1}. ${escapeHtml(title)}</div><div class="meta">${escapeHtml(meta)}</div></div>`;
  }).join('');
  el(container).querySelectorAll('[data-jump]').forEach(item => item.addEventListener('click', e => {
    const title = e.currentTarget.dataset.jump;
    const node = data.nodes.find(n => labelFor(n) === title);
    if (node) selectNode(node.id, true);
  }));
}

function buildSidePanels(){
  renderList('bridgePeople', data.meta.top_people, 'people');
  renderList('bridgeFilms', data.meta.top_films, 'films');
  el('questionChips').innerHTML = [
    'Why might Ang Lee be a bridge figure?',
    'Which Chinese actors have strong international positioning?',
    'Which American directors are award heavy?',
    'Which creators connect action cinema across markets?'
  ].map(q => `<button class="chip" data-q="${escapeHtml(q)}">${escapeHtml(q)}</button>`).join('');
  el('questionChips').querySelectorAll('[data-q]').forEach(btn => btn.addEventListener('click', e => {
    const q = e.currentTarget.dataset.q;
    el('explainOutput').innerHTML = explainQuestion(q);
  }));
  el('storyBtn').addEventListener('click', () => {
    el('storyOutput').innerHTML = positionStory(el('storyInput').value);
  });
  el('storyInput').addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') el('storyBtn').click();
  });
}

function positionStory(prompt){
  const text = norm(prompt);
  const genres = [];
  const refs = [];
  const directors = [];
  const actors = [];
  const platforms = [];
  const segments = [];
  const risks = [];
  const match = (terms) => terms.some(t => text.includes(t));
  const pushUnique = (arr, item) => { if (item && !arr.includes(item)) arr.push(item); };
  if (match(['sci-fi','science fiction','space'])) { ['Sci-Fi', 'Dune', 'Interstellar', 'Arrival', 'The Wandering Earth'].forEach(x => pushUnique(refs, x)); pushUnique(genres, 'Sci-Fi'); }
  if (match(['thriller','crime','suspense'])) { ['Thriller', 'Get Out', 'Se7en', 'Black Coal, Thin Ice'].forEach(x => pushUnique(refs, x)); pushUnique(genres, 'Thriller'); }
  if (match(['family','mother','father','daughter','son'])) { ['Drama', 'Minari', 'The Farewell', 'Eat Drink Man Woman', 'Hi, Mom'].forEach(x => pushUnique(refs, x)); pushUnique(genres, 'Drama'); }
  if (match(['identity','memory','self'])) { ['Everything Everywhere All at Once', 'The Farewell', 'Lost in Translation', 'Moonlight'].forEach(x => pushUnique(refs, x)); pushUnique(genres, 'Drama'); }
  if (match(['action','martial','fight'])) { ['Hero', 'The Wandering Earth', 'Black Panther', 'Mulan'].forEach(x => pushUnique(refs, x)); pushUnique(genres, 'Action'); }
  if (match(['female','women','woman'])) { ['Greta Gerwig', 'Chloé Zhao', 'Ava DuVernay', 'Michelle Yeoh', 'Zhang Ziyi', 'Meryl Streep'].forEach(x => pushUnique(actors, x)); }
  if (match(['global','international','cross-market','cross cultural','cross-cultural'])) { pushUnique(segments, 'Global streaming audience'); pushUnique(segments, 'Prestige-drama audience'); }
  if (match(['streaming','platform'])) { ['Netflix', 'Disney+', 'MUBI', 'Max', 'Apple TV+'].forEach(x => pushUnique(platforms, x)); }
  if (match(['award','prestige','festival'])) { ['Ang Lee', 'Chloé Zhao', 'Christopher Nolan', 'Michelle Yeoh', 'Meryl Streep'].forEach(x => pushUnique(directors, x)); }
  if (!genres.length) { genres.push('Drama', 'Cross-market'); }
  if (!refs.length) { ['The Farewell', 'Nomadland', 'Everything Everywhere All at Once', 'Crouching Tiger, Hidden Dragon'].forEach(x => pushUnique(refs, x)); }
  if (!directors.length) { ['Ang Lee', 'Chloé Zhao', 'Christopher Nolan'].forEach(x => pushUnique(directors, x)); }
  if (!actors.length) { ['Michelle Yeoh', 'Zendaya', 'Steven Yeun'].forEach(x => pushUnique(actors, x)); }
  if (!platforms.length) { ['Netflix', 'Disney+', 'MUBI'].forEach(x => pushUnique(platforms, x)); }
  if (!segments.length) segments.push('Global streaming audience');
  if (match(['thriller','crime'])) risks.push('Tone needs a clear hook and stakes; otherwise it can read generic.');
  if (match(['family'])) risks.push('Character specificity matters more than plot mechanics.');
  if (match(['global','international','cross-market'])) risks.push('Casting and cultural translation need explicit strategy.');
  if (match(['female','women'])) risks.push('Lead perspective should be concrete, not just thematic.');
  if (!risks.length) risks.push('Balance reach with a specific emotional proposition.');

  return `
    <div class="card"><div><span class="badge">Recommended genres</span> ${genres.map(x => `<span class="pill">${escapeHtml(x)}</span>`).join(' ')}</div></div>
    <div class="card"><div><span class="badge">Reference films</span> ${refs.slice(0,5).map(x => `<span class="pill">${escapeHtml(x)}</span>`).join(' ')}</div></div>
    <div class="card"><div><span class="badge">Potential directors</span> ${directors.slice(0,5).map(x => `<span class="pill">${escapeHtml(x)}</span>`).join(' ')}</div></div>
    <div class="card"><div><span class="badge">Potential actors</span> ${actors.slice(0,5).map(x => `<span class="pill">${escapeHtml(x)}</span>`).join(' ')}</div></div>
    <div class="card"><div><span class="badge">Possible platforms</span> ${platforms.slice(0,5).map(x => `<span class="pill">${escapeHtml(x)}</span>`).join(' ')}</div></div>
    <div class="card"><div><span class="badge">Audience segments</span> ${segments.map(x => `<span class="pill">${escapeHtml(x)}</span>`).join(' ')}</div></div>
    <div class="card"><div><span class="badge">Market risks</span><div style="margin-top:8px;color:var(--muted)">${risks.map(x => `• ${escapeHtml(x)}`).join('<br>')}</div></div></div>
    <div class="card"><span class="badge">Positioning statement</span><div style="margin-top:8px;line-height:1.6">${escapeHtml(`A ${genres.slice(0,2).join(' / ')} project with ${refs.slice(0,3).join(', ')} as reference points and a ${platforms.slice(0,3).join(', ')} launch strategy.`)}</div></div>
  `;
}

function explainQuestion(q){
  const text = norm(q);
  let facts = [], explanation = '';
  if (text.includes('ang lee')) {
    facts = [
      'Ang Lee links Chinese-language cinema, Hong Kong cinema, and U.S. prestige cinema.',
      'His strongest anchors in this demo include Crouching Tiger, Hidden Dragon and Eat Drink Man Woman.',
      'The bridge signal is strongest when award recognition and international distribution overlap.'
    ];
    explanation = 'Ang Lee works as a bridge because the network connects him to Chinese-language works with strong international reach. That combination makes him useful for cross-market projects that need credibility in more than one industry.';
  } else if (text.includes('international positioning')) {
    facts = [
      'Michelle Yeoh, Zhang Ziyi, Tony Leung Chiu-wai, Gong Li, and Jackie Chan sit near the center of the cross-market cluster.',
      'They connect awards, festival attention, and international distribution.',
      'Their graph paths run through prestige films as well as commercial releases.'
    ];
    explanation = 'These performers travel well because they are not confined to one market. They show up in award-heavy films, cross-border titles, and projects with strong audience recognition.';
  } else if (text.includes('award') || text.includes('prestige')) {
    facts = [
      'American prestige directors cluster around Scorsese, Fincher, Spielberg, Chazelle, Jenkins, and Bigelow.',
      'The awards layer is dense around Academy Awards, BAFTA, Cannes, and Venice.',
      'The supporting cast often repeats across drama and thriller subgraphs.'
    ];
    explanation = 'The graph shows prestige creators through repeated award pathways and overlapping casts. These nodes sit in tightly connected film clusters that are useful for awards-season strategy.';
  } else {
    facts = [
      'Bridge nodes appear when a creator has both high degree and high cross-market signal.',
      'Films with mixed market-type labels tend to sit between Chinese-language and American clusters.',
      'The graph favors people who connect multiple genres, awards, and markets.'
    ];
    explanation = 'This is a graph-grounded answer, not a prediction engine. It uses the network structure, people-film links, and the award/platform context to explain why a creator or film matters.';
  }
  return `
    <div class="card"><span class="badge">Graph facts</span><div style="margin-top:8px;line-height:1.7">${facts.map(x => `• ${escapeHtml(x)}`).join('<br>')}</div></div>
    <div class="card"><span class="badge">Explanation</span><div style="margin-top:8px;line-height:1.7">${escapeHtml(explanation)}</div></div>
  `;
}

function detailHTML(n){
  if (!n) return '<div class="card">Select a node in the graph to inspect profile details, collaborators, and network context.</div>';
  const relatedLinks = data.links.filter(l => resolveId(l.source) === n.id || resolveId(l.target) === n.id).slice(0, 18);
  const related = relatedLinks.map(l => {
    const otherId = resolveId(l.source) === n.id ? resolveId(l.target) : resolveId(l.source);
    const other = data.nodes.find(x => x.id === otherId);
    return `<span class="pill">${escapeHtml(labelFor(other || {label:l.target}))} · ${escapeHtml(l.relationship)}</span>`;
  }).join(' ');
  const stats = [`degree ${n.degree || 0}`, `importance ${Number(n.importance || 0).toFixed(1)}`];
  if (n.type === 'Person') stats.push(`cross-market ${safe(n.cross_market_score)}`);
  if (n.type === 'Film') stats.push(`rating ${safe(n.rating_score)}`, `popularity ${safe(n.popularity_score)}`);
  let body = '';
  if (n.type === 'Person') {
    body = `
      <div class="card"><div><span class="badge">Profile</span><div class="name" style="font-size:18px;font-weight:800">${escapeHtml(n.label)}</div><div class="small">${escapeHtml(stats.join(' · '))}</div></div></div>
      <div class="card"><span class="badge">Known for</span><div style="margin-top:8px;line-height:1.6">${escapeHtml(n.known_for || n.main_cast || '—')}</div></div>
      <div class="card"><span class="badge">Creative signals</span><div style="margin-top:8px;line-height:1.8">Role: ${escapeHtml(safe(n.primary_role))}<br>Country / region: ${escapeHtml(safe(n.country_or_region))}<br>Active decades: ${escapeHtml(safe(n.active_decades))}<br>Award score: ${escapeHtml(safe(n.award_score))}<br>Genre diversity: ${escapeHtml(safe(n.genre_diversity_score))}</div></div>
      <div class="card"><span class="badge">Connected neighbors</span><div style="margin-top:8px">${related || '—'}</div></div>
    `;
  } else if (n.type === 'Film') {
    body = `
      <div class="card"><div><span class="badge">Film</span><div class="name" style="font-size:18px;font-weight:800">${escapeHtml(n.label)}</div><div class="small">${escapeHtml(stats.join(' · '))}</div></div></div>
      <div class="card"><span class="badge">Strategy profile</span><div style="margin-top:8px;line-height:1.8">Year: ${escapeHtml(safe(n.year))}<br>Country / region: ${escapeHtml(safe(n.country_or_region))}<br>Language: ${escapeHtml(safe(n.language))}<br>Genres: ${escapeHtml(safe(n.genres))}<br>Market type: ${escapeHtml(safe(n.market_type))}</div></div>
      <div class="card"><span class="badge">Audience signals</span><div style="margin-top:8px;line-height:1.8">Rating score: ${escapeHtml(safe(n.rating_score))}<br>Popularity score: ${escapeHtml(safe(n.popularity_score))}<br>Themes: ${escapeHtml(safe(n.themes))}<br>Platforms: ${escapeHtml(safe(n.platforms))}</div></div>
      <div class="card"><span class="badge">Connected neighbors</span><div style="margin-top:8px">${related || '—'}</div></div>
    `;
  } else {
    body = `
      <div class="card"><div><span class="badge">Node</span><div class="name" style="font-size:18px;font-weight:800">${escapeHtml(n.label)}</div><div class="small">${escapeHtml(stats.join(' · '))}</div></div></div>
      <div class="card"><span class="badge">Type attributes</span><div style="margin-top:8px;line-height:1.8">Type: ${escapeHtml(n.type)}<br>Country / region: ${escapeHtml(safe(n.country_or_region))}<br>Primary role: ${escapeHtml(safe(n.primary_role))}<br>Year: ${escapeHtml(safe(n.year))}</div></div>
      <div class="card"><span class="badge">Connected neighbors</span><div style="margin-top:8px">${related || '—'}</div></div>
    `;
  }
  return body;
}

function selectNode(id, center=false){
  selectedId = id;
  const n = data.nodes.find(x => x.id === id);
  if (!n) return;
  el('selectedTitle').textContent = n.label;
  el('selectedBody').innerHTML = detailHTML(n);
  nodeSel.classed('selected', d => d.id === id);
  labelSel.classed('selected', d => d.id === id);
  document.querySelectorAll('.item').forEach(elm => elm.classList.toggle('active', elm.dataset.jump === n.label));
  if (center) {
    simulation.alphaTarget(motionMode === 'playful' ? 0.22 : 0.15).restart();
    data.nodes.forEach(m => { m.fx = null; m.fy = null; });
    n.fx = width / 2; n.fy = height / 2;
    setTimeout(() => { n.fx = null; n.fy = null; simulation.alpha(motionMode === 'playful' ? 0.9 : 0.7).restart(); }, motionMode === 'playful' ? 1700 : 1400);
  }
}

function updateGraph(){
  const visible = buildVisibility();
  const visibleSet = new Set(visibleNodes.map(d => d.id));
  const ranked = [...visibleNodes].sort((a,b) => (b.importance||0) - (a.importance||0));
  const nodeById = new Map(visibleNodes.map(d => [d.id, d]));
  const filteredLinks = visibleLinks.map(l => ({
    ...l,
    source: nodeById.get(resolveId(l.source)),
    target: nodeById.get(resolveId(l.target)),
  })).filter(l => l.source && l.target);

  linkSel = svg.select('.links').selectAll('line').data(filteredLinks, d => `${d.source.id}-${d.target.id}-${d.relationship}`);
  linkSel.exit().remove();
  const linkEnter = linkSel.enter().append('line').attr('stroke', 'rgba(148,163,184,.22)').attr('stroke-width', d => Math.max(0.6, Math.min(3, (d.weight || 1) / 2)));
  linkSel = linkEnter.merge(linkSel);

  nodeSel = svg.select('.nodes').selectAll('circle').data(ranked, d => d.id);
  nodeSel.exit().remove();
  const nodeEnter = nodeSel.enter().append('circle')
    .attr('r', d => sizeFor(d))
    .attr('fill', d => nodeColor(d))
    .attr('stroke', 'rgba(255,255,255,.85)')
    .attr('stroke-width', 1.1)
    .attr('opacity', 0)
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))
    .on('mouseover', showTooltip)
    .on('mousemove', showTooltip)
    .on('mouseout', hideTooltip)
    .on('click', (event, d) => { selectNode(d.id, true); });
  nodeSel = nodeEnter.merge(nodeSel);
  nodeEnter.transition().duration(500).attr('opacity', 1);

  const labelThreshold = displayMode === 'people' ? 100 : displayMode === 'spotlight' ? 999 : displayMode === 'explore' ? 210 : 180;
  labelSel = svg.select('.labels').selectAll('text').data(ranked.filter(d => d.id === selectedId || (d.type === 'Person' && (d.importance || 0) > labelThreshold) || (d.type === 'Film' && (d.importance || 0) > labelThreshold + 15)), d => d.id);
  labelSel.exit().remove();
  const labelEnter = labelSel.enter().append('text').attr('fill', '#dbeafe').attr('font-size', 11).attr('font-weight', 700).attr('text-anchor', 'middle').attr('pointer-events', 'none')
    .text(d => labelFor(d).length > 24 ? `${labelFor(d).slice(0,21)}…` : labelFor(d));
  labelSel = labelEnter.merge(labelSel);

  simulation.nodes(ranked);
  simulation.force('link').links(filteredLinks);
  simulation.force('charge', d3.forceManyBody().strength(d => {
    if (motionMode === 'playful') return d.type === 'Person' ? -220 : d.type === 'Film' ? -170 : -110;
    return d.type === 'Person' ? -140 : d.type === 'Film' ? -120 : -80;
  }));
  simulation.force('collision', d3.forceCollide().radius(d => sizeFor(d) + (motionMode === 'playful' ? 6 : 4)).iterations(2));
  simulation.force('link').distance(d => motionMode === 'playful' ? Math.max(42, distanceFor(d) - 16) : distanceFor(d));
  simulation.alpha(motionMode === 'playful' ? 0.9 : 0.7).restart();
  nodeSel.attr('opacity', 1);
  linkSel.attr('opacity', 1);
  labelSel.attr('opacity', d => selectedId === d.id ? 1 : 0.88);
}

function sizeFor(d){
  const base = d.type === 'Person' ? 9 : d.type === 'Film' ? 8 : 6;
  const scale = Math.log1p(Number(d.importance || d.degree || 1)) * (d.type === 'Person' ? 2.6 : 2.0);
  return Math.max(base, Math.min(28, base + scale));
}

function showTooltip(event, d){
  const tip = el('tooltip');
  tip.classList.remove('hidden');
  tip.style.left = `${event.offsetX + 14}px`;
  tip.style.top = `${event.offsetY + 14}px`;
  const bits = [
    `<strong>${escapeHtml(d.label)}</strong>`,
    `${escapeHtml(d.type)}`,
    d.type === 'Person' ? `Cross-market score: ${safe(d.cross_market_score)}` : `Market type: ${safe(d.market_type)}`,
    `Degree: ${safe(d.degree)}`
  ].filter(Boolean);
  tip.innerHTML = bits.join('<br>');
}
function hideTooltip(){ el('tooltip').classList.add('hidden'); }

function hashText(str){
  let h = 0;
  for (const ch of String(str || '')) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return h;
}

function sizeFor(d){
  if (displayMode === 'people' && d.type === 'Person') {
    const score = Number(d.cross_market_score || d.international_recognition_score || d.degree || 1);
    return 8 + Math.log1p(score) * 1.7;
  }
  const base = d.type === 'Person' ? 9 : d.type === 'Film' ? 8 : 6;
  const scale = Math.log1p(Number(d.importance || d.degree || 1)) * (d.type === 'Person' ? 2.6 : 2.0);
  return Math.max(base, Math.min(28, base + scale));
}

function nodeColor(d){
  if (displayMode === 'people' && d.type === 'Person') {
    const role = norm(d.primary_role || '');
    if (role.includes('director')) return '#b66dff';
    if (role.includes('actress')) return '#ff7aa8';
    if (role.includes('actor')) return '#4fb8ff';
    if (role.includes('writer')) return '#f59e0b';
    return '#7dd3fc';
  }
  return COLORS[d.type] || '#fff';
}

function anchorX(d){
  if (displayMode === 'people' && d.type === 'Person') {
    const anchors = [150, 320, 490, 660, 830, 1000, 1170, 200, 540, 900];
    return anchors[hashText(`${labelFor(d)}:${d.primary_role}`) % anchors.length];
  }
  return selectedId && d.id === selectedId ? width/2 : (FOCUS_TYPES[d.type]?.[0] || width/2);
}

function anchorY(d){
  if (displayMode === 'people' && d.type === 'Person') {
    const anchors = [150, 210, 260, 330, 390, 450, 520];
    return anchors[hashText(`${d.country_or_region || ''}:${labelFor(d)}`) % anchors.length];
  }
  return selectedId && d.id === selectedId ? height/2 : (FOCUS_TYPES[d.type]?.[1] || height/2);
}

function distanceFor(d){ return d.relationship === 'DIRECTED' || d.relationship === 'ACTED_IN' ? 64 : 84; }
function dragstarted(event, d){ if (!event.active) simulation.alphaTarget(0.25).restart(); d.fx = d.x; d.fy = d.y; }
function dragged(event, d){ d.fx = event.x; d.fy = event.y; }
function dragended(event, d){ if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }

function applyForces(){
  simulation = d3.forceSimulation()
    .force('link', d3.forceLink().id(d => d.id).distance(d => distanceFor(d)).strength(0.07))
    .force('charge', d3.forceManyBody().strength(d => d.type === 'Person' ? -140 : d.type === 'Film' ? -120 : -80))
    .force('collision', d3.forceCollide().radius(d => sizeFor(d) + 4).iterations(2))
    .force('x', d3.forceX(d => anchorX(d)).strength(.06))
    .force('y', d3.forceY(d => anchorY(d)).strength(.06))
    .on('tick', ticked);
}

function ticked(){
  nodeSel.attr('cx', d => d.x = Math.max(20, Math.min(width-20, d.x))).attr('cy', d => d.y = Math.max(20, Math.min(height-20, d.y)));
  linkSel.attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y);
  labelSel.attr('x', d => d.x).attr('y', d => d.y + sizeFor(d) + 10);
}

const FALLBACK_DATA = {
  meta: {
    metrics: {
      people: 12,
      films: 6,
      relationships: 24,
      chinese_creators: 6,
      american_creators: 6,
      most_connected_person: 'Ang Lee',
      most_connected_director: 'Ang Lee',
      bridge_like_creator: 'Ang Lee'
    },
    top_people: [
      { name: 'Ang Lee', role: 'Director', country: 'Taiwan / United States', degree: 8, cross_market_score: 98 },
      { name: 'Michelle Yeoh', role: 'Actor', country: 'Malaysia / Hong Kong / United States', degree: 7, cross_market_score: 96 },
      { name: 'Tony Leung Chiu-wai', role: 'Actor', country: 'Hong Kong', degree: 7, cross_market_score: 92 }
    ],
    top_films: [
      { title: 'Crouching Tiger, Hidden Dragon', country: 'China / United States', year: 2000, market_type: 'Cross-cultural', degree: 8 },
      { title: 'Everything Everywhere All at Once', country: 'United States', year: 2022, market_type: 'Cross-cultural', degree: 8 },
      { title: 'The Farewell', country: 'United States', year: 2019, market_type: 'Cross-cultural', degree: 7 }
    ]
  },
  nodes: [
    { id:'Person:Ang Lee', type:'Person', label:'Ang Lee', name:'Ang Lee', country_or_region:'Taiwan / United States', primary_role:'Director', active_decades:'1990s|2000s|2010s|2020s', known_for:'Crouching Tiger, Hidden Dragon|Eat Drink Man Woman', degree:8, cross_market_score:98, importance:92 },
    { id:'Person:Michelle Yeoh', type:'Person', label:'Michelle Yeoh', name:'Michelle Yeoh', country_or_region:'Malaysia / Hong Kong / United States', primary_role:'Actor', active_decades:'1990s|2000s|2010s|2020s', known_for:'Everything Everywhere All at Once|Crouching Tiger, Hidden Dragon', degree:7, cross_market_score:96, importance:88 },
    { id:'Person:Tony Leung Chiu-wai', type:'Person', label:'Tony Leung Chiu-wai', name:'Tony Leung Chiu-wai', country_or_region:'Hong Kong', primary_role:'Actor', active_decades:'1980s|1990s|2000s|2010s|2020s', known_for:'In the Mood for Love|Shang-Chi and the Legend of the Ten Rings', degree:7, cross_market_score:92, importance:86 },
    { id:'Person:Zhang Ziyi', type:'Person', label:'Zhang Ziyi', name:'Zhang Ziyi', country_or_region:'China', primary_role:'Actor', active_decades:'1990s|2000s|2010s|2020s', known_for:'Crouching Tiger, Hidden Dragon|Hero', degree:6, cross_market_score:90, importance:84 },
    { id:'Person:Chloé Zhao', type:'Person', label:'Chloé Zhao', name:'Chloé Zhao', country_or_region:'China / United States', primary_role:'Director', active_decades:'2010s|2020s', known_for:'Nomadland|The Rider', degree:6, cross_market_score:95, importance:89 },
    { id:'Person:Christopher Nolan', type:'Person', label:'Christopher Nolan', name:'Christopher Nolan', country_or_region:'United Kingdom / United States', primary_role:'Director', active_decades:'2000s|2010s|2020s', known_for:'Inception|Oppenheimer', degree:6, cross_market_score:78, importance:82 },
    { id:'Film:Crouching Tiger, Hidden Dragon', type:'Film', label:'Crouching Tiger, Hidden Dragon', title:'Crouching Tiger, Hidden Dragon', year:2000, country_or_region:'China / United States', language:'Mandarin', genres:'Action|Drama', market_type:'Cross-cultural', rating_score:96, popularity_score:94, themes:'Honor|Desire|Legacy', degree:8, importance:90 },
    { id:'Film:Everything Everywhere All at Once', type:'Film', label:'Everything Everywhere All at Once', title:'Everything Everywhere All at Once', year:2022, country_or_region:'United States', language:'English', genres:'Action|Sci-Fi|Drama', market_type:'Cross-cultural', rating_score:95, popularity_score:96, themes:'Identity|Family|Multiverse', degree:8, importance:91 },
    { id:'Film:The Farewell', type:'Film', label:'The Farewell', title:'The Farewell', year:2019, country_or_region:'United States', language:'English / Mandarin', genres:'Drama', market_type:'Cross-cultural', rating_score:91, popularity_score:88, themes:'Family|Identity|Diaspora', degree:7, importance:83 },
    { id:'Film:Hero', type:'Film', label:'Hero', title:'Hero', year:2002, country_or_region:'China', language:'Mandarin', genres:'Action|Drama', market_type:'Domestic', rating_score:90, popularity_score:89, themes:'Honor|Sacrifice', degree:6, importance:80 },
    { id:'Country:China', type:'Country', label:'China', country_or_region:'China', degree:6, importance:64 },
    { id:'Country:United States', type:'Country', label:'United States', country_or_region:'United States', degree:6, importance:62 },
    { id:'Platform:Netflix', type:'Platform', label:'Netflix', platforms:'Netflix', degree:4, importance:60 },
    { id:'Award:Oscars', type:'Award', label:'Oscars', degree:4, importance:58 },
    { id:'Theme:Identity', type:'Theme', label:'Identity', degree:4, importance:55 },
    { id:'Genre:Drama', type:'Genre', label:'Drama', degree:5, importance:57 }
  ],
  links: [
    { source:'Person:Ang Lee', target:'Film:Crouching Tiger, Hidden Dragon', relationship:'DIRECTED', weight:3 },
    { source:'Person:Michelle Yeoh', target:'Film:Crouching Tiger, Hidden Dragon', relationship:'ACTED_IN', weight:3 },
    { source:'Person:Zhang Ziyi', target:'Film:Crouching Tiger, Hidden Dragon', relationship:'ACTED_IN', weight:3 },
    { source:'Person:Tony Leung Chiu-wai', target:'Film:Everything Everywhere All at Once', relationship:'ACTED_IN', weight:2 },
    { source:'Person:Michelle Yeoh', target:'Film:Everything Everywhere All at Once', relationship:'ACTED_IN', weight:3 },
    { source:'Person:Chloé Zhao', target:'Film:The Farewell', relationship:'PRODUCED', weight:1 },
    { source:'Film:Crouching Tiger, Hidden Dragon', target:'Country:China', relationship:'MADE_IN_COUNTRY', weight:2 },
    { source:'Film:Crouching Tiger, Hidden Dragon', target:'Country:United States', relationship:'CROSSES_MARKET', weight:2 },
    { source:'Film:Everything Everywhere All at Once', target:'Country:United States', relationship:'MADE_IN_COUNTRY', weight:2 },
    { source:'Film:Everything Everywhere All at Once', target:'Award:Oscars', relationship:'WON_AWARD', weight:2 },
    { source:'Film:Everything Everywhere All at Once', target:'Theme:Identity', relationship:'HAS_THEME', weight:2 },
    { source:'Film:The Farewell', target:'Platform:Netflix', relationship:'DISTRIBUTED_ON', weight:1 },
    { source:'Film:The Farewell', target:'Theme:Identity', relationship:'HAS_THEME', weight:2 },
    { source:'Film:Hero', target:'Genre:Drama', relationship:'BELONGS_TO_GENRE', weight:2 },
    { source:'Person:Christopher Nolan', target:'Award:Oscars', relationship:'NOMINATED_FOR', weight:1 }
  ]
};

async function loadData(){
  try { return await (await fetch('graph-data.json', { cache: 'no-store' })).json(); }
  catch (err) { return FALLBACK_DATA; }
}

async function init(){
  data = await loadData();
  buildMetrics(data.meta);
  setMetricSelection();
  buildLegend();
  buildFilters(data.nodes);
  buildSidePanels();
  el('selectedBody').innerHTML = '<div class="card">Select a bubble to see a graph-grounded profile, connections, and strategy context.</div>';
  width = el('graph').clientWidth;
  height = el('graph').clientHeight;
  svg = d3.select('#graph').attr('viewBox', `0 0 ${width} ${height}`);
  svg.append('g').attr('class', 'links');
  svg.append('g').attr('class', 'nodes');
  svg.append('g').attr('class', 'labels');
  applyForces();
  setModeButtons(displayMode);
  setTaxonomyButton();
  el('motionBtn').textContent = 'Motion: Smooth';
  const initialName = data.meta?.metrics?.bridge_like_creator || 'Ang Lee';
  const initialNode = data.nodes.find(n => labelFor(n) === initialName || n.label === initialName);
  selectedId = null;
  updateGraph();
  if (initialNode) {
    el('selectedTitle').textContent = 'Playground';
    el('selectedBody').innerHTML = '<div class="card"><span class="badge">Opening mode</span><div style="margin-top:8px;line-height:1.6;color:var(--muted)">The network opens in a core mix of creators, films, and platforms so the first screen stays focused. Use the taxonomy toggle if you want to expand all node types.</div></div>';
  }
  window.addEventListener('resize', () => {
    width = el('graph').clientWidth; height = el('graph').clientHeight;
    svg.attr('viewBox', `0 0 ${width} ${height}`);
    simulation.force('x', d3.forceX(d => anchorX(d)).strength(.06));
    simulation.force('y', d3.forceY(d => anchorY(d)).strength(.06));
    simulation.alpha(0.3).restart();
  });
  el('searchBox').addEventListener('input', e => {
    currentSearch = norm(e.target.value);
    updateGraph();
  });
  el('spotlightBtn').addEventListener('click', () => { displayMode = 'spotlight'; setModeButtons(displayMode); updateGraph(); });
  el('exploreBtn').addEventListener('click', () => { displayMode = 'explore'; setModeButtons(displayMode); updateGraph(); });
  el('peopleBtn').addEventListener('click', () => { displayMode = 'people'; setModeButtons(displayMode); updateGraph(); });
  el('fullBtn').addEventListener('click', () => { displayMode = 'full'; setModeButtons(displayMode); updateGraph(); });
  el('taxonomyBtn').addEventListener('click', () => { showAllNodeTypes = !showAllNodeTypes; setTaxonomyButton(); buildLegend(); updateGraph(); });
  el('motionBtn').addEventListener('click', () => {
    motionMode = motionMode === 'smooth' ? 'playful' : 'smooth';
    el('motionBtn').textContent = motionMode === 'smooth' ? 'Motion: Smooth' : 'Motion: Playful';
    updateGraph();
  });
  el('surpriseBtn').addEventListener('click', () => {
    const pool = data.meta.top_people.length ? data.meta.top_people : data.nodes.filter(n => n.type === 'Person');
    const pick = pool[Math.floor(Math.random() * Math.min(pool.length, 8))];
    const target = data.nodes.find(n => n.label === (pick.name || pick.label));
    if (target) selectNode(target.id, true);
  });
  el('resetBtn').addEventListener('click', () => {
    currentFilters = {}; currentSearch = ''; selectedId = null;
    displayMode = 'full';
    motionMode = 'smooth';
    showAllNodeTypes = false;
    setModeButtons(displayMode);
    setTaxonomyButton();
    el('motionBtn').textContent = 'Motion: Smooth';
    document.querySelectorAll('select[data-filter]').forEach(sel => sel.value = '');
    el('searchBox').value = '';
    el('storyInput').value = 'A female-led sci-fi thriller about memory, family, and identity for a global streaming audience.';
    el('selectedTitle').textContent = 'Select a node';
    el('selectedBody').innerHTML = '<div class="card">Select a bubble to see a graph-grounded profile, connections, and strategy context.</div>';
    updateGraph();
  });
  el('storyInput').value = 'A female-led sci-fi thriller about memory, family, and identity for a global streaming audience.';
  el('storyOutput').innerHTML = positionStory(el('storyInput').value);
  el('explainOutput').innerHTML = explainQuestion('Why might Ang Lee be a strong bridge figure between Chinese and American cinema?');
}

init();
