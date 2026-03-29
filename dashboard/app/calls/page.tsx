import CallsTable from '@/components/calls-table';

export const dynamic = 'force-dynamic';

export default function CallsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Llamadas</h1>
      <CallsTable />
    </div>
  );
}
