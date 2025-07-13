import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const mockSummary = [
  { label: 'Total Income', value: '$15,200', color: 'bg-green-100 text-green-700' },
  { label: 'Total Expenses', value: '$9,100', color: 'bg-red-100 text-red-700' },
  { label: 'Net Savings', value: '$6,100', color: 'bg-blue-100 text-blue-700' },
];

const mockTransactions = [
  { date: '2024-01-10', description: 'Supermarket', amount: -120, type: 'expense' },
  { date: '2024-01-09', description: 'Salary', amount: 2000, type: 'income' },
  { date: '2024-02-08', description: 'Coffee', amount: -4.5, type: 'expense' },
  { date: '2024-02-07', description: 'Gym', amount: -45, type: 'expense' },
  { date: '2024-02-06', description: 'Freelance', amount: 500, type: 'income' },
  { date: '2024-03-10', description: 'Supermarket', amount: -220, type: 'expense' },
  { date: '2024-03-09', description: 'Salary', amount: 2500, type: 'income' },
  { date: '2024-03-08', description: 'Coffee', amount: -14.5, type: 'expense' },
  { date: '2024-03-07', description: 'Gym', amount: -45, type: 'expense' },
  { date: '2024-03-06', description: 'Freelance', amount: 800, type: 'income' },
];

// Agrupar por mes
const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const monthlyData: Record<string, { Income: number; Expenses: number }> = {};
mockTransactions.forEach(tx => {
  const date = new Date(tx.date);
  const month = months[date.getMonth()];
  if (!monthlyData[month]) monthlyData[month] = { Income: 0, Expenses: 0 };
  if (tx.type === 'income') monthlyData[month].Income += tx.amount;
  if (tx.type === 'expense') monthlyData[month].Expenses += Math.abs(tx.amount);
});
const barChartData = months.map(month => ({
  name: month,
  Income: monthlyData[month]?.Income || 0,
  Expenses: monthlyData[month]?.Expenses || 0,
}));

const Dashboard: React.FC = () => {
  return (
    <div className="flex flex-col items-start relative bg-white min-h-screen">
      <div className="flex flex-col min-h-[800px] items-start relative self-stretch w-full flex-[0_0_auto] bg-white">
        <div className="flex self-stretch w-full flex-col items-start relative flex-[0_0_auto]">
          {/* Header */}
          <div className="w-full border-b border-[#e5e8ea] px-10 py-3 flex items-center">
            <span className="font-bold text-lg text-[#111416]">FinTrack</span>
          </div>
          {/* Main content */}
          <div className="items-start justify-center px-4 md:px-40 py-5 flex-1 grow flex relative self-stretch w-full">
            <div className="flex flex-col max-w-[960px] w-full items-center relative flex-1 grow mb-[-2.00px] mx-auto">
              {/* Summary Cards */}
              <div className="w-full grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {mockSummary.map((item) => (
                  <div key={item.label} className={`rounded-2xl p-6 shadow-sm flex flex-col items-center ${item.color}`}>
                    <span className="text-2xl font-bold mb-1">{item.value}</span>
                    <span className="text-base font-medium text-gray-500">{item.label}</span>
                  </div>
                ))}
              </div>
              {/* Bar Chart Real agrupado por mes */}
              <div className="w-full bg-white rounded-2xl shadow-sm p-6 mb-8 flex flex-col items-center">
                <span className="font-bold text-lg text-[#111416] mb-2">Spending & Income by Month</span>
                <div className="w-full h-64 flex items-center justify-center">
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={barChartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="Income" fill="#4ade80" radius={[6, 6, 0, 0]} />
                      <Bar dataKey="Expenses" fill="#f87171" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
              {/* Latest Transactions */}
              <div className="flex flex-col items-start pt-5 pb-3 px-4 relative self-stretch w-full flex-[0_0_auto]">
                <div className="font-bold text-[#111416] text-[22px] tracking-[0] leading-7 mb-2">
                  Latest Transactions
                </div>
                <div className="w-full overflow-x-auto">
                  <table className="min-w-full bg-white rounded-xl shadow-sm">
                    <thead>
                      <tr>
                        <th className="px-4 py-2 text-left text-gray-500 font-semibold">Date</th>
                        <th className="px-4 py-2 text-left text-gray-500 font-semibold">Description</th>
                        <th className="px-4 py-2 text-right text-gray-500 font-semibold">Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {mockTransactions.map((tx, idx) => (
                        <tr key={idx} className="border-b last:border-b-0">
                          <td className="px-4 py-2 text-gray-700 whitespace-nowrap">{tx.date}</td>
                          <td className="px-4 py-2 text-gray-700 whitespace-nowrap">{tx.description}</td>
                          <td className={`px-4 py-2 text-right font-semibold ${tx.type === 'income' ? 'text-green-600' : 'text-red-600'}`}>{tx.type === 'income' ? '+' : '-'}${Math.abs(tx.amount).toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 