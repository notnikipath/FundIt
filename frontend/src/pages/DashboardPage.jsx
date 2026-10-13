import React, { useEffect, useMemo, useState } from "react";

import { KpiCard } from "../components/KpiCard";
import { TaskBoard } from "../components/TaskBoard";

const runtimeHost = typeof window !== "undefined" ? window.location.hostname : "localhost";
const runtimeProtocol = typeof window !== "undefined" ? window.location.protocol : "http:";
const runtimePort = typeof window !== "undefined" ? window.location.port : "";
const defaultGatewayPort = runtimePort === "31029" ? "31028" : "8500";
const gatewayUrl = import.meta.env.VITE_API_GATEWAY_URL || `${runtimeProtocol}//${runtimeHost}:${defaultGatewayPort}`;

const emptyDashboard = {
  project: {
    project_id: "PRJ-DEMO",
    title: "FundIt Demo Project",
    short_description: "Crowdfunding campaign",
    goal_amount: 1,
    pledged_amount: 0,
    currency: "RUB",
    category: "tech",
    funding_model: "all_or_nothing",
    status: "active",
    tags: [],
    author_id: "AUTH-100",
  },
  rewards: { items: [], count: 0 },
  deliveries: { items: [], count: 0 },
  updates: { items: [], count: 0 },
  comments: { items: [], count: 0 },
  payments: { items: [], count: 0, total_gross: 0, total_fee: 0, total_net: 0 },
  analytics: {
    visits: 0,
    backers_count: 0,
    pledged_amount: 0,
    net_amount: 0,
    conversion_pct: 0,
    progress_pct: 0,
    forecast_success_score: 0,
    goal_amount: 1,
  },
  conversion: { visits: 0, backers_count: 0, conversion_pct: 0 },
  author_report: { projects: [], total_pledged: 0, total_refunds: 0, avg_conversion_pct: 0, avg_progress_pct: 0 },
  notifications: { items: [], count: 0, delivered_count: 0 },
};

async function loadDashboard(projectId) {
  const response = await fetch(`${gatewayUrl}/dashboard/${projectId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard: ${response.status}`);
  }
  return response.json();
}

async function pledge(payload) {
  const response = await fetch(`${gatewayUrl}/workflow/pledge`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const details = await response.text();
    throw new Error(`Pledge failed: ${details}`);
  }
  return response.json();
}

