import { useState, useMemo, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const API_BASE = '/api'

const COLORS = ['#6366f1', '#8b5cf6', '#a855f7', '#22c55e', '#eab308', '#f97316', '#ec4899']

export default function App() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [filtroTabla, setFiltroTabla] = useState('')
  const [filtroAccionable, setFiltroAccionable] = useState('')
  const [filtroOrderType, setFiltroOrderType] = useState('')
  const [filtroMilestone, setFiltroMilestone] = useState('')
  const [loadingLast, setLoadingLast] = useState(true)

  useEffect(() => {
    fetch(`${API_BASE}/process`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.stats && data?.tabla) setResult(data)
      })
      .catch(() => {})
      .finally(() => setLoadingLast(false))
  }, [])

  const handleUpload = async (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    setFile(f)
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      const form = new FormData()
      form.append('file', f)
      const res = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        body: form,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || 'Error al procesar')
      }
      const data = await res.json()
      setResult(data)
      setFiltroTabla('')
      setFiltroAccionable('')
      setFiltroOrderType('')
      setFiltroMilestone('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const chartData = useMemo(() => {
    if (!result?.stats?.distribucion_accionables) return []
    return Object.entries(result.stats.distribucion_accionables).map(([name, count]) => ({ name, count }))
  }, [result])

  const opcionesFiltros = useMemo(() => {
    if (!result?.tabla?.length) return { orderType: [], milestone: [], accionable: [] }
    const rows = result.tabla
    const orderType = [...new Set(rows.map((r) => String(r['order_type'] || '').trim()).filter(Boolean))].sort()
    const milestone = [...new Set(rows.map((r) => String(r['Logistics Milestone'] || '').trim()).filter(Boolean))].sort()
    const accionable = [...new Set(rows.map((r) => String(r['Accionables'] || '').trim()).filter(Boolean))].sort()
    return { orderType, milestone, accionable }
  }, [result])

  const tablaFiltrada = useMemo(() => {
    if (!result?.tabla) return []
    let rows = result.tabla
    if (filtroOrderType) {
      rows = rows.filter((r) => String(r['order_type'] || '').trim() === filtroOrderType)
    }
    if (filtroMilestone) {
      rows = rows.filter((r) => String(r['Logistics Milestone'] || '').trim() === filtroMilestone)
    }
    if (filtroAccionable) {
      rows = rows.filter((r) => String(r['Accionables'] || '').trim() === filtroAccionable)
    }
    if (filtroTabla.trim()) {
      const q = filtroTabla.toLowerCase()
      rows = rows.filter((r) =>
        Object.values(r).some((v) => String(v).toLowerCase().includes(q))
      )
    }
    return rows
  }, [result, filtroTabla, filtroAccionable, filtroOrderType, filtroMilestone])

  const hayFiltrosActivos = filtroTabla || filtroAccionable || filtroOrderType || filtroMilestone
  const limpiarFiltros = () => {
    setFiltroTabla('')
    setFiltroAccionable('')
    setFiltroOrderType('')
    setFiltroMilestone('')
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>Dashboard Accionables</h1>
        <p style={styles.subtitle}>
          Subí el archivo Excel &quot;Order Detail - Pending Orders First Mile...&quot; para ver estadísticas y accionables.
        </p>
      </header>

      <section style={styles.uploadSection}>
        <label style={styles.uploadZone}>
          <input
            type="file"
            accept=".xlsx,.xls"
            onChange={handleUpload}
            style={{ display: 'none' }}
            disabled={loading}
          />
          {loading ? (
            <span style={styles.uploadText}>Procesando...</span>
          ) : (
            <>
              <span style={styles.uploadIcon}>📁</span>
              <span style={styles.uploadText}>
                {file ? file.name : 'Arrastrá o elegí el archivo Excel'}
              </span>
            </>
          )}
        </label>
        {result && (
          <p style={styles.muted}>Podés subir un nuevo Excel para reemplazar los datos mostrados abajo.</p>
        )}
        {!loadingLast && !result && !loading && (
          <p style={styles.muted}>Para que el último archivo se guarde y lo vea quien entre, agregá <strong>Upstash Redis</strong> en el proyecto de Vercel (Marketplace → Redis).</p>
        )}
        {error && <p style={styles.error}>{error}</p>}
      </section>

      {result && (
        <>
          <section style={styles.cards}>
            <div style={styles.card}>
              <div style={styles.cardLabel}>Órdenes totales</div>
              <div style={styles.cardValue}>{result.stats.ordenes_totales}</div>
            </div>
            <div style={styles.card}>
              <div style={styles.cardLabel}>Con milestone válido</div>
              <div style={styles.cardValue}>{result.stats.ordenes_milestone_valido}</div>
            </div>
            <div style={styles.card}>
              <div style={styles.cardLabel}>Con accionables</div>
              <div style={{ ...styles.cardValue, color: 'var(--accent)' }}>
                {result.stats.ordenes_con_accionables}
              </div>
            </div>
            <div style={styles.card}>
              <div style={styles.cardLabel}>Fecha de análisis</div>
              <div style={styles.cardValueSmall}>{result.stats.fecha_analisis}</div>
            </div>
          </section>

          {chartData.length > 0 && (
            <section style={styles.chartSection}>
              <h2 style={styles.sectionTitle}>Distribución de accionables</h2>
              <div style={styles.chartWrap}>
                <ResponsiveContainer width="100%" height={360}>
                  <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 40 }}>
                    <XAxis type="number" stroke="var(--text-muted)" fontSize={12} />
                    <YAxis type="category" dataKey="name" width={220} stroke="var(--text-muted)" fontSize={11} tick={{ fill: 'var(--text)' }} />
                    <Tooltip
                      contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8 }}
                      labelStyle={{ color: 'var(--text)' }}
                      formatter={(value) => [value, 'Órdenes']}
                    />
                    <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                      {chartData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>
          )}

          <section style={styles.tableSection}>
            <h2 style={styles.sectionTitle}>Tabla de órdenes</h2>
            <div style={styles.filters}>
              <select
                value={filtroOrderType}
                onChange={(e) => setFiltroOrderType(e.target.value)}
                style={styles.select}
                title="Order type"
              >
                <option value="">Order type (todos)</option>
                {opcionesFiltros.orderType.map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
              <select
                value={filtroMilestone}
                onChange={(e) => setFiltroMilestone(e.target.value)}
                style={styles.select}
                title="Logistics Milestone"
              >
                <option value="">Logistics Milestone (todos)</option>
                {opcionesFiltros.milestone.map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
              <select
                value={filtroAccionable}
                onChange={(e) => setFiltroAccionable(e.target.value)}
                style={styles.select}
                title="Accionable"
              >
                <option value="">Accionable (todos)</option>
                {opcionesFiltros.accionable.map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
              <input
                type="text"
                placeholder="Buscar en toda la tabla..."
                value={filtroTabla}
                onChange={(e) => setFiltroTabla(e.target.value)}
                style={styles.input}
              />
              {hayFiltrosActivos && (
                <button type="button" onClick={limpiarFiltros} style={styles.btnLimpiar}>
                  Limpiar filtros
                </button>
              )}
            </div>
            {hayFiltrosActivos && (
              <p style={styles.muted}>Mostrando {tablaFiltrada.length} filas (filtros activos).</p>
            )}
            <div style={styles.tableWrap}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    {result.tabla?.length && Object.keys(result.tabla[0]).map((k) => (
                      <th key={k} style={styles.th}>{k}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tablaFiltrada.slice(0, 500).map((row, i) => (
                    <tr key={i} style={styles.tr}>
                      {Object.entries(row).map(([k, v]) => (
                        <td key={k} style={styles.td}>{String(v)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {tablaFiltrada.length > 500 && (
              <p style={styles.muted}>Mostrando 500 de {tablaFiltrada.length} filas. Usá los filtros para acotar.</p>
            )}
          </section>
        </>
      )}
    </div>
  )
}

const styles = {
  container: {
    maxWidth: 1200,
    margin: '0 auto',
    padding: '2rem 1.5rem',
  },
  header: {
    marginBottom: '2rem',
  },
  title: {
    fontSize: '1.75rem',
    fontWeight: 700,
    margin: 0,
    letterSpacing: '-0.02em',
  },
  subtitle: {
    color: 'var(--text-muted)',
    margin: '0.5rem 0 0',
    fontSize: '0.95rem',
  },
  uploadSection: {
    marginBottom: '2rem',
  },
  uploadZone: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.75rem',
    padding: '2.5rem',
    background: 'var(--surface)',
    border: '2px dashed var(--border)',
    borderRadius: 'var(--card-radius)',
    cursor: 'pointer',
    transition: 'border-color 0.2s, background 0.2s',
  },
  uploadIcon: {
    fontSize: '2rem',
  },
  uploadText: {
    color: 'var(--text-muted)',
    fontSize: '0.95rem',
  },
  error: {
    color: '#ef4444',
    marginTop: '0.75rem',
    fontSize: '0.9rem',
  },
  cards: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: '1rem',
    marginBottom: '2rem',
  },
  card: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--card-radius)',
    padding: '1.25rem',
  },
  cardLabel: {
    color: 'var(--text-muted)',
    fontSize: '0.8rem',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    marginBottom: '0.5rem',
  },
  cardValue: {
    fontSize: '1.75rem',
    fontWeight: 700,
  },
  cardValueSmall: {
    fontSize: '1rem',
    fontWeight: 600,
  },
  chartSection: {
    marginBottom: '2rem',
  },
  sectionTitle: {
    fontSize: '1.1rem',
    fontWeight: 600,
    margin: '0 0 1rem',
  },
  chartWrap: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--card-radius)',
    padding: '1rem',
  },
  tableSection: {
    marginBottom: '2rem',
  },
  filters: {
    display: 'flex',
    gap: '0.75rem',
    marginBottom: '1rem',
    flexWrap: 'wrap',
  },
  select: {
    minWidth: 180,
    padding: '0.6rem 0.75rem',
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 8,
    color: 'var(--text)',
    fontSize: '0.9rem',
    cursor: 'pointer',
  },
  input: {
    flex: '1',
    minWidth: 200,
    padding: '0.6rem 0.75rem',
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 8,
    color: 'var(--text)',
    fontSize: '0.9rem',
  },
  btnLimpiar: {
    padding: '0.6rem 1rem',
    background: 'var(--border)',
    border: 'none',
    borderRadius: 8,
    color: 'var(--text)',
    fontSize: '0.9rem',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  },
  tableWrap: {
    overflowX: 'auto',
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--card-radius)',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '0.85rem',
  },
  th: {
    textAlign: 'left',
    padding: '0.75rem',
    borderBottom: '1px solid var(--border)',
    color: 'var(--text-muted)',
    fontWeight: 600,
    whiteSpace: 'nowrap',
  },
  tr: {
    borderBottom: '1px solid var(--border)',
  },
  td: {
    padding: '0.6rem 0.75rem',
    maxWidth: 280,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  muted: {
    color: 'var(--text-muted)',
    fontSize: '0.85rem',
    marginTop: '0.5rem',
  },
}
