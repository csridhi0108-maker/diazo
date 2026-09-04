import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

function GlucoseChart({ logs }) {
  const chartData = [...logs]
    .reverse()
    .map((log) => ({
      time: new Date(log.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      value: log.value,
    }))

  if (chartData.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-400 text-sm bg-slate-50 rounded-xl border border-dashed border-slate-200">
        No glucose readings logged yet
      </div>
    )
  }

  return (
    // Increased height to 320 to fill the container vertically
    <ResponsiveContainer width="100%" height={320}>
      {/* Adjusted margins: top/bottom/left push the graph away from the edges/labels */}
      <LineChart data={chartData} margin={{ top: 20, right: 20, left: 10, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
        <XAxis 
          dataKey="time" 
          tick={{ fontSize: 12, fill: '#6b7280' }} 
          stroke="#e5e7eb" 
          tickLine={false}
          axisLine={false}
          dy={10} // Adds extra space below the X-axis labels
        />
        <YAxis 
          tick={{ fontSize: 12, fill: '#6b7280' }} 
          stroke="#e5e7eb" 
          tickLine={false}
          axisLine={false}
          domain={['dataMin - 10', 'dataMax + 10']} 
          width={40} // Gives more room for the Y-axis numbers like "94"
          dx={-10} // Pushes Y-axis labels slightly left
        />
        <Tooltip
          contentStyle={{ 
            borderRadius: '8px', 
            border: '1px solid #e5e7eb', 
            fontSize: '13px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}
        />
        <Line
          type="monotone"
          dataKey="value"
          stroke="#059669"
          strokeWidth={2.5}
          dot={{ r: 4, fill: '#059669', strokeWidth: 2, stroke: '#fff' }}
          activeDot={{ r: 6, stroke: '#059669', strokeWidth: 2, fill: '#fff' }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

export default GlucoseChart