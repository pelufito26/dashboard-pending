import { useState, useMemo, useEffect } from 'react'
import { PieChart, Pie, Tooltip, ResponsiveContainer, Cell, Legend } from 'recharts'

const API_BASE = '/api'

/** Tooltip legible: fondo claro, muestra comentario/categoría + cantidad de órdenes */
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const { name, value } = payload[0]
  return (
    <div style={{
      background: '#ffffff',
      color: '#1e293b',
      padding: '12px 16px',
      borderRadius: 8,
      border: '1px solid #cbd5e1',
      boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
      fontSize: '0.9rem',
      lineHeight: 1.5,
      minWidth: 180,
    }}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>Comentario / Categoría</div>
      <div style={{ color: '#475569', marginBottom: 8, wordBreak: 'break-word' }}>{name}</div>
      <div style={{ fontWeight: 600 }}>Órdenes: {value}</div>
    </div>
  )
}

// Paleta azul y blanco (tonalidades claras para buena lectura)
const COLORS = [
  '#1e40af', '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe', '#eff6ff',
  '#0ea5e9', '#0284c7', '#0369a1', '#1d4ed8',
]

// Merchant generales: agrupar cuentas (Meli, Walmart, Fravega, etc.)
const MERCHANT_GRUPOS = {
  Meli: ['MELI_TIER_ONE', 'MeLiUS_Standard', 'MercadoLibre', 'MercadoLibreUY'],
  Walmart: ['Walmart', 'WalmartCN', 'WalmartUSCL'],
  Fravega: ['FravegaUS', 'FravegaCN'],
  Carrefour: ['Carrefour', 'CarrefourCN'],
  ViaVarejo: ['ViaVarejo', 'ViaVarejoCN'],
  MagaluCBT: ['MagaluCBTUS', 'MagaluCBTCN'],
  Megatone: ['MegatoneUS', 'MegatoneCN'],
  Coppel: ['CoppelUS', 'CoppelCN'],
}
function merchantGeneral(name) {
  const n = (name || '').trim()
  for (const [general, cuentas] of Object.entries(MERCHANT_GRUPOS)) {
    if (cuentas.some((c) => c.toLowerCase() === n.toLowerCase())) return general
  }
  return n || 'Sin merchant'
}

export default function App() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [loadingLast, setLoadingLast] = useState(true)
  const [redisOk, setRedisOk] = useState(null)
  const [merchantChartFilter, setMerchantChartFilter] = useState('total') // 'total' | '2P' | '3P'

  useEffect(() => {
    fetch(`${API_BASE}/process`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && typeof data.redis_ok === 'boolean') setRedisOk(data.redis_ok)
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
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const chartData = useMemo(() => {
    if (!result?.stats?.distribucion_accionables) return []
    return Object.entries(result.stats.distribucion_accionables).map(([name, count]) => ({ name, value: count }))
  }, [result])

  const merchantGeneralData = useMemo(() => {
    if (!result?.tabla?.length) return []
    let rows = result.tabla
    if (merchantChartFilter !== 'total') {
      rows = rows.filter(
        (row) => String(row['order_type'] || '').trim().toUpperCase() === merchantChartFilter
      )
    }
    const counts = {}
    for (const row of rows) {
      const g = merchantGeneral(row['Merchant Name'])
      counts[g] = (counts[g] || 0) + 1
    }
    return Object.entries(counts)
      .map(([name, count]) => ({ name, value: count }))
      .sort((a, b) => b.value - a.value)
  }, [result, merchantChartFilter])

  const ageingBucket = (row) => {
    const col = 'Ageing Buckets (in_process_date)'
    const raw = row[col]
    if (raw != null && String(raw).trim() !== '') return String(raw).trim()
    const daysRaw = row['Days since in process date']
    let d
    try {
      d = parseInt(String(daysRaw).replace(/\D/g, ''), 10)
    } catch {
      return 'Sin datos'
    }
    if (isNaN(d)) return 'Sin datos'
    if (d <= 3) return '0-3 días'
    if (d <= 6) return '4-6 días'
    if (d <= 14) return '7-14 días'
    return '15+ días'
  }

  const ageingData = useMemo(() => {
    if (!result?.tabla?.length) return []
    const counts = {}
    for (const row of result.tabla) {
      const b = ageingBucket(row)
      counts[b] = (counts[b] || 0) + 1
    }
    const order = ['0-3 días', '4-6 días', '7-14 días', '15+ días', 'Sin datos']
    const ordered = order.filter((b) => counts[b]).map((name) => ({ name, value: counts[name] }))
    const rest = Object.keys(counts)
      .filter((b) => !order.includes(b))
      .map((name) => ({ name, value: counts[name] }))
    return ordered.concat(rest)
  }, [result])

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
        {!loadingLast && redisOk === false && (
          <p style={styles.muted}>Redis no detectado. En Vercel: Settings → Environment Variables deben existir <strong>UPSTASH_REDIS_REST_URL</strong> y <strong>UPSTASH_REDIS_REST_TOKEN</strong> (o agregá Upstash Redis desde Marketplace). Redeploy después.</p>
        )}
        {!loadingLast && !result && !loading && redisOk !== false && (
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
                  <PieChart>
                    <Pie
                      data={chartData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={120}
                      stroke="#fff"
                      strokeWidth={1.5}
                    >
                      {chartData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<ChartTooltip />} />
                    <Legend formatter={(value) => <span style={{ color: 'var(--text)' }}>{value}</span>} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </section>
          )}

          {merchantGeneralData.length > 0 && (
            <section style={styles.chartSection}>
              <div style={styles.chartHeader}>
                <h2 style={styles.sectionTitle}>Distribución por Merchant</h2>
                <select
                  value={merchantChartFilter}
                  onChange={(e) => setMerchantChartFilter(e.target.value)}
                  style={styles.select}
                  aria-label="Filtrar por tipo de orden"
                >
                  <option value="total">Total</option>
                  <option value="2P">2P</option>
                  <option value="3P">3P</option>
                </select>
              </div>
              <p style={styles.muted}>
                Agrupados: Meli, Walmart, Fravega (US+CN), Carrefour (+CN), ViaVarejo (+CN), MagaluCBT (US+CN), Megatone (US+CN), Coppel (US+CN)
              </p>
              <div style={styles.chartWrap}>
                <ResponsiveContainer width="100%" height={360}>
                  <PieChart>
                    <Pie
                      data={merchantGeneralData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={120}
                      stroke="#fff"
                      strokeWidth={1.5}
                    >
                      {merchantGeneralData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<ChartTooltip />} />
                    <Legend formatter={(value) => <span style={{ color: 'var(--text)' }}>{value}</span>} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </section>
          )}

          {ageingData.length > 0 && (
            <section style={styles.chartSection}>
              <h2 style={styles.sectionTitle}>Distribución por Ageing Buckets (in_process_date)</h2>
              <div style={styles.chartWrap}>
                <ResponsiveContainer width="100%" height={360}>
                  <PieChart>
                    <Pie
                      data={ageingData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={120}
                      stroke="#fff"
                      strokeWidth={1.5}
                    >
                      {ageingData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<ChartTooltip />} />
                    <Legend formatter={(value) => <span style={{ color: 'var(--text)' }}>{value}</span>} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </section>
          )}
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
  chartHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    flexWrap: 'wrap',
    marginBottom: '0.5rem',
  },
  sectionTitle: {
    fontSize: '1.1rem',
    fontWeight: 600,
    margin: 0,
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
