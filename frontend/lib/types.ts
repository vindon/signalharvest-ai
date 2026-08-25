export type SignalSource = 'reddit' | 'google_trends' | 'cfpb' | 'rss';

export type IntentType =
  | 'complaint'
  | 'comparison'
  | 'purchase_ready'
  | 'churn_risk'
  | 'information'
  | 'unknown';

export type SignalTier = 'hot' | 'warm' | 'watch';

export type SignalCategory = string; // 40-value taxonomy — kept open-ended, not hand-duplicated

export interface ScoredSignal {
  id: string;
  source: SignalSource;
  source_id: string;
  url: string | null;
  title: string | null;
  text: string;
  author: string | null;
  geography: string | null;
  harvested_at: string;
  source_created_at: string | null;
  raw_metadata: Record<string, unknown>;
  category: SignalCategory;
  intent_type: IntentType;
  classification_confidence: number;
  keywords: string[];
  competitor_mentions: string[];
  classified_at: string | null;
  score: number;
  tier: SignalTier;
  velocity_delta_24h: number;
  velocity_delta_7d: number;
  engagement_score: number;
  scored_at: string | null;
}

export interface CuratedLead extends ScoredSignal {
  brand_id: string;
  match_reason: string;
  curated_at: string | null;
}

export interface BrandSubscription {
  id: string;
  name: string;
  contact_email: string;
  categories: SignalCategory[];
  geographies: string[];
  min_tier: SignalTier;
  keywords_include: string[];
  keywords_exclude: string[];
  competitor_brands: string[];
  digest_frequency: 'daily' | 'weekly';
  approval_required: boolean;
  active: boolean;
  created_at: string;
  updated_at: string | null;
}

export type DigestStatus = 'pending' | 'approved' | 'delivered' | 'failed' | 'skipped';

export interface DigestSummary {
  total_leads: number;
  hot_count: number;
  warm_count: number;
  watch_count: number;
  top_categories: string[];
  top_geographies: string[];
}

export interface Digest {
  id: string;
  run_id: string;
  brand_id: string;
  brand_name: string;
  lead_count: number;
  summary: DigestSummary;
  status: DigestStatus;
  output_path: string | null;
  generated_at: string;
  delivered_at: string | null;
  error_message: string | null;
}

export interface DigestDetail extends Digest {
  leads: CuratedLead[];
}

export type PipelineRunStatus = 'running' | 'completed' | 'failed';

export interface PipelineRun {
  id: string;
  started_at: string;
  completed_at: string | null;
  signals_harvested: number;
  signals_classified: number;
  signals_scored: number;
  leads_curated: number;
  digests_generated: number;
  digests_delivered: number;
  status: PipelineRunStatus;
  error_message: string | null;
}

export interface SignalsResponse {
  signals: ScoredSignal[];
  count: number;
}

export interface BrandsResponse {
  brands: BrandSubscription[];
  count: number;
}

export interface DigestsResponse {
  digests: Digest[];
  count: number;
}

export interface RunsResponse {
  runs: PipelineRun[];
}

export interface PipelineRunState {
  run_id: string;
  signals_harvested: number;
  signals_classified: number;
  signals_scored: number;
  leads_curated: number;
  digests_generated: number;
  digests_delivered: number;
  last_completed_stage: string | null;
  error: string | null;
}

export interface TriggerRunResponse {
  run_id: string;
  status: 'started';
}
