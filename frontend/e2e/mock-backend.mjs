import { createServer } from 'node:http';

const PORT = process.env.MOCK_BACKEND_PORT || 8001;

const now = () => new Date().toISOString();

const FIXTURE_SIGNALS = [
  {
    id: 'e2e-signal-hot-0001',
    source: 'reddit',
    source_id: 'reddit_hot_1',
    url: 'https://reddit.com/r/tmobile/hot1',
    title: 'Switching carriers today, T-Mobile overcharged me again',
    text: "I've had it with T-Mobile's billing. Switching to a competitor this week, anyone have recommendations?",
    author: null,
    geography: 'US-TX',
    harvested_at: now(),
    source_created_at: now(),
    raw_metadata: {},
    category: 'telecom_mobile',
    intent_type: 'churn_risk',
    classification_confidence: 0.94,
    keywords: ['billing', 'switch', 'tmobile'],
    competitor_mentions: ['T-Mobile'],
    classified_at: now(),
    score: 82,
    tier: 'hot',
    velocity_delta_24h: 340,
    velocity_delta_7d: 210,
    engagement_score: 0.8,
    scored_at: now(),
  },
  {
    id: 'e2e-signal-watch-0002',
    source: 'google_trends',
    source_id: 'trends_home_internet_1',
    url: 'https://trends.google.com/trends/explore?q=fiber+internet',
    title: 'Trending: fiber internet',
    text: "Google Trends signal for 'fiber internet' in category 'home_internet'. Interest: 40/100.",
    author: null,
    geography: 'global',
    harvested_at: now(),
    source_created_at: null,
    raw_metadata: {},
    category: 'home_internet',
    intent_type: 'comparison',
    classification_confidence: 0.7,
    keywords: ['fiber', 'internet'],
    competitor_mentions: [],
    classified_at: now(),
    score: 22,
    tier: 'watch',
    velocity_delta_24h: 12,
    velocity_delta_7d: -5,
    engagement_score: 0.3,
    scored_at: now(),
  },
];

const FIXTURE_BRAND = {
  id: 'e2e-brand-0001',
  name: 'Acme Mobile',
  contact_email: 'leads@acme.test',
  categories: ['telecom_mobile', 'home_internet'],
  geographies: [],
  min_tier: 'watch',
  keywords_include: [],
  keywords_exclude: [],
  competitor_brands: [],
  digest_frequency: 'daily',
  approval_required: false,
  active: true,
  created_at: now(),
  updated_at: null,
};

const FIXTURE_DIGEST = {
  id: 'e2e-digest-0001',
  run_id: 'e2e-run-0001',
  brand_id: 'e2e-brand-0001',
  brand_name: 'Acme Mobile',
  lead_count: 1,
  summary: { total_leads: 1, hot_count: 1, warm_count: 0, watch_count: 0, top_categories: ['telecom_mobile'], top_geographies: ['US-TX'] },
  status: 'delivered',
  output_path: 'output/digests/acme_mobile.csv',
  generated_at: now(),
  delivered_at: now(),
  error_message: null,
};

const FIXTURE_RUN = {
  id: 'e2e-run-0001',
  started_at: now(),
  completed_at: now(),
  signals_harvested: 2,
  signals_classified: 2,
  signals_scored: 2,
  leads_curated: 1,
  digests_generated: 1,
  digests_delivered: 1,
  status: 'completed',
  error_message: null,
};

let state = {};

function resetState() {
  state = {
    signals: FIXTURE_SIGNALS.map((s) => ({ ...s })),
    brands: [{ ...FIXTURE_BRAND }],
    digests: [{ ...FIXTURE_DIGEST }],
    runs: [{ ...FIXTURE_RUN }],
  };
}
resetState();

function send(res, status, body) {
  const text = JSON.stringify(body);
  res.writeHead(status, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(text) });
  res.end(text);
}

