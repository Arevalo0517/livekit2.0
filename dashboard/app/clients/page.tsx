'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchClients, type Client } from '@/lib/api';

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);

  useEffect(() => {
    fetchClients()
      .then(setClients)
      .catch(() => setFetchError(true))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Clientes</h1>
        <Link
          href="/clients/new"
          className="bg-indigo-600 text-white px-4 py-2 rounded text-sm font-medium hover:bg-indigo-700"
        >
          + Nuevo cliente
        </Link>
      </div>

      {loading && <p className="text-gray-400">Cargando…</p>}
      {fetchError && <p className="text-red-500">Error al cargar los clientes.</p>}

      <div className="grid gap-4">
        {clients.map((client) => (
          <div
            key={client.id}
            className="bg-white border border-gray-200 rounded-lg p-5"
          >
            <div className="flex justify-between items-start">
              <div>
                <p className="font-semibold">{client.name}</p>
                {client.company_name && (
                  <p className="text-sm text-gray-500">{client.company_name}</p>
                )}
                <p className="text-sm text-gray-500 mt-0.5">{client.email}</p>
              </div>
              <span
                className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                  client.status === 'active'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                {client.status}
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-2 font-mono">ID: {client.id}</p>
          </div>
        ))}
        {!loading && !fetchError && clients.length === 0 && (
          <p className="text-gray-400">No hay clientes todavía.</p>
        )}
      </div>
    </div>
  );
}
