import { useState, useMemo, useEffect } from 'react'
import { PieChart, Pie, Tooltip, ResponsiveContainer, Cell, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts'

const API_BASE = '/api'

const tooltipStyle = {
  background: '#ffffff',
  color: '#1e293b',
  padding: '12px 16px',
  borderRadius: 8,
  border: '1px solid #cbd5e1',
  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
  fontSize: '0.9rem',
  lineHeight: 1.5,
  minWidth: 180,
}

/** Tooltip legible: fondo claro, muestra comentario/categoría + cantidad de órdenes */
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const { name, value } = payload[0]
  return (
    <div style={tooltipStyle}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>Comentario / Categoría</div>
      <div style={{ color: '#475569', marginBottom: 8, wordBreak: 'break-word' }}>{name}</div>
      <div style={{ fontWeight: 600 }}>Órdenes: {value}</div>
    </div>
  )
}

/** Tooltip para gráfico de columnas: Ageing Bucket + lista de comentarios y órdenes */
function BarChartTooltip({ active, payload, label, commentKeys }) {
  if (!active || !payload?.length) return null
  const total = payload.reduce((s, p) => s + (p.value || 0), 0)
  return (
    <div style={tooltipStyle}>
      <div style={{ fontWeight: 600, marginBottom: 6 }}>Ageing Bucket</div>
      <div style={{ color: '#475569', marginBottom: 10 }}>{label}</div>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>Comentarios y órdenes</div>
      {payload.filter((p) => p.value != null && p.value !== 0).map((p) => (
        <div key={p.name} style={{ marginBottom: 2 }}>
          <span style={{ color: '#475569' }}>{p.name}:</span> <strong>{p.value}</strong>
        </div>
      ))}
      <div style={{ marginTop: 6, paddingTop: 6, borderTop: '1px solid #e2e8f0', fontWeight: 600 }}>Total: {total}</div>
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
  const [ageingChartFilter, setAgeingChartFilter] = useState('total') // 'total' | '2P' | '3P'
  const [accionablesChartFilter, setAccionablesChartFilter] = useState('total') // 'total' | '2P' | '3P'
  const [lateMeliFilter, setLateMeliFilter] = useState('total')
  const [lateAllFilter, setLateAllFilter] = useState('total')
  const [showLateByAgeing, setShowLateByAgeing] = useState(false) // casilla: true = columnas por Ageing, false = torta general

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
    if (!result?.tabla?.length && !result?.stats?.distribucion_accionables) return []
    if (accionablesChartFilter === 'total' && result?.stats?.distribucion_accionables) {
      return Object.entries(result.stats.distribucion_accionables).map(([name, count]) => ({ name, value: count }))
    }
    let rows = result.tabla || []
    if (accionablesChartFilter !== 'total') {
      rows = rows.filter(
        (row) => String(row['order_type'] || '').trim().toUpperCase() === accionablesChartFilter
      )
    }
    const counts = {}
    for (const row of rows) {
      const a = String(row['Accionables'] || '').trim() || 'Sin comentario'
      counts[a] = (counts[a] || 0) + 1
    }
    return Object.entries(counts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
  }, [result, accionablesChartFilter])

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

  // Valor del campo "Ageing Buckets (in_process_date)": 3-5, 6-10, 11-20, +20 (tal como viene en los datos)
  const ageingBucket = (row) => {
    const col = 'Ageing Buckets (in_process_date)'
    const raw = row[col]
    if (raw != null && String(raw).trim() !== '') return String(raw).trim()
    return 'Sin datos'
  }

  const bucketOrder = ['3-5', '6-10', '11-20', '+20', 'Sin datos']

  const buildBucketCommentData = (rows) => {
    const byBucket = {}
    const commentSet = new Set()
    for (const row of rows) {
      const bucket = ageingBucket(row)
      const comment = String(row['Accionables'] || '').trim() || 'Sin comentario'
      commentSet.add(comment)
      if (!byBucket[bucket]) byBucket[bucket] = {}
      byBucket[bucket][comment] = (byBucket[bucket][comment] || 0) + 1
    }
    const commentKeys = Array.from(commentSet).sort((a, b) => a.localeCompare(b))
    const orderedBuckets = bucketOrder.filter((b) => byBucket[b]).concat(
      Object.keys(byBucket).filter((b) => !bucketOrder.includes(b))
    )
    const data = orderedBuckets.map((bucket) => ({ name: bucket, ...byBucket[bucket] }))
    return { data, commentKeys }
  }

  // Datos para gráfico de columnas: Comentarios (Accionables) x Ageing Buckets, con filtro 2P/3P/Total
  const ageingByCommentData = useMemo(() => {
    if (!result?.tabla?.length) return { data: [], commentKeys: [] }
    let rows = result.tabla
    if (ageingChartFilter !== 'total') {
      rows = rows.filter(
        (row) => String(row['order_type'] || '').trim().toUpperCase() === ageingChartFilter
      )
    }
    return buildBucketCommentData(rows)
  }, [result, ageingChartFilter])

  const isLate = (row) => String(row['SLA per mile'] || '').trim().toLowerCase() === 'late'

  // Órdenes Late - Solo Meli: distribución global por comentarios (sin Ageing)
  const lateMeliData = useMemo(() => {
    if (!result?.tabla?.length) return []
    let rows = result.tabla.filter(
      (row) => isLate(row) && merchantGeneral(row['Merchant Name']) === 'Meli'
    )
    if (lateMeliFilter !== 'total') {
      rows = rows.filter(
        (row) => String(row['order_type'] || '').trim().toUpperCase() === lateMeliFilter
      )
    }
    const counts = {}
    for (const row of rows) {
      const a = String(row['Accionables'] || '').trim() || 'Sin comentario'
      counts[a] = (counts[a] || 0) + 1
    }
    return Object.entries(counts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
  }, [result, lateMeliFilter])

  // Órdenes Late - Todos los merchants: distribución global por comentarios (sin Ageing)
  const lateAllData = useMemo(() => {
    if (!result?.tabla?.length) return []
    let rows = result.tabla.filter(isLate)
    if (lateAllFilter !== 'total') {
      rows = rows.filter(
        (row) => String(row['order_type'] || '').trim().toUpperCase() === lateAllFilter
      )
    }
    const counts = {}
    for (const row of rows) {
      const a = String(row['Accionables'] || '').trim() || 'Sin comentario'
      counts[a] = (counts[a] || 0) + 1
    }
    return Object.entries(counts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
  }, [result, lateAllFilter])

  // Órdenes Late - datos por Ageing (para cuando la casilla "Separar por Ageing" está tildada)
  const lateMeliDataByAgeing = useMemo(() => {
    if (!result?.tabla?.length) return { data: [], commentKeys: [] }
    let rows = result.tabla.filter(
      (row) => isLate(row) && merchantGeneral(row['Merchant Name']) === 'Meli'
    )
    if (lateMeliFilter !== 'total') {
      rows = rows.filter(
        (row) => String(row['order_type'] || '').trim().toUpperCase() === lateMeliFilter
      )
    }
    return buildBucketCommentData(rows)
  }, [result, lateMeliFilter])

  const lateAllDataByAgeing = useMemo(() => {
    if (!result?.tabla?.length) return { data: [], commentKeys: [] }
    let rows = result.tabla.filter(isLate)
    if (lateAllFilter !== 'total') {
      rows = rows.filter(
        (row) => String(row['order_type'] || '').trim().toUpperCase() === lateAllFilter
      )
    }
    return buildBucketCommentData(rows)
  }, [result, lateAllFilter])

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
          <p style={styles.milestoneNote}>
            Milestones válidos: <strong>1.1 - First Mile: Seller</strong> y <strong>1.2 - Already with seller_delivered_at</strong>. Todos los datos del tablero aplican solo a órdenes con estos milestones.
          </p>

          <div className="dashboard-pie-grid">
          {chartData.length > 0 && (
            <section style={styles.chartSection} className="dashboard-card-tile">
              <div style={styles.chartHeader}>
                <h2 style={styles.sectionTitle}>Distribución de accionables</h2>
                <select
                  value={accionablesChartFilter}
                  onChange={(e) => setAccionablesChartFilter(e.target.value)}
                  style={styles.select}
                  aria-label="Filtrar por tipo de orden"
                >
                  <option value="total">Total</option>
                  <option value="2P">2P</option>
                  <option value="3P">3P</option>
                </select>
              </div>
              <div style={styles.chartWrap} className="chart-tile-inner">
                <ResponsiveContainer width="100%" height={320}>
                  <PieChart>
                    <Pie
                      data={chartData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={110}
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
            <section style={styles.chartSection} className="dashboard-card-tile">
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
                Meli, Walmart, Fravega, Carrefour, ViaVarejo, MagaluCBT, Megatone, Coppel (agrupados)
              </p>
              <div style={styles.chartWrap} className="chart-tile-inner">
                <ResponsiveContainer width="100%" height={320}>
                  <PieChart>
                    <Pie
                      data={merchantGeneralData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={110}
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

          {(lateMeliData.length > 0 || lateAllData.length > 0) && (
            <section style={styles.chartSection} className="dashboard-bar-full">
              <label style={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={showLateByAgeing}
                  onChange={(e) => setShowLateByAgeing(e.target.checked)}
                  style={styles.checkbox}
                />
                <span>Separar por Ageing</span>
              </label>
            </section>
          )}

          {lateMeliData.length > 0 && (
            <section
              style={styles.chartSection}
              className={showLateByAgeing && lateMeliDataByAgeing.data.length > 0 ? 'dashboard-bar-full' : 'dashboard-card-tile'}
            >
              <div style={styles.chartHeader}>
                <h2 style={styles.sectionTitle}>Órdenes Late – Solo Meli</h2>
                <select
                  value={lateMeliFilter}
                  onChange={(e) => setLateMeliFilter(e.target.value)}
                  style={styles.select}
                  aria-label="Filtrar por tipo de orden"
                >
                  <option value="total">Total</option>
                  <option value="2P">2P</option>
                  <option value="3P">3P</option>
                </select>
              </div>
              <p style={styles.muted}>
                {showLateByAgeing
                  ? 'SLA per mile = "late", merchant Meli. Comentarios por Ageing Buckets.'
                  : 'SLA per mile = "late", merchant Meli (y sus cuentas). Distribución por comentarios.'}
              </p>
              <div style={styles.chartWrap} className={showLateByAgeing && lateMeliDataByAgeing.data.length > 0 ? '' : 'chart-tile-inner'}>
                {showLateByAgeing && lateMeliDataByAgeing.data.length > 0 && lateMeliDataByAgeing.commentKeys.length > 0 ? (
                  <ResponsiveContainer width="100%" height={380}>
                    <BarChart
                      data={lateMeliDataByAgeing.data}
                      margin={{ top: 16, right: 24, left: 24, bottom: 80 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis
                        dataKey="name"
                        tick={{ fill: 'var(--text)', fontSize: 12 }}
                        angle={-35}
                        textAnchor="end"
                        height={60}
                      />
                      <YAxis tick={{ fill: 'var(--text)', fontSize: 12 }} label={{ value: 'Órdenes', angle: -90, position: 'insideLeft', style: { fill: 'var(--text)' } }} />
                      <Tooltip content={<BarChartTooltip commentKeys={lateMeliDataByAgeing.commentKeys} />} />
                      <Legend formatter={(value) => <span style={{ color: 'var(--text)', fontSize: 11 }}>{value}</span>} />
                      {lateMeliDataByAgeing.commentKeys.map((key, i) => (
                        <Bar
                          key={key}
                          dataKey={key}
                          name={key}
                          stackId="a"
                          fill={COLORS[i % COLORS.length]}
                          stroke="#fff"
                          strokeWidth={0.5}
                        />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <ResponsiveContainer width="100%" height={320}>
                    <PieChart>
                      <Pie
                        data={lateMeliData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={110}
                        stroke="#fff"
                        strokeWidth={1.5}
                      >
                        {lateMeliData.map((_, i) => (
                          <Cell key={i} fill={COLORS[i % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip content={<ChartTooltip />} />
                      <Legend formatter={(value) => <span style={{ color: 'var(--text)' }}>{value}</span>} />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>
            </section>
          )}

          {lateAllData.length > 0 && (
            <section
              style={styles.chartSection}
              className={showLateByAgeing && lateAllDataByAgeing.data.length > 0 ? 'dashboard-bar-full' : 'dashboard-card-tile'}
            >
              <div style={styles.chartHeader}>
                <h2 style={styles.sectionTitle}>Órdenes Late – Todos los merchants</h2>
                <select
                  value={lateAllFilter}
                  onChange={(e) => setLateAllFilter(e.target.value)}
                  style={styles.select}
                  aria-label="Filtrar por tipo de orden"
                >
                  <option value="total">Total</option>
                  <option value="2P">2P</option>
                  <option value="3P">3P</option>
                </select>
              </div>
              <p style={styles.muted}>
                {showLateByAgeing
                  ? 'SLA per mile = "late". Comentarios por Ageing Buckets.'
                  : 'SLA per mile = "late". Distribución por comentarios.'}
              </p>
              <div style={styles.chartWrap} className={showLateByAgeing && lateAllDataByAgeing.data.length > 0 ? '' : 'chart-tile-inner'}>
                {showLateByAgeing && lateAllDataByAgeing.data.length > 0 && lateAllDataByAgeing.commentKeys.length > 0 ? (
                  <ResponsiveContainer width="100%" height={380}>
                    <BarChart
                      data={lateAllDataByAgeing.data}
                      margin={{ top: 16, right: 24, left: 24, bottom: 80 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis
                        dataKey="name"
                        tick={{ fill: 'var(--text)', fontSize: 12 }}
                        angle={-35}
                        textAnchor="end"
                        height={60}
                      />
                      <YAxis tick={{ fill: 'var(--text)', fontSize: 12 }} label={{ value: 'Órdenes', angle: -90, position: 'insideLeft', style: { fill: 'var(--text)' } }} />
                      <Tooltip content={<BarChartTooltip commentKeys={lateAllDataByAgeing.commentKeys} />} />
                      <Legend formatter={(value) => <span style={{ color: 'var(--text)', fontSize: 11 }}>{value}</span>} />
                      {lateAllDataByAgeing.commentKeys.map((key, i) => (
                        <Bar
                          key={key}
                          dataKey={key}
                          name={key}
                          stackId="a"
                          fill={COLORS[i % COLORS.length]}
                          stroke="#fff"
                          strokeWidth={0.5}
                        />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <ResponsiveContainer width="100%" height={320}>
                    <PieChart>
                      <Pie
                        data={lateAllData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={110}
                        stroke="#fff"
                        strokeWidth={1.5}
                      >
                        {lateAllData.map((_, i) => (
                          <Cell key={i} fill={COLORS[i % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip content={<ChartTooltip />} />
                      <Legend formatter={(value) => <span style={{ color: 'var(--text)' }}>{value}</span>} />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>
            </section>
          )}
          </div>

          {ageingByCommentData.data.length > 0 && ageingByCommentData.commentKeys.length > 0 && (
            <section style={styles.chartSectionWide}>
              <div style={styles.chartHeader}>
                <h2 style={styles.sectionTitle}>Comentarios por Ageing Buckets (in_process_date)</h2>
                <select
                  value={ageingChartFilter}
                  onChange={(e) => setAgeingChartFilter(e.target.value)}
                  style={styles.select}
                  aria-label="Filtrar por tipo de orden"
                >
                  <option value="total">Total</option>
                  <option value="2P">2P</option>
                  <option value="3P">3P</option>
                </select>
              </div>
              <p style={styles.muted}>Eje horizontal: Ageing Buckets. Barras: cantidad de órdenes por comentario/accionable.</p>
              <div style={styles.chartWrapWide}>
                <ResponsiveContainer width="100%" height={440}>
                  <BarChart
                    data={ageingByCommentData.data}
                    margin={{ top: 16, right: 24, left: 24, bottom: 80 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis
                      dataKey="name"
                      tick={{ fill: 'var(--text)', fontSize: 12 }}
                      angle={-35}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis tick={{ fill: 'var(--text)', fontSize: 12 }} label={{ value: 'Órdenes', angle: -90, position: 'insideLeft', style: { fill: 'var(--text)' } }} />
                    <Tooltip content={<BarChartTooltip commentKeys={ageingByCommentData.commentKeys} />} />
                    <Legend formatter={(value) => <span style={{ color: 'var(--text)', fontSize: 11 }}>{value}</span>} />
                    {ageingByCommentData.commentKeys.map((key, i) => (
                      <Bar
                        key={key}
                        dataKey={key}
                        name={key}
                        stackId="a"
                        fill={COLORS[i % COLORS.length]}
                        stroke="#fff"
                        strokeWidth={0.5}
                      />
                    ))}
                  </BarChart>
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
    maxWidth: 1400,
    margin: '0 auto',
    padding: 'clamp(1rem, 4vw, 2rem)',
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
    gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
    gap: '1rem',
    marginBottom: '1.5rem',
  },
  card: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--card-radius)',
    padding: '1.25rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
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
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
  },
  chartSectionWide: {
    marginBottom: '2rem',
    width: '100%',
  },
  chartWrapWide: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--card-radius)',
    padding: '1.25rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
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
  milestoneNote: {
    color: 'var(--text-muted)',
    fontSize: '0.85rem',
    marginTop: '0.25rem',
    marginBottom: '1.5rem',
  },
  checkboxLabel: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.5rem',
    cursor: 'pointer',
    color: 'var(--text)',
    fontSize: '0.95rem',
    marginBottom: '0.5rem',
  },
  checkbox: {
    width: 18,
    height: 18,
    cursor: 'pointer',
    accentColor: 'var(--accent)',
  },
}
