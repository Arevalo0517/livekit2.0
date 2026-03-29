'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const links = [
  { href: '/calls', label: '📞 Llamadas' },
  { href: '/agents', label: '🤖 Agentes' },
  { href: '/clients', label: '👥 Clientes' },
];

export default function Nav() {
  const pathname = usePathname();
  return (
    <aside className="w-52 min-h-screen bg-gray-900 text-white flex flex-col py-6 px-4 gap-1 shrink-0">
      <p className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-4 px-2">
        BajaCall Admin
      </p>
      {links.map(({ href, label }) => (
        <Link
          key={href}
          href={href}
          className={`rounded px-3 py-2 text-sm font-medium transition-colors ${
            pathname.startsWith(href)
              ? 'bg-indigo-600 text-white'
              : 'text-gray-300 hover:bg-gray-800'
          }`}
        >
          {label}
        </Link>
      ))}
    </aside>
  );
}