export function DashboardPage() {
  const [projectId, setProjectId] = useState("PRJ-DEMO");
  const [userId, setUserId] = useState("BACK-101");
  const [amount, setAmount] = useState(1500);
  const [rewardId, setRewardId] = useState("");
  const [theme, setTheme] = useState("light");

  const [status, setStatus] = useState("loading");
  const [error, setError] = useState(null);
  const [dashboard, setDashboard] = useState(emptyDashboard);
  const [toast, setToast] = useState("");

  useEffect(() => {
    let active = true;

    loadDashboard(projectId)
      .then((payload) => {
        if (!active) {
          return;
        }
        setDashboard({ ...emptyDashboard, ...payload });
        setStatus("succeeded");
        setError(null);
      })
      .catch((err) => {
        if (!active) {
          return;
        }
        setStatus("failed");
        setError(err.message);
      });

    return () => {
      active = false;
    };
  }, [projectId]);

  const refresh = async () => {
    try {
      setStatus("loading");
      const payload = await loadDashboard(projectId);
      setDashboard({ ...emptyDashboard, ...payload });
      setStatus("succeeded");
      setError(null);
    } catch (err) {
      setStatus("failed");
      setError(err.message);
    }
  };

  const submitPledge = async () => {
    try {
      setToast("");
      await pledge({
        user_id: userId,
        project_id: projectId,
        amount: Number(amount),
        reward_id: rewardId || null,
        payment_method: "card",
        actor_role: "backer",
      });
      setToast("Pledge completed successfully.");
      await refresh();
    } catch (err) {
      setToast(err.message);
    }
  };

  const progress = Number(dashboard.analytics?.progress_pct || 0);
  const conversion = Number(dashboard.analytics?.conversion_pct || 0);
  const forecast = Number(dashboard.analytics?.forecast_success_score || 0);
  const rewardItems = dashboard.rewards?.items || [];
  const updates = dashboard.updates?.items || [];
  const comments = dashboard.comments?.items || [];
  const notifications = dashboard.notifications?.items || [];

  const statusLabel = useMemo(() => {
    if (status === "loading") {
      return "loading";
    }
    if (status === "failed") {
      return "Service unavailable";
    }
    return "live";
  }, [status]);

  return (
    <div className={`app theme-${theme}`}>
      <div className="background-orb orb-a" />
      <div className="background-orb orb-b" />

      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">FundIt Crowdfunding Platform</p>
          <h1>Campaign overview</h1>
          <p className="sub">
            FundIt supports all-or-nothing and flexible campaigns with rewards, author updates, analytics, and project
            recommendations.
          </p>
          <div className="hero-badges">
            <span>All or nothing model</span>
            <span>Flexible funding</span>
            <span>Reward logistics</span>
            <span>Crowd-invest metrics</span>
          </div>
        </div>

        <div className="hero-panel">
          <label>
            Project ID
            <input value={projectId} onChange={(event) => setProjectId(event.target.value)} placeholder="PRJ-DEMO" />
          </label>
          <label>
            Backer ID
            <input value={userId} onChange={(event) => setUserId(event.target.value)} placeholder="BACK-101" />
          </label>
          <label>
            Amount
            <input type="number" value={amount} onChange={(event) => setAmount(event.target.value)} min={100} step={100} />
          </label>
          <label>
            Reward ID (optional)
            <input value={rewardId} onChange={(event) => setRewardId(event.target.value)} placeholder="RWD-STARTER" />
          </label>
          <div className="hero-actions">
            <button onClick={submitPledge}>Pledge now</button>
            <button className="ghost" onClick={() => setTheme((current) => (current === "light" ? "dark" : "light"))}>
              Theme
            </button>
          </div>
          <button className="ghost" onClick={refresh}>Refresh dashboard</button>
          <p className="status-line" role="status" aria-live="polite">Status: {statusLabel}</p>
        </div>
      </header>

      {toast ? <div className="toast-banner">{toast}</div> : null}
      {error ? <div className="error-banner" role="alert">{error}</div> : null}

      <section className="kpi-grid">
        <KpiCard
          title="Funding Progress"
          value={`${progress.toFixed(1)}%`}
          target="Target >= 100%"
          ok={progress >= 100}
        />
        <KpiCard
          title="Conversion"
          value={`${conversion.toFixed(1)}%`}
          target="Track source quality"
          ok={conversion >= 3}
        />
        <KpiCard
          title="Forecast"
          value={`${forecast.toFixed(1)} / 100`}
          target="Keep above 70"
          ok={forecast >= 70}
        />
        <KpiCard
          title="Net Raised"
          value={`${Math.round(dashboard.analytics?.net_amount || 0).toLocaleString()} RUB`}
          target="After refunds"
          ok={Number(dashboard.analytics?.net_amount || 0) > 0}
        />
      </section>

      <section className="content-grid">
        <article className="panel panel-featured">
          <div className="panel-head compact">
            <div>
              <p className="section-kicker">Campaign</p>
              <h2>{dashboard.project?.title}</h2>
            </div>
            <span className="pill">{dashboard.project?.status}</span>
          </div>
          <p className="panel-copy">{dashboard.project?.short_description}</p>
          <div className="metrics-row">
            <div>
              <strong>{Math.round(dashboard.project?.goal_amount || 0).toLocaleString()}</strong>
              <span>goal, RUB</span>
            </div>
            <div>
              <strong>{Math.round(dashboard.project?.pledged_amount || 0).toLocaleString()}</strong>
              <span>pledged, RUB</span>
            </div>
            <div>
              <strong>{dashboard.analytics?.visits || 0}</strong>
              <span>visits</span>
            </div>
            <div>
              <strong>{dashboard.analytics?.backers_count || 0}</strong>
              <span>backers</span>
            </div>
          </div>
          <TaskBoard updates={updates} />
        </article>

        <article className="panel">
          <div className="panel-head compact">
            <div>
              <p className="section-kicker">Rewards</p>
              <h2>Support tiers</h2>
            </div>
            <span className="pill accent">{rewardItems.length} tiers</span>
          </div>
          <div className="stack-list">
            {rewardItems.map((tier) => (
              <div className="stack-item" key={tier.tier_id}>
                <div>
                  <p className="stack-title">{tier.title}</p>
                  <p className="stack-sub">{tier.description}</p>
                </div>
                <button className="chip-btn" onClick={() => setRewardId(tier.tier_id)}>
                  {Math.round(tier.min_amount)} RUB
                </button>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-head compact">
            <div>
              <p className="section-kicker">Community</p>
              <h2>Recent comments</h2>
            </div>
            <span className="pill">{comments.length}</span>
          </div>
          <div className="stack-list">
            {comments.slice(-5).reverse().map((item) => (
              <div className="stack-item" key={item.comment_id}>
                <div>
                  <p className="stack-title">{item.user_id}</p>
                  <p className="stack-sub">{item.text}</p>
                </div>
                <span>{new Date(item.created_at).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-head compact">
            <div>
              <p className="section-kicker">Payments</p>
              <h2>Collection snapshot</h2>
            </div>
            <span className="pill accent">{dashboard.payments?.count || 0} tx</span>
          </div>
          <div className="analytics-grid">
            <div>
              <strong>{Math.round(dashboard.payments?.total_gross || 0).toLocaleString()}</strong>
              <span>gross</span>
            </div>
            <div>
              <strong>{Math.round(dashboard.payments?.total_fee || 0).toLocaleString()}</strong>
              <span>commission</span>
            </div>
            <div>
              <strong>{Math.round(dashboard.payments?.total_net || 0).toLocaleString()}</strong>
              <span>net</span>
            </div>
            <div>
              <strong>{dashboard.notifications?.delivered_count || 0}</strong>
              <span>delivered notices</span>
            </div>
          </div>
        </article>

        <article className="panel panel-analytics">
          <div className="panel-head compact">
            <div>
              <p className="section-kicker">Author Analytics</p>
              <h2>Portfolio report</h2>
            </div>
            <span className="pill accent">{dashboard.author_report?.projects?.length || 0} projects</span>
          </div>
          <div className="analytics-grid">
            <div>
              <strong>{Math.round(dashboard.author_report?.total_pledged || 0).toLocaleString()}</strong>
              <span>total pledged</span>
            </div>
            <div>
              <strong>{Math.round(dashboard.author_report?.total_refunds || 0).toLocaleString()}</strong>
              <span>total refunds</span>
            </div>
            <div>
              <strong>{Number(dashboard.author_report?.avg_conversion_pct || 0).toFixed(1)}%</strong>
              <span>avg conversion</span>
            </div>
            <div>
              <strong>{Number(dashboard.author_report?.avg_progress_pct || 0).toFixed(1)}%</strong>
              <span>avg progress</span>
            </div>
          </div>
          <div className="timeline-list">
            {notifications.slice(-5).reverse().map((item) => (
              <div className="stack-item" key={item.notification_id}>
                <div>
                  <p className="stack-title">{item.subject}</p>
                  <p className="stack-sub">{item.body}</p>
                </div>
                <span>{item.status}</span>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
