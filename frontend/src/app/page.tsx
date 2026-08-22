"use client";

import React, { useState } from "react";
import { 
  ShieldCheck, 
  ShieldAlert, 
  ShieldX, 
  Activity, 
  Zap, 
  Send, 
  RefreshCw 
} from "lucide-react";

interface AuditLog {
  id: string;
  email: string;
  amount: number;
  currency: string;
  score: number;
  tier: "ALLOW" | "MANUAL_REVIEW" | "BLOCK";
  latency: string;
  reason: string;
  timestamp: string;
}

export default function ShieldFlowDashboard() {
  const [logs, setLogs] = useState<AuditLog[]>([
    {
      id: "pay_O9xK3B8Z11L",
      email: "fraudster@tempmail.com",
      amount: 45000,
      currency: "INR",
      score: 100,
      tier: "BLOCK",
      latency: "3.42ms",
      reason: "Disposable email domain, TOR exit node detected",
      timestamp: "Just now"
    },
    {
      id: "pay_K2lM9P4Q00X",
      email: "buyer@gmail.com",
      amount: 1200,
      currency: "INR",
      score: 12,
      tier: "ALLOW",
      latency: "1.85ms",
      reason: "Clean IP reputation, valid billing address",
      timestamp: "2 mins ago"
    },
    {
      id: "pay_V8vC5R2T66Y",
      email: "suspicious.shopper@outlook.com",
      amount: 18500,
      currency: "INR",
      score: 55,
      tier: "MANUAL_REVIEW",
      latency: "4.10ms",
      reason: "High velocity rate limit spike detected",
      timestamp: "5 mins ago"
    }
  ]);

  const [simulating, setSimulating] = useState(false);

  const simulateIncomingWebhook = async () => {
    setSimulating(true);
    setTimeout(() => {
      const isRisky = Math.random() > 0.5;
      const newLog: AuditLog = {
        id: `pay_${Math.random().toString(36).substring(2, 9).toUpperCase()}`,
        email: isRisky ? "bot@disposable-inbox.com" : "customer@verified.org",
        amount: isRisky ? Math.floor(Math.random() * 50000 + 10000) : Math.floor(Math.random() * 5000 + 500),
        currency: "INR",
        score: isRisky ? 95 : 8,
        tier: isRisky ? "BLOCK" : "ALLOW",
        latency: `${(Math.random() * 3 + 1.2).toFixed(2)}ms`,
        reason: isRisky ? "Disposable inbox + IP proxy detected" : "Trusted merchant history",
        timestamp: "Just now"
      };
      setLogs((prev) => [newLog, ...prev]);
      setSimulating(false);
    }, 600);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 font-sans">
      <header className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between border-b border-slate-800 pb-6 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">ShieldFlow AI</h1>
              <p className="text-sm text-slate-400">Real-Time Payment Risk & Fraud Mitigation Engine</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={simulateIncomingWebhook}
            disabled={simulating}
            className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 active:scale-95 text-slate-950 px-4 py-2 rounded-lg font-semibold transition-all disabled:opacity-50 text-sm cursor-pointer shadow-lg shadow-emerald-500/10"
          >
            {simulating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            Simulate Webhook
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto mt-8 space-y-8">
        <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-xl">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium uppercase tracking-wider">Fast-Path Latency</span>
              <Zap className="w-4 h-4 text-amber-400" />
            </div>
            <p className="text-2xl font-bold text-white">&lt; 3.5ms</p>
            <p className="text-xs text-slate-500 mt-1">Sub-10ms Redis Heuristics</p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-xl">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium uppercase tracking-wider">Allowed Rate</span>
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-2xl font-bold text-emerald-400">92.4%</p>
            <p className="text-xs text-slate-500 mt-1">Legitimate transactions</p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-xl">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium uppercase tracking-wider">Blocked (Fraud)</span>
              <ShieldX className="w-4 h-4 text-rose-400" />
            </div>
            <p className="text-2xl font-bold text-rose-400">5.1%</p>
            <p className="text-xs text-slate-500 mt-1">Auto-refunded & halted</p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-xl">
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-medium uppercase tracking-wider">HITL Manual Queue</span>
              <ShieldAlert className="w-4 h-4 text-yellow-400" />
            </div>
            <p className="text-2xl font-bold text-yellow-400">2.5%</p>
            <p className="text-xs text-slate-500 mt-1">Awaiting analyst action</p>
          </div>
        </section>

        <section className="bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden shadow-sm">
          <div className="p-5 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-200">Live Decision Audit Feed</h2>
            </div>
            <span className="text-xs text-slate-500">Auto-refreshing</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/50 text-xs uppercase text-slate-500 tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-6 py-3">Transaction ID</th>
                  <th className="px-6 py-3">Payer Email</th>
                  <th className="px-6 py-3">Amount</th>
                  <th className="px-6 py-3">Risk Tier</th>
                  <th className="px-6 py-3">Risk Score</th>
                  <th className="px-6 py-3">Latency</th>
                  <th className="px-6 py-3">Detected Anomalies</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs text-slate-400">{log.id}</td>
                    <td className="px-6 py-4 text-slate-200">{log.email}</td>
                    <td className="px-6 py-4 font-medium text-white">₹{log.amount.toLocaleString()}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        log.tier === "ALLOW"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : log.tier === "BLOCK"
                          ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                          : "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                      }`}>
                        {log.tier}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono font-medium">{log.score}/100</td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-400">{log.latency}</td>
                    <td className="px-6 py-4 text-xs text-slate-400 max-w-xs truncate">{log.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}
