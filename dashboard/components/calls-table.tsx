'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { fetchCalls, type Call, type CallList } from '@/lib/api';

const STATUS_COLORS: Record<string, string> = {
  completed: 'bg-green-100 text-green-800',
  in_progress: 'bg-blue-100 text-blue-800',
  pending: 'bg-yellow-100 text-yellow-800',
  failed: 'bg-red-100 text-red-800',
  abandoned: 'bg-gray-100 text-gray-600',
};

function fmt(iso: string) {
  return new Date(iso).toLocaleString('es-MX', {
    dateStyle: 'short',
    timeStyle: 'short',
  });
}

function duration(secs: number | null) {
  if (secs === null) return '—';
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

export default function CallsTable() {
  const [data, setData] = useState<CallList | null>(null);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const limit = 20;

  useEffect(() => {
    setLoading(true);
    fetchCalls({ page, limit, status: statusFilter || undefined })
      .then(setData)
      .finally(() => setLoading(false));
  }, [page, statusFilter]);

  const totalPages = data ? Math.ceil(data.total / limit) : 1;

  return (
    <div>
      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        >
          <option value="">Todos los estados</option>
          <option value="completed">Completada</option>
          <option value="in_progress">En curso</option>
          <option value="pending">Pendiente</option>
          <option value="failed">Fallida</option>
          <option value="abandoned">Abandonada</option>
        </select>
        {data && (
          <span className="text-sm text-gray-500 self-center">
            {data.total} llamada{data.total !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
            <tr>
              <th className="px-4 py-3 text-left">Inicio</th>
              <th className="px-4 py-3 text-left">Número</th>
              <th className="px-4 py-3 text-left">Duración</th>
              <th className="px-4 py-3 text-left">Estado</th>
              <th className="px-4 py-3 text-left">Transcripción</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                  Cargando…
                </td>
              </tr>
            )}
            {!loading && data?.items.map((call: Call) => (
              <tr key={call.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 whitespace-nowrap">{fmt(call.started_at)}</td>
                <td className="px-4 py-3 font-mono text-xs">{call.caller_number ?? '—'}</td>
                <td className="px-4 py-3">{duration(call.duration_seconds)}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[call.status] ?? 'bg-gray-100'}`}>
                    {call.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500 max-w-xs truncate">
                  {call.transcript ? call.transcript.slice(0, 80) + '…' : '—'}
                </td>
                <td className="px-4 py-3 text-right">
                  <Link href={`/calls/${call.id}`} className="text-indigo-600 hover:underline text-xs">
                    Ver →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 text-sm border rounded disabled:opacity-40"
          >
            ← Anterior
          </button>
          <span className="text-sm text-gray-500">
            Página {page} de {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1.5 text-sm border rounded disabled:opacity-40"
          >
            Siguiente →
          </button>
        </div>
      )}
    </div>
  );
}
