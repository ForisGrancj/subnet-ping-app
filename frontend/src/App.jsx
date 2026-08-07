import React, { useState } from 'react';
import axios from 'axios';
import { Search, Activity, Database, CheckCircle2, XCircle } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

export default function App() {
  const [subnetValue, setSubnetValue] = useState('127.0.0.0/30');
  const [queryId, setQueryId] = useState('');
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [error, setError] = useState('');

  const handleScan = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await axios.post(`${API_BASE_URL}/ping/`, { subnet_value: subnetValue });
      setResultData(res.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Tarama isteği başarısız oldu.');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchLog = async (e) => {
    e.preventDefault();
    if (!queryId) return;
    setLoading(true);
    setError('');

    try {
      const res = await axios.get(`${API_BASE_URL}/logs/?query_id=${queryId}`);
      setResultData(res.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Log kaydı bulunamadı.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6">
      {/* Üst Başlık */}
      <header className="flex items-center gap-3 mb-8 border-b border-slate-800 pb-4">
        <Activity className="w-8 h-8 text-cyan-400" />
        <h1 className="text-2xl font-bold tracking-wide">Subnet Ping & Logger Dashboard</h1>
      </header>

      {/* Kontrol Paneli */}
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        {/* Subnet Scan Formu */}
        <div className="md:col-span-2 bg-slate-800/50 p-5 rounded-xl border border-slate-700">
          <label className="block text-sm font-medium mb-2 text-slate-300">Target CIDR Subnet</label>
          <form onSubmit={handleScan} className="flex gap-3">
            <input
              type="text"
              value={subnetValue}
              onChange={(e) => setSubnetValue(e.target.value)}
              placeholder="e.g. 192.168.1.0/28"
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-cyan-500"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-cyan-600 hover:bg-cyan-500 text-white font-medium px-5 py-2 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
            >
              {loading ? 'Scanning...' : 'Scan Subnet'}
            </button>
          </form>
        </div>

        {/* Log Arama Formu */}
        <div className="bg-slate-800/50 p-5 rounded-xl border border-slate-700">
          <label className="block text-sm font-medium mb-2 text-slate-300">Lookup by Query ID</label>
          <form onSubmit={handleFetchLog} className="flex gap-2">
            <input
              type="text"
              value={queryId}
              onChange={(e) => setQueryId(e.target.value)}
              placeholder="ID (e.g. 42)"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-cyan-500"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-slate-700 hover:bg-slate-600 text-slate-200 p-2 rounded-lg cursor-pointer"
            >
              <Search className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>

      {/* Hata Kutusu */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 p-4 rounded-xl mb-6">
          {error}
        </div>
      )}
      {resultData && (
        <div className="bg-slate-800/30 border border-slate-700 rounded-xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Database className="w-5 h-5 text-cyan-400" />
              Scan Results
            </h2>
            <span className="px-3 py-1 rounded-full text-xs font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              Source: {resultData.source || 'Database'}
            </span>
          </div>

          {resultData.message && (
            <p className="text-sm text-slate-400 mb-4">{resultData.message}</p>
          )}
          {Array.isArray(resultData.data) && (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-700 text-slate-400 text-sm">
                    <th className="py-3 px-4">Host IP</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Latency (RTT)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {resultData.data.map((host, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40">
                      <td className="py-3 px-4 font-mono">{host.ip_address}</td>
                      <td className="py-3 px-4">
                        {host.is_active ? (
                          <span className="inline-flex items-center gap-1.5 text-emerald-400 text-sm">
                            <CheckCircle2 className="w-4 h-4" /> Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 text-rose-400 text-sm">
                            <XCircle className="w-4 h-4" /> Inactive
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-400">
                        {host.rtt !== null ? `${host.rtt} ms` : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}