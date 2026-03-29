'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchAgents, type Agent } from '@/lib/api';

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);

  useEffect(() => {
    fetchAgents()
      .then(setAgents)
      .catch(() => setFetchError(true))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Agentes</h1>

      {loading && <p className="text-gray-400">Cargando…</p>}
      {fetchError && <p className="text-red-500">Error al cargar los agentes.</p>}

      <div className="grid gap-4">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className="bg-white border border-gray-200 rounded-lg p-5 flex justify-between items-start"
          >
            <div>
              <p className="font-semibold">{agent.name}</p>
              <p className="text-sm text-gray-500 mt-0.5">
                {agent.twilio_phone_number ?? 'Sin número'} · voz: {agent.voice_id} · idioma: {agent.language}
              </p>
              <span
                className={`inline-block mt-2 px-2 py-0.5 rounded-full text-xs font-medium ${
                  agent.status === 'active'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                {agent.status}
              </span>
            </div>
            <Link
              href={`/agents/${agent.id}`}
              className="text-indigo-600 text-sm hover:underline shrink-0 ml-4"
            >
              Editar →
            </Link>
          </div>
        ))}
        {!loading && agents.length === 0 && (
          <p className="text-gray-400">No hay agentes todavía.</p>
        )}
      </div>
    </div>
  );
}
