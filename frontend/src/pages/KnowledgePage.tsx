import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { PageContainer } from '../components/PageContainer';
import { Button } from '../components/Button';
import { Icon } from '../components/Icon';
import { EmptyState } from '../components/EmptyState';
import { LoadingState } from '../components/LoadingState';
import { OriginTag } from '../components/StatusBadge';
import { AppRoute, KnowledgeSource, StructureKnowledgeRecord } from '../types';
import { fetchSources, fetchStructures } from '../services/api';

export interface KnowledgePageProps {
  onRouteChange: (route: AppRoute) => void;
}

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; structures: StructureKnowledgeRecord[]; sources: Map<string, KnowledgeSource>; sourcesError?: string };

const ListBlock: React.FC<{ title: string; items?: string[] }> = ({ title, items }) =>
  items && items.length > 0 ? (
    <section className="border-t border-ink-900/15 pt-5">
      <h3 className="text-sm font-semibold text-ink-900">{title}</h3>
      <ul className="mt-3 space-y-2.5">
        {items.map((item) => (
          <li key={item} className="flex gap-3 text-sm leading-relaxed text-ink-700">
            <span className="mt-[10px] h-px w-3 shrink-0 bg-ink-500" aria-hidden="true" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </section>
  ) : null;

const StructureDetail: React.FC<{ record: StructureKnowledgeRecord; sources: Map<string, KnowledgeSource> }> = ({
  record,
  sources,
}) => (
  <article aria-labelledby={`typology-${record.id}`}>
    <header className="pb-8">
      <div className="flex flex-wrap items-center gap-3">
        <OriginTag kind="knowledge" />
        {record.sources && record.sources.length > 0 && (
          <span className="font-mono text-[0.6875rem] text-ink-500 tabular-nums">
            {record.sources.length} cited source{record.sources.length === 1 ? '' : 's'}
          </span>
        )}
      </div>
      <h2 id={`typology-${record.id}`} className="mt-5 font-display text-display-lg font-medium text-ink-900">
        {record.name}
      </h2>
      {record.alternate_names && record.alternate_names.length > 0 && (
        <p className="mt-3 text-sm text-ink-600">Also: {record.alternate_names.join(', ')}</p>
      )}
      {record.regions && record.regions.length > 0 && (
        <p className="mt-1 text-sm text-ink-600">Regions: {record.regions.join(' · ')}</p>
      )}
    </header>

    <div className="space-y-10">
      <ListBlock title="Traditional function" items={record.traditional_function} />

      {record.engineering_principles && record.engineering_principles.length > 0 && (
        <section className="border-t border-ink-900/15 pt-5">
          <h3 className="text-sm font-semibold text-ink-900">Engineering principles</h3>
          <div className="mt-4 space-y-8">
            {record.engineering_principles.map((p, i) => (
              <div key={p.principle} className="grid gap-3 md:grid-cols-[2.5rem_minmax(0,1fr)]">
                <span className="font-mono text-xs text-laterite-500 tabular-nums">{String(i + 1).padStart(2, '0')}</span>
                <div>
                  <h4 className="font-display text-2xl font-medium leading-tight text-ink-900">{p.principle}</h4>
                  <dl className="mt-3 grid gap-x-5 gap-y-2 text-sm sm:grid-cols-[6rem_minmax(0,1fr)]">
                    {(
                      [
                        ['What', p.what],
                        ['Why', p.why],
                        ['How', p.how],
                        ['Significance', p.engineering_significance],
                      ] as const
                    ).map(([label, text]) =>
                      text ? (
                        <React.Fragment key={label}>
                          <dt className="text-xs text-ink-500 sm:pt-0.5">{label}</dt>
                          <dd className="leading-relaxed text-ink-700">{text}</dd>
                        </React.Fragment>
                      ) : null,
                    )}
                  </dl>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {record.water_management_principles && record.water_management_principles.length > 0 && (
        <section className="border-t border-ink-900/15 pt-5">
          <h3 className="text-sm font-semibold text-ink-900">Water management</h3>
          <div className="mt-4 grid gap-6 md:grid-cols-2">
            {record.water_management_principles.map((p) => (
              <div key={p.principle}>
                <h4 className="text-sm font-medium text-ink-900">{p.principle}</h4>
                {p.description && <p className="mt-1.5 text-sm leading-relaxed text-ink-700">{p.description}</p>}
                {p.hydrological_mechanism && (
                  <p className="mt-1.5 text-sm leading-relaxed text-ink-600">{p.hydrological_mechanism}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {record.traditional_materials && record.traditional_materials.length > 0 && (
        <section className="border-t border-ink-900/15 pt-5">
          <h3 className="text-sm font-semibold text-ink-900">Traditional materials</h3>
          <dl className="mt-4 divide-y divide-ink-900/10">
            {record.traditional_materials.map((m) => (
              <div key={m.material_family} className="grid gap-2 py-3 md:grid-cols-[12rem_minmax(0,1fr)] md:gap-6">
                <dt className="text-sm font-medium text-ink-900">{m.material_family}</dt>
                <dd className="text-sm leading-relaxed text-ink-700">
                  {m.usage}
                  {m.traditional_role && <span className="mt-1 block text-ink-600">{m.traditional_role}</span>}
                </dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      <div className="grid gap-10 lg:grid-cols-2">
        <ListBlock title="Construction features" items={record.construction_features} />
        <ListBlock title="Environmental adaptations" items={record.environmental_adaptations} />
        <ListBlock title="Common deterioration" items={record.common_deterioration_factors} />
        <ListBlock title="Conservation considerations" items={record.conservation_considerations} />
      </div>

      {record.limitations && record.limitations.length > 0 && (
        <section className="rounded-sm border border-ochre-500/30 bg-ochre-100/40 p-5">
          <h3 className="text-sm font-semibold text-ink-900">Limitations of this record</h3>
          <ul className="mt-2 space-y-1.5 text-sm leading-relaxed text-ink-700">
            {record.limitations.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        </section>
      )}

      {record.sources && record.sources.length > 0 && (
        <section className="border-t border-ink-900/15 pt-5">
          <h3 className="text-sm font-semibold text-ink-900">Sources</h3>
          <ol className="mt-3 space-y-4">
            {record.sources.map((id) => {
              const source = sources.get(id);
              return (
                <li key={id} className="text-sm leading-relaxed">
                  {source ? (
                    <>
                      <p className="text-ink-900">
                        {source.url ? (
                          <a
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-baseline gap-1 underline decoration-ink-900/30 underline-offset-4 hover:decoration-ink-900"
                          >
                            {source.title}
                            <Icon name="external" className="h-3 w-3 self-center" />
                            <span className="sr-only">(opens in a new tab)</span>
                          </a>
                        ) : (
                          source.title
                        )}
                      </p>
                      <p className="text-xs text-ink-500">
                        {[source.publisher, source.year].filter(Boolean).join(', ')}
                        {source.topic ? ` — ${source.topic}` : ''}
                      </p>
                    </>
                  ) : (
                    <p className="font-mono text-xs text-ink-500">{id} (details unavailable)</p>
                  )}
                </li>
              );
            })}
          </ol>
        </section>
      )}
    </div>
  </article>
);

export const KnowledgePage: React.FC<KnowledgePageProps> = ({ onRouteChange }) => {
  const [state, setState] = useState<LoadState>({ status: 'loading' });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});

  const load = useCallback(async () => {
    setState({ status: 'loading' });
    try {
      const [structures, sourcesResult] = await Promise.all([
        fetchStructures(),
        fetchSources().then(
          (list) => ({ list, error: undefined as string | undefined }),
          (error: unknown) => ({ list: [] as KnowledgeSource[], error: error instanceof Error ? error.message : 'Unavailable' }),
        ),
      ]);
      setState({
        status: 'ready',
        structures,
        sources: new Map(sourcesResult.list.map((s) => [s.source_id, s])),
        sourcesError: sourcesResult.error,
      });
      setSelectedId((current) => current ?? structures[0]?.id ?? null);
    } catch (error) {
      setState({ status: 'error', message: error instanceof Error ? error.message : 'Unknown error' });
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const structures = state.status === 'ready' ? state.structures : [];
  const selected = useMemo(() => structures.find((s) => s.id === selectedId) ?? structures[0], [structures, selectedId]);

  const handleTabKey = (event: React.KeyboardEvent, index: number) => {
    const delta = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1 }[event.key];
    if (!delta) return;
    event.preventDefault();
    const next = structures[(index + delta + structures.length) % structures.length];
    setSelectedId(next.id);
    tabRefs.current[next.id]?.focus();
  };

  return (
    <PageContainer
      eyebrow="JalDrishti / Knowledge"
      title="Knowledge rooted in place and practice"
      subtitle="Documented records of traditional Indian water structures — how they were built, why they work, and how they decay — with the sources each record cites."
      plate="tank-mist"
      treatment="panel"
      ground="dark"
      actions={
        <Button variant="secondary" onClick={() => onRouteChange('/upload')}>
          Start an inspection
        </Button>
      }
    >
      {state.status === 'loading' && <LoadingState label="Loading records from the knowledge service" className="max-w-md" />}

      {state.status === 'error' && (
        <EmptyState
          title="Knowledge service unreachable"
          description={<p>{state.message}</p>}
          actions={
            <Button onClick={() => void load()} icon={<Icon name="refresh" className="h-4 w-4" />}>
              Try again
            </Button>
          }
        />
      )}

      {state.status === 'ready' && structures.length === 0 && (
        <EmptyState title="No records" description="The knowledge service returned no structure records." />
      )}

      {state.status === 'ready' && selected && (
        <div className="grid gap-10 lg:grid-cols-[14rem_minmax(0,1fr)] lg:gap-16">
          <div className="min-w-0 lg:sticky lg:top-24 lg:self-start">
            <p className="eyebrow mb-3 text-ink-500" id="typology-tabs-label">
              Typologies
            </p>
            <div
              role="tablist"
              aria-labelledby="typology-tabs-label"
              aria-orientation="vertical"
              className="-mx-[var(--gutter)] flex gap-1 overflow-x-auto px-[var(--gutter)] lg:mx-0 lg:flex-col lg:overflow-visible lg:px-0"
            >
              {structures.map((s, i) => {
                const active = s.id === selected.id;
                return (
                  <button
                    key={s.id}
                    ref={(el) => (tabRefs.current[s.id] = el)}
                    role="tab"
                    id={`tab-${s.id}`}
                    aria-selected={active}
                    aria-controls="typology-panel"
                    tabIndex={active ? 0 : -1}
                    onClick={() => setSelectedId(s.id)}
                    onKeyDown={(event) => handleTabKey(event, i)}
                    className={`flex shrink-0 items-baseline gap-3 whitespace-nowrap rounded-lg px-3 py-2.5 text-left transition-colors duration-fast lg:rounded-none lg:border-l-2 ${
                      active
                        ? 'bg-ws-stone text-ws-text lg:border-ws-moss-deep lg:bg-transparent lg:text-ink-900'
                        : 'text-ink-600 hover:text-ink-900 lg:border-ink-900/10'
                    }`}
                  >
                    <span className="font-mono text-[0.625rem] tabular-nums opacity-70">{String(i + 1).padStart(2, '0')}</span>
                    <span className="font-display text-xl font-medium">{s.name}</span>
                  </button>
                );
              })}
            </div>
            {state.sourcesError && (
              <p className="mt-4 text-xs text-ochre-700">Source details could not be loaded: {state.sourcesError}</p>
            )}
          </div>

          <div id="typology-panel" role="tabpanel" aria-labelledby={`tab-${selected.id}`} tabIndex={0} className="min-w-0 max-w-[48rem] focus:outline-none">
            <StructureDetail record={selected} sources={state.sources} />
          </div>
        </div>
      )}
    </PageContainer>
  );
};

export default KnowledgePage;
