'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { fetchAgent, updateAgent, type Agent } from '@/lib/api';

export default function AgentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAgent(id).then(setAgent);
  }, [id]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!agent) return;
    setSaving(true);
    setSaved(false);
    setError('');
    const form = new FormData(e.currentTarget);
    try {
      await updateAgent(id, {
        name: form.get('name') as string,
        system_prompt: form.get('system_prompt') as string,
        voice_id: form.get('voice_id') as string,
        language: form.get('language') as string,
        twilio_phone_number: (form.get('twilio_phone_number') as string) || undefined,
      });
      setSaved(true);
    } catch {
      setError('Error al guardar. Intenta de nuevo.');
    } finally {
      setSaving(false);
    }
  }

  if (!agent) return <p className="text-gray-400">Cargando…</p>;

  return (
    <div className="max-w-xl">
      <button onClick={() => router.back()} className="text-sm text-gray-500 hover:underline mb-4 block">
        ← Volver
      </button>

      <h1 className="text-2xl font-bold mb-6">Editar Agente</h1>

      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-lg p-6 space-y-5">
        {[
          { label: 'Nombre', name: 'name', defaultValue: agent.name },
          { label: 'Número Twilio', name: 'twilio_phone_number', defaultValue: agent.twilio_phone_number ?? '' },
          { label: 'Voz (voice_id)', name: 'voice_id', defaultValue: agent.voice_id },
          { label: 'Idioma', name: 'language', defaultValue: agent.language },
        ].map(({ label, name, defaultValue }) => (
          <div key={name}>
            <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
            <input
              name={name}
              defaultValue={defaultValue}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            />
          </div>
        ))}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">System Prompt</label>
          <textarea
            name="system_prompt"
            defaultValue={agent.system_prompt}
            rows={6}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono"
          />
        </div>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={saving}
            className="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-50 hover:bg-indigo-700"
          >
            {saving ? 'Guardando…' : 'Guardar cambios'}
          </button>
          {saved && <span className="text-green-600 text-sm">✓ Guardado</span>}
        </div>
      </form>
    </div>
  );
}
