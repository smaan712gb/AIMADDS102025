import { 
  LineChart, 
  BarChart, 
  PieChart,
  Line, 
  Bar, 
  Pie,
  Cell,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

export function ChartRenderer({ chartData }) {
  if (!chartData || !chartData.type) {
    return null;
  }

  const commonProps = {
    width: "100%",
    height: 300
  };

  switch (chartData.type) {
    case 'line':
      return (
        <div className="my-4 p-4 bg-white rounded-lg shadow">
          {chartData.title && (
            <h4 className="text-lg font-semibold mb-2 text-gray-900">{chartData.title}</h4>
          )}
          <ResponsiveContainer {...commonProps}>
            <LineChart data={chartData.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={chartData.xKey || "name"} />
              <YAxis />
              <Tooltip />
              <Legend />
              {chartData.series && chartData.series.map((series, index) => (
                <Line 
                  key={series.key} 
                  type="monotone" 
                  dataKey={series.key} 
                  stroke={series.color || COLORS[index % COLORS.length]}
                  name={series.name || series.key}
                  strokeWidth={2}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      );

    case 'bar':
      return (
        <div className="my-4 p-4 bg-white rounded-lg shadow">
          {chartData.title && (
            <h4 className="text-lg font-semibold mb-2 text-gray-900">{chartData.title}</h4>
          )}
          <ResponsiveContainer {...commonProps}>
            <BarChart data={chartData.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={chartData.xKey || "name"} />
              <YAxis />
              <Tooltip />
              <Legend />
              {chartData.series && chartData.series.map((series, index) => (
                <Bar 
                  key={series.key} 
                  dataKey={series.key} 
                  fill={series.color || COLORS[index % COLORS.length]}
                  name={series.name || series.key}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      );

    case 'pie':
      return (
        <div className="my-4 p-4 bg-white rounded-lg shadow">
          {chartData.title && (
            <h4 className="text-lg font-semibold mb-2 text-gray-900">{chartData.title}</h4>
          )}
          <ResponsiveContainer {...commonProps}>
            <PieChart>
              <Pie
                data={chartData.data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => entry.name}
                outerRadius={80}
                fill="#8884d8"
                dataKey={chartData.valueKey || "value"}
              >
                {chartData.data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      );

    default:
      return null;
  }
}

// Helper function to detect if response contains chart data
export function extractChartData(content) {
  try {
    // Look for JSON chart data in markdown code blocks
    const chartRegex = /```chart\n([\s\S]*?)```/g;
    const match = chartRegex.exec(content);
    
    if (match && match[1]) {
      const chartData = JSON.parse(match[1]);
      // Remove chart block from content
      const cleanContent = content.replace(match[0], '');
      return { chartData, cleanContent };
    }
  } catch (e) {
    console.error('Error parsing chart data:', e);
  }
  
  return { chartData: null, cleanContent: content };
}
