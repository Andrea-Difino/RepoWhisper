import { useState } from 'react';
import { Check, List, Search } from 'lucide-react';
import type { ModuleNavItem } from '../types';

interface ModuleIndexProps {
  items: ModuleNavItem[];
  currentIndex: number;
  onSelect: (index: number) => void;
}

export default function ModuleIndex({ items, currentIndex, onSelect }: ModuleIndexProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const filteredItems = items.filter((item) =>
    `${item.title} ${item.path}`.toLowerCase().includes(query.trim().toLowerCase())
  );
  const completedCount = items.filter((item) => item.index > 0 && item.studied).length;

  const handleSelect = (index: number) => {
    onSelect(index);
    setIsOpen(false);
    setQuery('');
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        aria-expanded={isOpen}
        aria-controls="module-index"
        className="inline-flex h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 shadow-sm transition hover:border-slate-300 hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
      >
        <List className="h-4 w-4" />
        <span>Indice</span>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
          {completedCount}/{items.length - 1}
        </span>
      </button>

      {isOpen && (
        <div
          id="module-index"
          role="dialog"
          aria-label="Indice delle schede"
          onKeyDown={(event) => {
            if (event.key === 'Escape') {
              setIsOpen(false);
            }
          }}
          className="absolute right-0 top-full z-50 mt-2 w-[min(90vw,24rem)] overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-2xl shadow-slate-900/15"
        >
          <div className="border-b border-slate-100 p-3">
            <label className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2.5 text-slate-400 focus-within:ring-2 focus-within:ring-indigo-500/30">
              <Search className="h-4 w-4 shrink-0" />
              <input
                autoFocus
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Cerca una scheda o un file..."
                className="min-w-0 flex-1 bg-transparent text-sm text-slate-800 outline-none placeholder:text-slate-400"
              />
            </label>
            <p className="px-1 pt-2 text-xs text-slate-500">
              {completedCount} di {items.length - 1} schede completate
            </p>
          </div>

          <ul className="max-h-[min(60vh,24rem)] overflow-y-auto p-2">
            {filteredItems.length > 0 ? filteredItems.map((item) => {
              const isCurrent = item.index === currentIndex;
              return (
                <li key={item.index}>
                  <button
                    type="button"
                    onClick={() => handleSelect(item.index)}
                    aria-current={isCurrent ? 'step' : undefined}
                    className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition ${
                      isCurrent
                        ? 'bg-indigo-50 text-indigo-950'
                        : 'text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                      item.studied
                        ? 'bg-emerald-100 text-emerald-700'
                        : isCurrent
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-100 text-slate-500'
                    }`}>
                      {item.studied ? <Check className="h-4 w-4" /> : item.index === 0 ? 'i' : item.index}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-medium">
                        {item.title}
                      </span>
                      <span className="block truncate text-xs text-slate-500">
                        {item.path}
                      </span>
                    </span>
                    {isCurrent && <span className="text-xs font-medium text-indigo-600">Ora</span>}
                  </button>
                </li>
              );
            }) : (
              <li className="px-3 py-8 text-center text-sm text-slate-500">
                Nessuna scheda corrisponde alla ricerca.
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
