/**
 * Example usage of Chart Components
 * This file demonstrates how to use BarChart, LineChart, and PieChart
 */

import { BarChart, LineChart, PieChart } from './index'

// Sample data
const monthlyData = [
  { name: 'Jan', value: 100 },
  { name: 'Feb', value: 200 },
  { name: 'Mar', value: 150 },
  { name: 'Apr', value: 300 },
  { name: 'May', value: 250 },
]

const categoryData = [
  { name: 'Electronics', value: 400 },
  { name: 'Clothing', value: 300 },
  { name: 'Food', value: 200 },
  { name: 'Books', value: 100 },
]

export function ChartExamples() {
  return (
    <div style={{ padding: '20px' }}>
      <h1>Chart Component Examples</h1>

      <section style={{ marginBottom: '40px' }}>
        <h2>Bar Chart</h2>
        <BarChart
          data={monthlyData}
          height={300}
          color="#1976d2"
          ariaLabel="Monthly sales bar chart"
        />
      </section>

      <section style={{ marginBottom: '40px' }}>
        <h2>Line Chart</h2>
        <LineChart
          data={monthlyData}
          height={300}
          color="#388e3c"
          ariaLabel="Monthly trend line chart"
        />
      </section>

      <section style={{ marginBottom: '40px' }}>
        <h2>Pie Chart</h2>
        <PieChart
          data={categoryData}
          height={350}
          ariaLabel="Category distribution pie chart"
        />
      </section>

      <section style={{ marginBottom: '40px' }}>
        <h2>Pie Chart with Custom Colors</h2>
        <PieChart
          data={categoryData}
          height={350}
          colors={['#ff6b6b', '#4ecdc4', '#45b7d1', '#f7b731']}
          ariaLabel="Category distribution with custom colors"
        />
      </section>
    </div>
  )
}
