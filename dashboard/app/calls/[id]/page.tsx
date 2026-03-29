'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { fetchCall, type Call } from '@/lib/api';
import TranscriptViewer from '@/components/transcript-viewer';

function fmt(iso: string) {
  return new Date(iso).toLocaleString('es-MX', {
    dateStyle: 'medium',
    timeStyle: 'medium',
  });
}

function duration(secs: number | null) {
  if (secs === null) return '—';
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m}m ${s}s`;
}

export default function CallDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [call, setCall] = useState<Call | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchCall(id)
      .then(setCall)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-gray-400">Cargando…</p>;
  if (error) return <p className="text-red-500">Error al cargar la llamada.</p>;
  if (!call) return <p className="text-red-500">Llamada no encontrada</p>;

  return (
    <div className="max-w-3xl">
      <button onClick={() => router.back()} className="text-sm text-gray-500 hover:underline mb-4 block">
        ← Volver
      </button>

      <h1 className="text-2xl font-bold mb-6">Detalle de llamada</h1>

      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6 grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-gray-500 text-xs uppercase font-semibold mb-1">Número</p>
          <p className="font-mono">{call.caller_number ?? '—'}</p>
        </div>
        <div>
          <p className="text-gray-500 text-xs uppercase font-semibold mb-1">Estado</p>
          <p>{call.status}</p>
        </div>
        <div>
          <p className="text-gray-500 text-xs uppercase font-semibold mb-1">Inicio</p>
          <p>{fmt(call.started_at)}</p>
        </div>
        <div>
          <p className="text-gray-500 text-xs uppercase font-semibold mb-1">Duración</p>
          <p>{duration(call.duration_seconds)}</p>
        </div>
        <div>
          <p className="text-gray-500 text-xs uppercase font-semibold mb-1">SID Twilio</p>
          <p className="font-mono text-xs break-all">{call.twilio_call_sid ?? '—'}</p>
        </div>
        <div>
          <p className="text-gray-500 text-xs uppercase font-semibold mb-1">Sala LiveKit</p>
          <p className="font-mono text-xs break-all">{call.livekit_room_name ?? '—'}</p>
        </div>
      </div>

      <h2 className="text-lg font-semibold mb-4">Transcripción</h2>
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <TranscriptViewer transcript={call.transcript ?? ''} />
      </div>
    </div>
  );
}
