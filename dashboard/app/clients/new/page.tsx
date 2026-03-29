'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/api';

export default function NewClientPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSaving(true);
    setError('');
    const form = new FormData(e.currentTarget);
    try {
      await createClient({
        name: form.get('name') as string,
        email: form.get('email') as string,
        company_name: (form.get('company_name') as string) || undefined,
        billing_plan: (form.get('billing_plan') as string) || 'basic',
        notes: (form.get('notes') as string) || undefined,
      });
      router.push('/clients');
    } catch {
      setError('Error al crear el cliente. Verifica los datos e intenta de nuevo.');
      setSaving(false);
    }
  }

  return (
    <div className="max-w-md">
      <button onClick={() => router.back()} className="text-sm text-gray-500 hover:underline mb-4 block">
        ← Volver
      </button>

      <h1 className="text-2xl font-bold mb-6">Nuevo Cliente</h1>

      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-lg p-6 space-y-5">
        {[
          { label: 'Nombre *', name: 'name', type: 'text', required: true },
          { label: 'Email *', name: 'email', type: 'email', required: true },
          { label: 'Empresa', name: 'company_name', type: 'text', required: false },
        ].map(({ label, name, type, required }) => (
          <div key={name}>
            <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
            <input
              name={name}
              type={type}
              required={required}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            />
          </div>
        ))}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Plan</label>
          <select
            name="billing_plan"
            defaultValue="basic"
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          >
            <option value="basic">Basic</option>
            <option value="pro">Pro</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Notas</label>
          <textarea
            name="notes"
            rows={3}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
          />
        </div>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        <button
          type="submit"
          disabled={saving}
          className="w-full bg-indigo-600 text-white py-2 rounded text-sm font-medium disabled:opacity-50 hover:bg-indigo-700"
        >
          {saving ? 'Creando…' : 'Crear cliente'}
        </button>
      </form>
    </div>
  );
}