function readBody(req) {
  return new Promise((resolve) => {
    let data = '';
    req.on('data', (chunk) => (data += chunk));
    req.on('end', () => {
      try {
        resolve(data ? JSON.parse(data) : {});
      } catch {
        resolve({});
      }
    });
  });
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const path = url.pathname;
  const method = req.method;

  if (path === '/health') return send(res, 200, { status: 'ok', service: 'signalharvest-ai-mock' });

  if (path === '/e2e/reset' && method === 'POST') {
    resetState();
    return send(res, 200, { reset: true });
  }

  if (path === '/api/v1/pipeline/runs' && method === 'GET') {
    return send(res, 200, { runs: state.runs });
  }

  const runMatch = path.match(/^\/api\/v1\/pipeline\/runs\/([^/]+)$/);
  if (runMatch && method === 'GET') {
    const run = state.runs.find((r) => r.id === runMatch[1]);
    if (!run) return send(res, 404, { detail: 'not found' });
    return send(res, 200, run);
  }

  const runStateMatch = path.match(/^\/api\/v1\/pipeline\/runs\/([^/]+)\/state$/);
  if (runStateMatch && method === 'GET') {
    const run = state.runs.find((r) => r.id === runStateMatch[1]);
    if (!run) return send(res, 404, { detail: 'not found' });
    return send(res, 200, {
      run_id: run.id,
      signals_harvested: run.signals_harvested,
      signals_classified: run.signals_classified,
      signals_scored: run.signals_scored,
      leads_curated: run.leads_curated,
      digests_generated: run.digests_generated,
      digests_delivered: run.digests_delivered,
      last_completed_stage: 'publisher',
      error: null,
    });
  }

  if (path === '/api/v1/pipeline/run' && method === 'POST') {
    const newRun = { ...FIXTURE_RUN, id: 'e2e-run-triggered', started_at: now() };
    state.runs = [newRun, ...state.runs];
    return send(res, 200, { run_id: newRun.id, status: 'started' });
  }

  if (path === '/api/v1/signals' && method === 'GET') {
    let signals = state.signals;
    const source = url.searchParams.get('source');
    const tier = url.searchParams.get('tier');
    if (source) signals = signals.filter((s) => s.source === source);
    if (tier) signals = signals.filter((s) => s.tier === tier);
    return send(res, 200, { signals, count: signals.length });
  }

  if (path === '/api/v1/brands' && method === 'GET') {
    return send(res, 200, { brands: state.brands, count: state.brands.length });
  }

  if (path === '/api/v1/brands' && method === 'POST') {
    const body = await readBody(req);
    const brand = {
      id: `e2e-brand-${state.brands.length + 1}`,
      name: body.name,
      contact_email: body.contact_email,
      categories: body.categories || [],
      geographies: body.geographies || [],
      min_tier: body.min_tier || 'watch',
      keywords_include: body.keywords_include || [],
      keywords_exclude: body.keywords_exclude || [],
      competitor_brands: body.competitor_brands || [],
      digest_frequency: body.digest_frequency || 'daily',
      approval_required: body.approval_required || false,
      active: true,
      created_at: now(),
      updated_at: null,
    };
    state.brands = [...state.brands, brand];
    return send(res, 200, brand);
  }

  const brandMatch = path.match(/^\/api\/v1\/brands\/([^/]+)$/);
  if (brandMatch && method === 'PATCH') {
    const body = await readBody(req);
    const idx = state.brands.findIndex((b) => b.id === brandMatch[1]);
    if (idx === -1) return send(res, 404, { detail: 'not found' });
    state.brands[idx] = { ...state.brands[idx], ...body, updated_at: now() };
    return send(res, 200, state.brands[idx]);
  }
  if (brandMatch && method === 'DELETE') {
    const before = state.brands.length;
    state.brands = state.brands.filter((b) => b.id !== brandMatch[1]);
    if (state.brands.length === before) return send(res, 404, { detail: 'not found' });
    return send(res, 200, { deleted: true, brand_id: brandMatch[1] });
  }

  if (path === '/api/v1/digests' && method === 'GET') {
    return send(res, 200, { digests: state.digests, count: state.digests.length });
  }

  const digestMatch = path.match(/^\/api\/v1\/digests\/([^/]+)$/);
  if (digestMatch && method === 'GET') {
    const digest = state.digests.find((d) => d.id === digestMatch[1]);
    if (!digest) return send(res, 404, { detail: 'not found' });
    return send(res, 200, { ...digest, leads: [{ ...FIXTURE_SIGNALS[0], brand_id: digest.brand_id, match_reason: 'High-intent churn signal — Acme Mobile can intercept before the switch.', curated_at: now() }] });
  }

  const downloadMatch = path.match(/^\/api\/v1\/digests\/([^/]+)\/download$/);
  if (downloadMatch && method === 'GET') {
    const csv = 'score,tier,category,text\n82,hot,telecom_mobile,"Switching carriers today"\n';
    res.writeHead(200, {
      'Content-Type': 'text/csv',
      'Content-Disposition': `attachment; filename="digest_${downloadMatch[1]}.csv"`,
    });
    return res.end(csv);
  }

  send(res, 404, { detail: 'not found' });
});

server.listen(PORT, () => {
  console.log(`mock signalharvest backend on :${PORT}`);
});
