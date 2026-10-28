/**
 * Project - 01: Marketing Budget Optimization
 * Frontend Application Logic & Interactive AI Visualizations
 */

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

let appState = {
    overview: null,
    curveData: null,
    currentBudget: 12000000,
    currentStrategy: 'profit_maximization'
};

const formatCurrency = (val) => {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 0
    }).format(val);
};

const formatPercent = (val) => {
    return `${val > 0 ? '+' : ''}${val.toFixed(1)}%`;
};

async function initApp() {
    setupTabNavigation();
    setupSimulatorControls();
    await loadInitialData();
    await loadCurveData();
}

// ----------------- Tab Navigation -----------------
function setupTabNavigation() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const targetId = btn.getAttribute('data-tab');
            const targetPane = document.getElementById(targetId);
            if (targetPane) {
                targetPane.classList.add('active');
                // Trigger Plotly relayout to ensure proper chart dimension rendering on hidden tabs
                window.dispatchEvent(new Event('resize'));
            }
        });
    });
}

// ----------------- Simulator Controls -----------------
function setupSimulatorControls() {
    const slider = document.getElementById('budget-slider');
    const display = document.getElementById('slider-val-display');
    const tickBtns = document.querySelectorAll('.tick-btn');
    const runBtn = document.getElementById('btn-run-sim');
    const resetBtn = document.getElementById('btn-reset-sim');
    const strategyRadios = document.querySelectorAll('input[name="opt-strategy"]');
    const channelSelect = document.getElementById('curve-channel-select');

    slider.addEventListener('input', (e) => {
        const val = parseInt(e.target.value);
        appState.currentBudget = val;
        display.textContent = formatCurrency(val);
        
        tickBtns.forEach(b => {
            if (parseInt(b.getAttribute('data-val')) === val) {
                b.classList.add('active');
            } else {
                b.classList.remove('active');
            }
        });
    });

    tickBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const val = parseInt(btn.getAttribute('data-val'));
            slider.value = val;
            appState.currentBudget = val;
            display.textContent = formatCurrency(val);
            tickBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            triggerOptimization();
        });
    });

    strategyRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            appState.currentStrategy = e.target.value;
            triggerOptimization();
        });
    });

    runBtn.addEventListener('click', () => {
        triggerOptimization();
    });

    resetBtn.addEventListener('click', () => {
        slider.value = 12000000;
        appState.currentBudget = 12000000;
        appState.currentStrategy = 'profit_maximization';
        display.textContent = '$12,000,000';
        document.querySelector('input[name="opt-strategy"][value="profit_maximization"]').checked = true;
        tickBtns.forEach(b => {
            b.classList.toggle('active', b.getAttribute('data-val') === '12000000');
        });
        triggerOptimization();
    });

    if (channelSelect) {
        channelSelect.addEventListener('change', () => {
            renderResponseCurves();
        });
    }
}

// ----------------- API Calls -----------------
async function loadInitialData() {
    try {
        const res = await fetch('/api/overview');
        const data = await res.json();
        if (data.status === 'success') {
            appState.overview = data;
            renderKPIs(data.portfolio_summary, data.optimization_summary);
            renderReallocationTable(data.reallocation);
            renderEconomicsTable(data.channel_economics);
            renderAttributionTable(data.attribution);
            renderCustomerJourneys(data.customer_journeys_sample);
            renderMarginalTable(data.channel_economics);
            
            // Render Charts
            renderReallocationCharts(data.reallocation);
            renderEconomicsCharts(data.channel_economics);
            renderAttributionChart(data.attribution);
        }
    } catch (err) {
        console.error('Failed to load initial data:', err);
    }
}

async function loadCurveData() {
    try {
        const res = await fetch('/api/curve-data');
        const data = await res.json();
        if (data.status === 'success') {
            appState.curveData = data.curves;
            renderResponseCurves();
        }
    } catch (err) {
        console.error('Failed to load curve data:', err);
    }
}

