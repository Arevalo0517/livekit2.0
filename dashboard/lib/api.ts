// ─── Types ────────────────────────────────────────────────────
export interface Client {
  id: string;
  name: string;
  company_name: string | null;
  email: string;
  status: string;
  billing_plan: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Agent {
  id: string;
  client_id: string;
  name: string;
  twilio_phone_number: string | null;
  system_prompt: string;
  voice_id: string;
  language: string;
  status: string;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Call {
  id: string;
  agent_id: string;
  caller_number: string | null;
  twilio_call_sid: string | null;
  livekit_room_name: string | null;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
  status: string;
  transcript: string | null;
  recording_url: string | null;
}

export interface CallList {
  items: Call[];
  total: number;
  page: number;
  limit: number;
}

// ─── Fetch helpers (call from Client Components) ──────────────
const base = '/api/proxy';

export async function fetchCalls(params: {
  page?: number;
  limit?: number;
  status?: string;
  agent_id?: string;
} = {}): Promise<CallList> {
  const qs = new URLSearchParams();
  if (params.page) qs.set('page', String(params.page));
  if (params.limit) qs.set('limit', String(params.limit));
  if (params.status) qs.set('status', params.status);
  if (params.agent_id) qs.set('agent_id', params.agent_id);
  const res = await fetch(`${base}/admin/calls?${qs}`);
  if (!res.ok) throw new Error(`fetchCalls failed: ${res.status}`);
  return res.json();
}

export async function fetchCall(id: string): Promise<Call> {
  const res = await fetch(`${base}/admin/calls/${id}`);
  if (!res.ok) throw new Error(`fetchCall failed: ${res.status}`);
  return res.json();
}

export async function fetchAgents(params: { status?: string } = {}): Promise<Agent[]> {
  const qs = new URLSearchParams();
  if (params.status) qs.set('status', params.status);
  const res = await fetch(`${base}/admin/agents?${qs}`);
  if (!res.ok) throw new Error(`fetchAgents failed: ${res.status}`);
  return res.json();
}

export async function fetchAgent(id: string): Promise<Agent> {
  const res = await fetch(`${base}/admin/agents/${id}`);
  if (!res.ok) throw new Error(`fetchAgent failed: ${res.status}`);
  return res.json();
}

export async function updateAgent(
  id: string,
  data: Partial<Pick<Agent, 'name' | 'system_prompt' | 'voice_id' | 'language' | 'status' | 'twilio_phone_number'>>,
): Promise<Agent> {
  const res = await fetch(`${base}/admin/agents/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`updateAgent failed: ${res.status}`);
  return res.json();
}

export async function fetchClients(params: { status?: string } = {}): Promise<Client[]> {
  const qs = new URLSearchParams();
  if (params.status) qs.set('status', params.status);
  const res = await fetch(`${base}/admin/clients?${qs}`);
  if (!res.ok) throw new Error(`fetchClients failed: ${res.status}`);
  return res.json();
}

export async function createClient(data: {
  name: string;
  email: string;
  company_name?: string;
  billing_plan?: string;
  notes?: string;
}): Promise<Client> {
  const res = await fetch(`${base}/admin/clients`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`createClient failed: ${res.status}`);
  return res.json();
}