async function triggerOptimization() {
    try {
        const runBtn = document.getElementById('btn-run-sim');
        runBtn.innerHTML = `<span>Optimizing SLSQP...</span>`;
        runBtn.style.opacity = '0.7';

        const res = await fetch('/api/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                total_budget: appState.currentBudget,
                strategy: appState.currentStrategy
            })
        });

        const data = await res.json();
        if (data.status === 'success') {
            appState.overview.optimization_summary = data.summary;
            appState.overview.reallocation = data.reallocation;

            renderKPIs(appState.overview.portfolio_summary, data.summary);
            renderReallocationTable(data.reallocation);
            renderReallocationCharts(data.reallocation);
            renderResponseCurves();
        }

        runBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            <span>Recompute Allocation</span>
        `;
        runBtn.style.opacity = '1';
    } catch (err) {
        console.error('Optimization error:', err);
    }
}

// ----------------- KPI Cards Rendering -----------------
function renderKPIs(portfolio, opt) {
    document.getElementById('kpi-current-spend').textContent = formatCurrency(portfolio.total_monthly_spend);
    document.getElementById('kpi-current-rev').textContent = formatCurrency(portfolio.total_monthly_revenue);
    document.getElementById('kpi-current-roas').textContent = `${portfolio.blended_roas}x ROAS`;
    
    document.getElementById('kpi-proj-rev').textContent = formatCurrency(opt.projected_total_revenue);
    document.getElementById('kpi-uplift').textContent = `+${opt.revenue_uplift_pct}% (+ ${formatCurrency(opt.revenue_uplift)}/mo)`;
    
    document.getElementById('kpi-proj-roas').textContent = `${opt.projected_blended_roas}x`;
    document.getElementById('kpi-roas-gain').textContent = `+${opt.roas_improvement.toFixed(2)}x ROAS Lift`;
    
    document.getElementById('kpi-waste').textContent = formatCurrency(portfolio.total_inefficient_spend);
    document.getElementById('kpi-waste-pct').textContent = `${portfolio.inefficient_spend_ratio_pct}% of Total Spend`;
}

// ----------------- Reallocation Table & Charts -----------------
function renderReallocationTable(realloc) {
    const tbody = document.getElementById('tbody-reallocation');
    tbody.innerHTML = '';

    realloc.forEach(item => {
        const tr = document.createElement('tr');
        
        const deltaClass = item.spend_change > 0 ? 'highlight-success' : (item.spend_change < 0 ? 'highlight-danger' : '');
        const actionPillClass = item.status.includes('Expand') ? 'action-expand' : (item.status.includes('Cut') ? 'action-cut' : 'action-maintain');

        tr.innerHTML = `
            <td><strong>${item.channel}</strong></td>
            <td><span class="badge-neutral">${item.efficiency_status}</span></td>
            <td>${formatCurrency(item.current_spend)}</td>
            <td><strong>${formatCurrency(item.recommended_spend)}</strong></td>
            <td class="${deltaClass}"><strong>${item.spend_change > 0 ? '+' : ''}${formatCurrency(item.spend_change)} (${formatPercent(item.spend_change_pct)})</strong></td>
            <td>${item.current_roas.toFixed(2)}x</td>
            <td><strong>${item.projected_roas.toFixed(2)}x</strong></td>
            <td>${formatCurrency(item.projected_revenue)}</td>
            <td><span class="action-pill ${actionPillClass}">${item.status}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderReallocationCharts(realloc) {
    const channels = realloc.map(d => d.channel);
    const currSpend = realloc.map(d => d.current_spend);
    const optSpend = realloc.map(d => d.recommended_spend);
    const revDelta = realloc.map(d => d.revenue_change);

    const trace1 = {
        y: channels,
        x: currSpend,
        name: 'Current Spend',
        type: 'bar',
        orientation: 'h',
        marker: { color: '#64748B' }
    };

    const trace2 = {
        y: channels,
        x: optSpend,
        name: 'AI Recommended',
        type: 'bar',
        orientation: 'h',
        marker: { color: '#4F46E5' }
    };

    const layout1 = {
        barmode: 'group',
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { family: 'Inter', color: '#94A3B8', size: 11 },
        margin: { l: 140, r: 20, t: 20, b: 40 },
        legend: { orientation: 'h', y: 1.15, x: 0.1 },
        xaxis: { gridcolor: 'rgba(255,255,255,0.05)', tickprefix: '$' },
        yaxis: { automargin: true }
    };

    Plotly.newPlot('chart-reallocation', [trace1, trace2], layout1, { responsive: true, displayModeBar: false });

    // Revenue Uplift Bar Chart
    const barColors = revDelta.map(v => v >= 0 ? '#10B981' : '#EF4444');
    const traceUplift = {
        x: channels,
        y: revDelta,
        type: 'bar',
        marker: { color: barColors }
    };

    const layout2 = {
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { family: 'Inter', color: '#94A3B8', size: 11 },
        margin: { l: 50, r: 20, t: 20, b: 80 },
        xaxis: { tickangle: -25, gridcolor: 'transparent' },
        yaxis: { gridcolor: 'rgba(255,255,255,0.05)', tickprefix: '$' }
    };

    Plotly.newPlot('chart-revenue-uplift', [traceUplift], layout2, { responsive: true, displayModeBar: false });
}

// ----------------- Unit Economics & Diagnostics -----------------
function renderEconomicsTable(econ) {
    const tbody = document.getElementById('tbody-economics');
    tbody.innerHTML = '';

    econ.forEach(row => {
        const tr = document.createElement('tr');
        const ratioColor = row.ltv_cac_ratio >= 3.0 ? 'highlight-success' : (row.ltv_cac_ratio >= 2.0 ? 'highlight-cyan' : 'highlight-danger');
        const statusBadge = row.efficiency_status === 'Star Performer' ? 'badge-success' : (row.efficiency_status === 'Profitable Growth' ? 'badge-cyan' : 'badge-danger');

        tr.innerHTML = `
            <td><strong>${row.channel}</strong></td>
            <td>$${row.cac.toFixed(1)}</td>
            <td><strong>$${row.avg_ltv.toFixed(0)}</strong></td>
            <td class="${ratioColor}"><strong>${row.ltv_cac_ratio.toFixed(2)}x</strong></td>
            <td>${row.profitable_customer_pct}%</td>
            <td>${row.churn_rate_pct}%</td>
            <td>${row.avg_payback_months} mo</td>
            <td><strong class="highlight-danger">${formatCurrency(row.inefficient_spend)}</strong></td>
            <td><small class="text-muted">${row.inefficiency_root_cause}</small></td>
            <td><span class="${statusBadge}">${row.efficiency_status}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderEconomicsCharts(econ) {
    const channels = econ.map(d => d.channel);
    const ratios = econ.map(d => d.ltv_cac_ratio);
    const barColors = ratios.map(r => r >= 3.0 ? '#10B981' : (r >= 2.0 ? '#06B6D4' : '#EF4444'));

    const trace1 = {
        x: channels,
        y: ratios,
        type: 'bar',
        marker: { color: barColors }
    };

    const layout1 = {
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { family: 'Inter', color: '#94A3B8', size: 11 },
        margin: { l: 40, r: 20, t: 20, b: 80 },
        shapes: [
            {
                type: 'line',
                x0: -0.5,
                x1: channels.length - 0.5,
                y0: 3.0,
                y1: 3.0,
                line: { color: '#10B981', width: 1.5, dash: 'dash' }
            },
            {
                type: 'line',
                x0: -0.5,
                x1: channels.length - 0.5,
                y0: 1.5,
                y1: 1.5,
                line: { color: '#EF4444', width: 1.5, dash: 'dot' }
            }
        ],
        xaxis: { tickangle: -25 },
        yaxis: { gridcolor: 'rgba(255,255,255,0.05)', title: 'LTV : CAC' }
    };

    Plotly.newPlot('chart-ltv-cac', [trace1], layout1, { responsive: true, displayModeBar: false });

    // Payback vs Churn Bubble
    const trace2 = {
        x: econ.map(d => d.avg_payback_months),
        y: econ.map(d => d.churn_rate_pct),
        text: channels,
        mode: 'markers+text',
        textposition: 'top center',
        marker: {
            size: econ.map(d => Math.max(12, d.current_spend / 6000)),
            color: econ.map(d => d.ltv_cac_ratio < 1.8 ? '#EF4444' : '#6366F1'),
            opacity: 0.8
        }
    };

    const layout2 = {
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { family: 'Inter', color: '#94A3B8', size: 11 },
        margin: { l: 50, r: 20, t: 20, b: 50 },
        xaxis: { title: 'Payback Period (Months)', gridcolor: 'rgba(255,255,255,0.05)' },
        yaxis: { title: 'Customer Churn Rate (%)', gridcolor: 'rgba(255,255,255,0.05)' }
    };

    Plotly.newPlot('chart-churn-payback', [trace2], layout2, { responsive: true, displayModeBar: false });
}

// ----------------- Multi-Touch Attribution -----------------
function renderAttributionTable(attr) {
    const tbody = document.getElementById('tbody-attribution');
    tbody.innerHTML = '';

    attr.forEach(row => {
        const tr = document.createElement('tr');
        const diff = row.markov_data_driven_pct - row.last_touch_pct;
        const biasDesc = diff > 2.0 
            ? '<span class="badge-success">Undervalued by Last-Touch (+ discovery)</span>' 
            : (diff < -2.0 ? '<span class="badge-danger">Over-credited by Last-Touch</span>' : '<span class="badge-neutral">Balanced</span>');

        tr.innerHTML = `
            <td><strong>${row.channel}</strong></td>
            <td>${row.first_touch_pct}%</td>
            <td>${row.last_touch_pct}%</td>
            <td>${row.linear_pct}%</td>
            <td><strong>${row.markov_data_driven_pct}%</strong></td>
            <td>${biasDesc}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderAttributionChart(attr) {
    const channels = attr.map(d => d.channel);

    const traceLast = {
        x: channels,
        y: attr.map(d => d.last_touch_pct),
        name: 'Last-Touch %',
        type: 'bar',
        marker: { color: '#64748B' }
    };

    const traceFirst = {
        x: channels,
        y: attr.map(d => d.first_touch_pct),
        name: 'First-Touch %',
        type: 'bar',
        marker: { color: '#06B6D4' }
    };

    const traceMarkov = {
        x: channels,
        y: attr.map(d => d.markov_data_driven_pct),
        name: 'Markov Data-Driven %',
        type: 'bar',
        marker: { color: '#6366F1' }
    };

    const layout = {
        barmode: 'group',
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { family: 'Inter', color: '#94A3B8', size: 11 },
        margin: { l: 40, r: 20, t: 30, b: 80 },
        legend: { orientation: 'h', y: 1.12, x: 0.15 },
        xaxis: { tickangle: -25 },
        yaxis: { gridcolor: 'rgba(255,255,255,0.05)', title: 'Revenue Share (%)' }
    };

    Plotly.newPlot('chart-attribution-comp', [traceLast, traceFirst, traceMarkov], layout, { responsive: true, displayModeBar: false });
}

// ----------------- Response Curves -----------------
function renderResponseCurves() {
    if (!appState.curveData) return;

    const select = document.getElementById('curve-channel-select');
    const selectedChannel = select ? select.value : 'ALL';
    const traces = [];

    const reallocMap = {};
    if (appState.overview && appState.overview.reallocation) {
        appState.overview.reallocation.forEach(r => {
            reallocMap[r.channel] = r;
        });
    }

    const channelKeys = selectedChannel === 'ALL' ? Object.keys(appState.curveData) : [selectedChannel];

    const colorPalette = [
        '#6366F1', '#06B6D4', '#10B981', '#F59E0B', '#EC4899', '#8B5CF6', '#14B8A6', '#F43F5E'
    ];

    channelKeys.forEach((ch, idx) => {
        const c = appState.curveData[ch];
        const color = colorPalette[idx % colorPalette.length];

        // Curve line
        traces.push({
            x: c.spends,
            y: c.revenues,
            name: `${ch} (Curve)`,
            type: 'scatter',
            mode: 'lines',
            line: { color: color, width: 2.5 }
        });

        // Current Operating Point
        traces.push({
            x: [c.current_spend],
            y: [c.current_revenue],
            name: `${ch} (Current: $${Math.round(c.current_spend/1000)}k)`,
            type: 'scatter',
            mode: 'markers',
            marker: { color: '#94A3B8', size: 9, symbol: 'circle' },
            showlegend: selectedChannel !== 'ALL'
        });

        // Recommended Operating Point
        if (reallocMap[ch]) {
            const optS = reallocMap[ch].recommended_spend;
            const optR = reallocMap[ch].projected_revenue;
            traces.push({
                x: [optS],
                y: [optR],
                name: `${ch} (Optimal: $${Math.round(optS/1000)}k)`,
                type: 'scatter',
                mode: 'markers',
                marker: { color: '#10B981', size: 11, symbol: 'star' },
                showlegend: selectedChannel !== 'ALL'
            });
        }
    });

    const layout = {
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { family: 'Inter', color: '#94A3B8', size: 11 },
        margin: { l: 60, r: 20, t: 30, b: 50 },
        legend: { orientation: 'h', y: 1.15, x: 0 },
        xaxis: { title: 'Monthly Spend ($)', gridcolor: 'rgba(255,255,255,0.05)', tickprefix: '$' },
        yaxis: { title: 'Generated Revenue ($)', gridcolor: 'rgba(255,255,255,0.05)', tickprefix: '$' }
    };

    Plotly.newPlot('chart-response-curves', traces, layout, { responsive: true, displayModeBar: false });
}

function renderMarginalTable(econ) {
    const tbody = document.getElementById('tbody-marginal');
    tbody.innerHTML = '';

    econ.forEach(row => {
        const tr = document.createElement('tr');
        const mRoas = row.marginal_roas || (row.roas * 0.85);
        const stageBadge = mRoas >= 2.0 ? 'badge-success' : (mRoas >= 1.0 ? 'badge-cyan' : 'badge-danger');
        const reco = mRoas >= 2.0 ? 'Aggressively Scale spend' : (mRoas >= 1.0 ? 'Maintain near inflection point' : 'Reduce spend to escape diminishing bleed');

        tr.innerHTML = `
            <td><strong>${row.channel}</strong></td>
            <td>${formatCurrency(row.current_spend)}</td>
            <td>${row.roas.toFixed(2)}x</td>
            <td><strong>${mRoas.toFixed(3)}x</strong></td>
            <td><span class="${stageBadge}">${row.saturation_stage || (mRoas < 1.0 ? 'Diminishing Bleed' : 'Optimal Band')}</span></td>
            <td><small>${reco}</small></td>
        `;
        tbody.appendChild(tr);
    });
}

// ----------------- Customer Journeys Sample -----------------
function renderCustomerJourneys(journeys) {
    const tbody = document.getElementById('tbody-journeys');
    tbody.innerHTML = '';

    journeys.forEach(j => {
        const tr = document.createElement('tr');
        const profitClass = j.is_profitable ? 'highlight-success' : 'highlight-danger';
        const statusBadge = j.churned ? '<span class="badge-danger">Churned</span>' : '<span class="badge-success">Retained</span>';
        const hid = j.household_id || j.customer_id;
        const brand = j.brand_category || 'Tide & Downy (Fabric Care)';

        tr.innerHTML = `
            <td><code>${hid}</code></td>
            <td><span class="badge-neutral">${brand}</span></td>
            <td>${j.first_touch}</td>
            <td><strong>${j.last_touch}</strong></td>
            <td><small>${j.touchpoints_path}</small></td>
            <td>${j.num_touchpoints}</td>
            <td>$${j.ltv.toFixed(0)}</td>
            <td>$${j.acquisition_cost.toFixed(0)}</td>
            <td class="${profitClass}"><strong>$${j.net_profit.toFixed(0)}</strong></td>
            <td>${j.payback_months} mo</td>
            <td>${statusBadge}</td>
        `;
        tbody.appendChild(tr);
    });
}
