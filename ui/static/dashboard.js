const API_BASE = '/api';

// --- Command Registry ---
const COMMANDS = [
    {
        id: 'view-market',
        label: '시장 상황 보기',
        description: 'Market 탭으로 이동',
        shortcut: 'Alt+1',
        global: true,
        action: () => window.activateView && window.activateView('market')
    },
    {
        id: 'view-strategy',
        label: '전략 및 신호 보기',
        description: 'Strategy 탭으로 이동',
        shortcut: 'Alt+2',
        global: true,
        action: () => window.activateView && window.activateView('strategy')
    },
    {
        id: 'view-orders',
        label: '오늘 주문 내역 보기',
        description: 'Strategy 탭의 주문 요약 패널로 이동',
        shortcut: '',
        global: true,
        action: () => {
            if (window.activateView) window.activateView('strategy');
            const el = document.getElementById('strategy-orders-card');
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    },
    {
        id: 'view-simulation',
        label: '시뮬레이션 결과 보기',
        description: 'Simulation 탭으로 이동',
        shortcut: 'Alt+3',
        global: true,
        action: () => window.activateView && window.activateView('simulation')
    },
    {
        id: 'view-portfolio',
        label: '포트폴리오 요약 보기',
        description: 'Portfolio 탭 및 포지션 표로 스크롤',
        shortcut: 'Alt+4',
        global: true,
        action: () => {
            if (window.activateView) window.activateView('portfolio');
            const el = document.getElementById('portfolio-positions');
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    },
    {
        id: 'view-research',
        label: '연구 및 검증 보기',
        description: 'Research 탭으로 이동',
        shortcut: 'Alt+5',
        global: true,
        action: () => window.activateView && window.activateView('research')
    },
    {
        id: 'view-system',
        label: '시스템 상태 및 단축키 보기',
        description: 'System 탭 + 단축키 안내 카드로 이동',
        shortcut: 'Alt+6',
        global: true,
        action: () => {
            if (window.activateView) window.activateView('system');
            const el = document.getElementById('shortcut-help-card');
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    },
    {
        id: 'refresh-operator',
        label: '데이터 새로고침',
        description: 'OPERATOR VIEW 및 시세 데이터 강제 새로고침',
        shortcut: '',
        global: false,
        action: () => window.updateOperatorView && window.updateOperatorView()
    }
];

// --- Navigation ---
function activateView(viewName) {
    const sidebarItems = document.querySelectorAll('[data-view-target]');
    const viewSections = document.querySelectorAll('.view-section');

    sidebarItems.forEach(item => {
        const target = item.getAttribute('data-view-target');
        if (target === viewName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    viewSections.forEach(section => {
        const sectionView = section.dataset.view;
        if (sectionView === viewName) {
            section.classList.remove('hidden');
        } else {
            section.classList.add('hidden');
        }
    });

    const loaders = {
        market: () => { window.updateOperatorView(); },
        strategy: () => { window.updateOperatorView(); }, // Strategy also needs live data
        simulation: () => { window.loadSimulationToday(); window.loadSimulationComparison(); },
        portfolio: () => { window.updateOperatorView(); }, // Portfolio needs live data
        system: window.loadSystemHealth,
        'ai-core': window.loadAiCoreSummary,
        research: () => { }
    };

    // Call loader
    const loader = loaders[viewName];
    if (typeof loader === 'function') {
        try {
            loader();
        } catch (err) {
            console.error('[GARAM] View loader error for', viewName, err);
        }
    }
}

function initNavigation() {
    const sidebarItems = document.querySelectorAll('[data-view-target]');
    const viewSections = document.querySelectorAll('.view-section');

    if (!sidebarItems.length || !viewSections.length) {
        console.warn('[GARAM] Navigation init: no sidebarItems or viewSections found');
        return;
    }

    // Click events
    sidebarItems.forEach(item => {
        item.addEventListener('click', () => {
            const target = item.getAttribute('data-view-target');
            if (target) {
                activateView(target);
            }
        });
    });

    // Expose activateView globally for command palette & shortcuts
    window.activateView = activateView;

    // Initial view
    activateView('market');

    // Auto Refresh Operator View (Global)
    setInterval(window.updateOperatorView, 5000);
    window.updateOperatorView(); // Initial call
}

// --- Operator View Logic ---

window.updateOperatorView = async function () {
    console.log("Updating Operator View...");

    // 1. Fetch Intent (Regime, Mode, Plan)
    try {
        const resp = await fetch("/api/live/intent");
        const intent = await resp.json();

        // Global Summary
        updateText('op-regime', intent.market_regime || "알 수 없음");
        updateText('op-intent', intent.intent_summary || "활성 계획 없음");

        // Strategy Tab
        updateText('strategy-daily-plan-text', intent.intent_summary || "-");

        // Market Tab
        updateText('regime-main', intent.market_regime || "-");
        updateText('regime-micro', intent.micro_regime || "-");
        updateText('regime-update-time', "최종 업데이트: " + new Date().toLocaleTimeString());

    } catch (e) { console.error("Intent fetch error:", e); }

    // 1.5 Fetch Strategy Status
    try {
        const resp = await fetch("/api/live/status");
        const status = await resp.json();

        updateText('strat-profile', status.profile || "-");
        updateText('strat-active-count', status.active_strategies ? status.active_strategies.length : 0);

        const allocList = document.getElementById('strat-allocations-list');
        if (allocList && status.allocations) {
            allocList.innerHTML = '';
            for (const [sym, weight] of Object.entries(status.allocations)) {
                const li = document.createElement('li');
                li.textContent = `${sym}: ${(weight * 100).toFixed(1)}%`;
                allocList.appendChild(li);
            }
        }
    } catch (e) { console.error("Status fetch error:", e); }

    // 2. Fetch Portfolio (Positions, Equity)
    try {
        const resp = await fetch("/api/live/portfolio");
        const pf = await resp.json();

        // Global Summary (HUD)
        if (pf.positions) updateText('op-positions', pf.positions.length);

        // HUD Equity & Investment Ratio
        if (pf.total_equity !== undefined) {
            updateText('hud-equity', formatCurrency(pf.total_equity));

            // Calculate Invested Ratio
            const nav = parseFloat(pf.total_equity) || 1;
            const cash = parseFloat(pf.cash_balance) || 0;
            const invested = nav - cash;
            const ratio = (invested / nav) * 100;

            const bar = document.getElementById('hud-invest-bar');
            const ratioText = document.getElementById('hud-invest-ratio-text');
            if (bar) bar.style.width = Math.min(Math.max(ratio, 0), 100) + "%";
            if (ratioText) ratioText.textContent = `${ratio.toFixed(1)}% Invested`;
        }


        // Portfolio Tab - Snapshot
        updateText('snap-equity', formatCurrency(pf.total_equity));
        updateText('snap-cash', formatCurrency(pf.cash_balance));

        // Portfolio Tab - Table
        const tableBody = document.querySelector('#positions-table tbody');
        if (tableBody && pf.positions) {
            tableBody.innerHTML = '';
            pf.positions.forEach(pos => {
                const tr = document.createElement('tr');
                tr.className = 'interactive';
                tr.onclick = () => showDetailModal(pos.name, pos);

                // Color for PnL
                const pnlClass = (pos.pnl > 0) ? 'up' : (pos.pnl < 0 ? 'down' : '');
                const pnlSign = (pos.pnl > 0) ? '+' : '';

                tr.innerHTML = `
                    <td>
                        <div class="symbol-info">
                            <span class="symbol-code">${pos.symbol}</span>
                            <span class="symbol-name">${pos.name}</span>
                        </div>
                    </td>
                    <td>
                        <div class="price-info">
                            <span class="main-price">${formatCurrency(pos.entry_price)}</span>
                            <span class="sub-info">${pos.entry_date}</span>
                        </div>
                    </td>
                    <td>
                        <div class="price-info">
                            <span class="main-price">${formatCurrency(pos.price)}</span>
                            <span class="sub-info">Qty: ${pos.qty}</span>
                        </div>
                    </td>
                    <td>
                        <div class="val-info">
                            <span class="main-val">${formatCurrency(pos.value)}</span>
                            <span class="sub-info">${(pos.weight * 100).toFixed(1)}%</span>
                        </div>
                    </td>
                    <td>
                        <div class="pnl-info ${pnlClass}">
                            <span class="pnl-val">${pnlSign}${formatCurrency(pos.pnl)}</span>
                            <span class="pnl-pct">(${pnlSign}${pos.pnl_pct.toFixed(2)}%)</span>
                        </div>
                    </td>
                    <td>
                        <div class="sparkline-container" id="spark-${pos.symbol}"></div>
                    </td>
                `;
                tableBody.appendChild(tr);

                // Render Sparkline if history exists
                if (pos.history && pos.history.length > 0) {
                    // Determine color based on trend (last vs first)
                    const first = pos.history[0];
                    const last = pos.history[pos.history.length - 1];
                    const color = last >= first ? '#f87171' : '#3b82f6'; // Red up, Blue down
                    renderSparkline(`spark-${pos.symbol}`, pos.history, color);
                } else {
                    const container = document.getElementById(`spark-${pos.symbol}`);
                    if (container) container.innerHTML = '<span class="placeholder-graph">데이터 없음</span>';
                }
            });
        }

    } catch (e) { console.error("Portfolio fetch error:", e); }

    // 3. Fetch Performance (PnL, Chart)
    try {
        const resp = await fetch("/api/live/performance");
        const perf = await resp.json();

        // Global Summary (Today PnL - Placeholder logic as we need daily start equity)
        // For now, assume 0 if not calculated
        updateText('op-pnl', "₩0 (0.00%)");
        updateText('snap-return', "0.00%");

        // Chart
        if (perf.equity_curve && perf.equity_curve.length > 0) {
            renderEquityChart(perf.equity_curve);
        }

    } catch (e) { console.error("Performance fetch error:", e); }

    // 4. Fetch Market Indices
    await updateMarketIndices();

    // 5. Fetch Top 10 Real-time Quotes
    await updateTop10();

    // 6. Fetch Active Signals
    await updateSignals();

    // 7. Fetch Today Orders
    await updateOrdersPanel();

    // 8. Fetch Kiwoom Status
    await updateKiwoomStatus();

    // 9. Update PnL Delta
    updatePnlDelta();
}

async function updatePnlDelta() {
    try {
        const resp = await fetch("/api/live/status");
        const data = await resp.json();

        const deltaDaily = data.pnl_delta_daily || 0;
        const deltaDailyPct = data.pnl_delta_daily_pct || 0;

        const el = document.getElementById('op-pnl-delta');
        if (el) {
            const sign = deltaDaily > 0 ? '+' : '';
            const color = deltaDaily > 0 ? '#4ade80' : (deltaDaily < 0 ? '#f87171' : '#aaa');
            el.style.color = color;
            el.textContent = `(Inc: ${sign}${formatCurrency(deltaDaily)})`;
        }
    } catch (e) {
        console.error("PnL Delta fetch error", e);
    }
}

// --- Simulation Comparison Logic ---
window.loadSimulationComparison = async function () {
    console.log("Loading Simulation Comparison...");
    try {
        const resp = await fetch("/api/simulation/comparison");
        const data = await resp.json();

        if (!data.dates || data.dates.length === 0) return;

        renderComparisonChart(data);

    } catch (e) {
        console.error("Comparison load error:", e);
    }
};

let comparisonChartInstance = null;

function renderComparisonChart(data) {
    const ctx = document.getElementById('simComparisonChart');
    if (!ctx) return;

    // Simplify timestamps
    const labels = data.dates.map(d => d.split(' ')[0]);

    // Datasets
    const datasets = [
        {
            label: '통합 엔진 (Blended)',
            data: data.blended,
            borderColor: '#00ff88', // Green
            borderWidth: 2,
            tension: 0.1,
            pointRadius: 0
        },
        {
            label: '엔진 1 (레거시)',
            data: data.engine1,
            borderColor: '#94a3b8', // Grey
            borderWidth: 1,
            borderDash: [5, 5],
            tension: 0.1,
            pointRadius: 0
        },
        {
            label: '엔진 2 (어드밴스드)',
            data: data.engine2,
            borderColor: '#3b82f6', // Blue
            borderWidth: 2,
            tension: 0.1,
            pointRadius: 0
        },
        {
            label: '시장 (KOSPI)',
            data: data.kospi || [],
            borderColor: '#ef4444', // Red
            borderWidth: 1,
            borderDash: [2, 2],
            tension: 0.1,
            pointRadius: 0
        }
    ];

    if (comparisonChartInstance) {
        comparisonChartInstance.data.labels = labels;
        comparisonChartInstance.data.datasets = datasets;
        comparisonChartInstance.update();
    } else {
        comparisonChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            callback: function (value) {
                                return (value / 1000000).toFixed(0) + 'M';
                            },
                            color: '#cbd5e1'
                        }
                    },
                    x: {
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#cbd5e1',
                            maxTicksLimit: 12
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#cbd5e1'
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function (context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += new Intl.NumberFormat('ko-KR', { style: 'currency', currency: 'KRW' }).format(context.parsed.y);
                                }
                                return label;
                            }
                        }
                    }
                }
            }
        });
    }
}

// --- Kiwoom Status Logic ---
async function updateKiwoomStatus() {
    try {
        const resp = await fetch("/api/system/kiwoom_status");
        const data = await resp.json();

        const dot = document.getElementById('kiwoom-status-dot');
        const text = document.getElementById('kiwoom-status-text');
        const btn = document.getElementById('kiwoom-toggle-btn');

        if (dot && text) {
            if (data.connected) {
                dot.className = 'status-dot online';
                text.textContent = '키움: 연결됨 (Connected)';
                if (btn) {
                    btn.textContent = "연결 끊기 (Logout)";
                    btn.style.background = "#ef4444"; // Red
                    btn.dataset.action = "stop";
                }
            } else {
                dot.className = 'status-dot offline';
                text.textContent = '키움: 연결 끊김 (Stopped)';
                if (btn) {
                    btn.textContent = "연결 시작 (Connect)";
                    btn.style.background = "#10b981"; // Green
                    btn.dataset.action = "start";
                }
            }
        }
    } catch (e) { console.error("Kiwoom status fetch error:", e); }
}

window.toggleKiwoomConnection = async function () {
    const btn = document.getElementById('kiwoom-toggle-btn');
    if (!btn) return;

    const action = btn.dataset.action;
    const url = action === 'stop' ? '/api/system/kiwoom/stop' : '/api/system/kiwoom/start';

    if (!confirm(action === 'stop' ? "연결을 끊고 자동 재접속을 중지하시겠습니까?" : "키움 모듈을 다시 시작하시겠습니까?")) return;

    try {
        btn.disabled = true;
        btn.textContent = "처리 중...";

        await fetch(url, { method: 'POST' });

        // Wait a bit for server/watchdog to react
        setTimeout(() => {
            btn.disabled = false;
            updateKiwoomStatus();
        }, 3000);

    } catch (e) {
        alert("Action failed: " + e);
        btn.disabled = false;
    }
};

// --- Orders Logic ---
async function updateOrdersPanel() {
    try {
        const resp = await fetch("/api/live/orders");
        const data = await resp.json();

        // Update HUD Orders Count
        const count = data.orders ? data.orders.length : 0;
        const hudCount = document.getElementById('hud-orders-count');
        if (hudCount) hudCount.textContent = count;

        const tableBody = document.querySelector('#orders-table tbody');
        const placeholder = document.getElementById('orders-summary-placeholder');
        if (!tableBody) return;

        if (data.orders && data.orders.length > 0) {
            if (placeholder) placeholder.style.display = 'none';
            tableBody.innerHTML = '';

            data.orders.forEach(order => {
                const tr = document.createElement('tr');
                tr.className = 'interactive';

                // Display Name Logic: Prioritize Name
                // If name is available and not just the code again, use it.
                // If the name IS the code (from CSV), we display just that.
                const displayName = (order.name && order.name !== order.symbol) ? order.name : order.symbol;

                tr.onclick = () => showDetailModal(displayName + ' 주문 상세', order);

                const type = order.action || order.signal || '-';
                const actionClass = type === 'BUY' ? 'up' : (type === 'SELL' ? 'down' : '');

                tr.innerHTML = `
                    <td>${order.time || '-'}</td>
                    <td>
                        <div class="symbol-info">
                            <span class="symbol-name" style="font-weight:600; color:#f1f5f9;">${displayName}</span>
                            ${(displayName !== order.symbol) ? `<span class="symbol-code-small" style="font-size:0.75em; color:#64748b; margin-left:6px;">${order.symbol}</span>` : ''}
                        </div>
                    </td>
                    <td class="${actionClass}">${type}</td>
                    <td>${order.qty}</td>
                    <td>${formatCurrency(order.price)}</td>
                    <td>${order.reason || '-'}</td>
                `;
                tableBody.appendChild(tr);
            });
        } else {
            if (placeholder) {
                placeholder.style.display = 'block';
                placeholder.textContent = "오늘 체결된 주문이 없습니다.";
            }
            tableBody.innerHTML = '';
        }
    } catch (e) { console.error("Orders fetch error:", e); }
}

// --- Market Indices Logic ---
async function updateMarketIndices() {
    try {
        const resp = await fetch("/api/market/indices");
        const data = await resp.json();

        if (data.kospi) updateIndexCard('kospi', data.kospi);
        if (data.kosdaq) updateIndexCard('kosdaq', data.kosdaq);

    } catch (e) { console.error("Indices fetch error:", e); }
}

function updateIndexCard(type, data) {
    const container = document.getElementById(`${type}-index`);
    if (!container) return;

    // Update Price & Change
    const priceEl = container.querySelector('.index-price');
    const changeValEl = container.querySelector('.change-value');
    const changePctEl = container.querySelector('.change-pct');

    if (priceEl) priceEl.textContent = data.price.toLocaleString();

    if (changeValEl && changePctEl) {
        const change = data.change;
        const pct = data.change_pct;
        const sign = change > 0 ? '+' : '';

        changeValEl.textContent = `${sign}${change}`;
        changePctEl.textContent = `(${sign}${pct}%)`;

        // Color classes
        const changeContainer = container.querySelector('.index-change');
        if (changeContainer) {
            changeContainer.classList.remove('up', 'down');
            if (change > 0) changeContainer.classList.add('up');
            if (change < 0) changeContainer.classList.add('down');
        }

        // HUD Trend Update (added)
        if (type === 'kospi') {
            const hudTrend = document.getElementById('hud-kospi-trend');
            if (hudTrend) {
                hudTrend.innerHTML = `<span class="${change > 0 ? 'up' : 'down'}">${sign}${pct}%</span>`;
            }
        }
    }

    // Render Sparkline
    renderSparkline(`${type}-chart`, data.history, type === 'kospi' ? '#3b82f6' : '#a855f7');
}

// --- Dynamic Command Injection ---
function injectStockCommands(targets) {
    // Remove old stock commands first to prevent info duplication
    const coreCommands = COMMANDS.filter(c => !c.isDynamic);

    const stockCommands = targets.map(t => ({
        id: `stock-${t.symbol}`,
        label: `${t.name} (${t.symbol})`,
        description: `현재가: ${formatCurrency(t.price)} (${t.change}%)`,
        shortcut: 'Stock',
        global: true,
        isDynamic: true, // Marker
        action: () => showDetailModal(t.name, t)
    }));

    // Rebuild global COMMANDS
    // Clear existing dynamic commands from COMMANDS array
    for (let i = COMMANDS.length - 1; i >= 0; i--) {
        if (COMMANDS[i].isDynamic) {
            COMMANDS.splice(i, 1);
        }
    }

    // Push new ones
    stockCommands.forEach(c => COMMANDS.push(c));
}

const sparklineInstances = {};

function renderSparkline(containerId, data, color) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Create canvas if not exists
    let canvas = container.querySelector('canvas');
    if (!canvas) {
        canvas = document.createElement('canvas');
        container.appendChild(canvas);
    }

    const ctx = canvas.getContext('2d');

    if (sparklineInstances[containerId]) {
        sparklineInstances[containerId].data.datasets[0].data = data;
        sparklineInstances[containerId].update();
    } else {
        sparklineInstances[containerId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map((_, i) => i),
                datasets: [{
                    data: data,
                    borderColor: color,
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { enabled: false } },
                scales: {
                    x: { display: false },
                    y: { display: false }
                },
                layout: { padding: 0 }
            }
        });
    }
}

// --- Command Palette Logic ---
function isInputFocused() {
    const active = document.activeElement;
    if (!active) return false;
    const tag = active.tagName.toLowerCase();
    return tag === 'input' || tag === 'textarea' || active.isContentEditable;
}

let commandState = {
    open: false,
    filtered: COMMANDS.slice(),
    activeIndex: 0
};

function initCommandPalette() {
    const palette = document.getElementById('command-palette');
    const backdrop = document.getElementById('command-backdrop');
    const input = document.getElementById('command-input');
    const list = document.getElementById('command-list');

    if (!palette || !backdrop || !input || !list) {
        console.warn('[GARAM] Command palette DOM not found');
        return;
    }

    function renderList() {
        list.innerHTML = '';
        if (!commandState.filtered.length) {
            const empty = document.createElement('div');
            empty.className = 'command-item';
            empty.innerHTML = '<div class="command-item-main"><div class="command-item-title">결과 없음</div><div class="command-item-desc">검색어를 바꾸거나 줄여보세요.</div></div>';
            list.appendChild(empty);
            return;
        }
        commandState.filtered.forEach((cmd, idx) => {
            const item = document.createElement('div');
            item.className = 'command-item' + (idx === commandState.activeIndex ? ' active' : '');
            item.dataset.index = idx;
            item.innerHTML = `
                <div class="command-item-main">
                    <div class="command-item-title">${cmd.label}</div>
                    <div class="command-item-desc">${cmd.description || ''}</div>
                </div>
                <div class="command-item-shortcut">${cmd.shortcut || ''}</div>
            `;
            item.addEventListener('click', () => executeCommand(idx));
            list.appendChild(item);
        });
    }

    function openPalette() {
        commandState.filtered = COMMANDS.slice();
        commandState.activeIndex = 0;
        palette.classList.remove('hidden');
        backdrop.classList.remove('hidden');
        commandState.open = true;
        renderList();
        input.value = '';
        setTimeout(() => input.focus(), 10);
    }

    function closePalette() {
        palette.classList.add('hidden');
        backdrop.classList.add('hidden');
        commandState.open = false;
    }

    function executeCommand(indexInFiltered) {
        const cmd = commandState.filtered[indexInFiltered];
        if (!cmd) return;
        try {
            if (typeof cmd.action === 'function') cmd.action();
        } catch (e) {
            console.error('[GARAM] Command execute error', cmd.id, e);
        }
        closePalette();
    }

    function filterCommands(term) {
        const q = term.trim().toLowerCase();
        if (!q) {
            commandState.filtered = COMMANDS.slice();
        } else {
            commandState.filtered = COMMANDS.filter(c => {
                return (
                    c.label.toLowerCase().includes(q) ||
                    (c.description && c.description.toLowerCase().includes(q)) ||
                    (c.id && c.id.toLowerCase().includes(q))
                );
            });
        }
        commandState.activeIndex = 0;
        renderList();
    }

    // Expose globally
    window.openCommandPalette = openPalette;
    window.closeCommandPalette = closePalette;

    input.addEventListener('input', (e) => {
        filterCommands(e.target.value || '');
    });

    input.addEventListener('keydown', (e) => {
        if (!commandState.open) return;
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (commandState.filtered.length) {
                commandState.activeIndex = (commandState.activeIndex + 1) % commandState.filtered.length;
                renderList();
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (commandState.filtered.length) {
                commandState.activeIndex =
                    (commandState.activeIndex - 1 + commandState.filtered.length) % commandState.filtered.length;
                renderList();
            }
        } else if (e.key === 'Enter') {
            e.preventDefault();
            executeCommand(commandState.activeIndex);
        } else if (e.key === 'Escape') {
            e.preventDefault();
            closePalette();
        }
    });

    backdrop.addEventListener('click', () => {
        closePalette();
    });
}

function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
        const ctrlOrCmd = isMac ? e.metaKey : e.ctrlKey;

        // 1) Command Palette: Ctrl/⌘ + K
        if (ctrlOrCmd && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            if (window.openCommandPalette) {
                window.openCommandPalette();
            }
            return;
        }

        // 2) Escape: Close Palette
        if (e.key === 'Escape') {
            if (window.closeCommandPalette) {
                window.closeCommandPalette();
            }
            return;
        }

        // 3) Shortcut Help: Shift + ? (or Shift + /)
        if ((e.key === '?' || (e.key === '/' && e.shiftKey)) && !ctrlOrCmd) {
            e.preventDefault();
            if (window.activateView) window.activateView('system');
            const el = document.getElementById('shortcut-help-card');
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            return;
        }

        // 4) View Switching: Alt + Number (only if input not focused)
        if (e.altKey && !ctrlOrCmd && !isInputFocused()) {
            switch (e.key) {
                case '1':
                    window.activateView && window.activateView('market');
                    break;
                case '2':
                    window.activateView && window.activateView('strategy');
                    break;
                case '3':
                    window.activateView && window.activateView('simulation');
                    break;
                case '4':
                    window.activateView && window.activateView('portfolio');
                    break;
                case '5':
                    window.activateView && window.activateView('research');
                    break;
                case '6':
                    window.activateView && window.activateView('system');
                    break;
                default:
                    return;
            }
            e.preventDefault();
        }
    });
}

function renderShortcutTable() {
    const tbody = document.querySelector('#shortcut-table tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    COMMANDS.forEach(cmd => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${cmd.label}</td>
            <td>${cmd.description || ''}</td>
            <td>${cmd.shortcut || 'Command Palette 내 검색 실행'}</td>
        `;
        tbody.appendChild(tr);
    });

    // Extra global shortcuts
    const extra = [
        { label: '커맨드 팔레트 열기', desc: '명령 검색 및 실행', key: 'Ctrl/⌘ + K' },
        { label: '단축키 도움말 보기', desc: 'System 탭의 단축키 안내 카드로 이동', key: 'Shift + ?' },
        { label: '뷰 전환', desc: 'Alt+1~6으로 각 탭 전환', key: 'Alt + 1~6' }
    ];
    extra.forEach(e => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${e.label}</td>
            <td>${e.desc}</td>
            <td>${e.key}</td>
        `;
        tbody.appendChild(tr);
    });
}

// --- Helpers ---

function updateText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function formatCurrency(val) {
    if (val === undefined || val === null) return "-";
    return "₩" + Math.floor(val).toLocaleString();
}

let equityChartInstance = null;

function renderEquityChart(dataPoints) {
    const ctx = document.getElementById('equityChart');
    if (!ctx) return;

    const labels = dataPoints.map(d => d.timestamp.split(' ')[1]); // Time only
    const data = dataPoints.map(d => d.total_equity);

    if (equityChartInstance) {
        equityChartInstance.data.labels = labels;
        equityChartInstance.data.datasets[0].data = data;
        equityChartInstance.update();
    } else {
        equityChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '총 자산',
                    data: data,
                    borderColor: '#00ff88',
                    backgroundColor: 'rgba(0, 255, 136, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#888' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#888' }
                    }
                }
            }
        });
    }
}

// --- Legacy Loaders (kept for compatibility) ---
let simChartInstance = null;

function renderSimulationChart(dataPoints) {
    const ctx = document.getElementById('simEquityChart');
    if (!ctx) return;

    if (!dataPoints || dataPoints.length === 0) return;

    const labels = dataPoints.map(d => d.timestamp.split(' ')[0]); // Date only for long sim
    const data = dataPoints.map(d => d.total_equity);

    if (simChartInstance) {
        simChartInstance.data.labels = labels;
        simChartInstance.data.datasets[0].data = data;
        simChartInstance.update();
    } else {
        simChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '시뮬레이션 자산',
                    data: data,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.2,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#888' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#888', maxTicksLimit: 10 }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }
}

window.loadSimulationToday = async function () {
    try {
        // Parallel fetch for summary and history
        const [todayResp, historyResp] = await Promise.all([
            fetch("/api/simulation/today"),
            fetch("/api/simulation/history")
        ]);

        const data = await todayResp.json();

        if (data.status === "NO_DATA") {
            updateText('sim-message', "데이터 없음");
            // Still try to render history if available
        } else {
            updateText('sim-win-rate', (data.win_rate != null) ? (data.win_rate * 100).toFixed(1) + "%" : "-");
            updateText('sim-pnl', (data.pnl != null) ? data.pnl.toLocaleString() : "-");
            updateText('sim-trade-count', data.trade_count || "-");
            updateText('sim-message', data.summary || "시뮬레이션 완료");
        }

        // Render Chart
        const historyData = await historyResp.json();
        if (historyData && historyData.length > 0) {
            renderSimulationChart(historyData);
        }

    } catch (e) {
        console.error(e);
        updateText('sim-message', "로드 오류");
    }
}

window.loadSystemHealth = async function () {
    const el = document.getElementById('system-health-json');
    if (!el) return;
    try {
        const resp = await fetch("/api/health");
        const data = await resp.json();
        el.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
        el.textContent = "상태 로드 중 오류 발생";
    }
}

// Expose for loader
window.loadAiCoreSummary = function () {
    // Placeholder or empty
};

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initCommandPalette();
    initKeyboardShortcuts();
    renderShortcutTable();
});

// --- Modal Logic ---

const KOREAN_LABELS = {
    symbol: "종목코드",
    name: "종목명",
    price: "현재가",
    qty: "수량",
    entry_price: "평단가",
    entry_date: "진입일",
    value: "평가금",
    pnl: "손익",
    pnl_pct: "수익률(%)",
    weight: "비중",
    time: "시간",
    action: "구분",
    reason: "사유",
    change: "등락",
    change_pct: "등락률(%)",
    open: "시가",
    high: "고가",
    low: "저가",
    volume: "거래량"
};

function initModalLogic() {
    const modal = document.getElementById('detail-modal');
    const closeBtn = document.getElementById('close-modal-btn');
    const backdrop = document.querySelector('.modal-backdrop');

    if (!modal) return;

    function closeModal() {
        modal.classList.add('hidden');
    }

    if (closeBtn) closeBtn.onclick = closeModal;
    if (backdrop) backdrop.onclick = closeModal;

    // Esc to close
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeModal();
        }
    });
}

function showDetailModal(title, data) {
    const modal = document.getElementById('detail-modal');
    const titleEl = document.getElementById('modal-title');
    const bodyEl = document.getElementById('modal-body');

    if (!modal || !titleEl || !bodyEl) return;

    titleEl.textContent = title;
    bodyEl.innerHTML = '';

    // Create rows
    for (const [key, val] of Object.entries(data)) {
        // Skip internal keys or objects
        if (typeof val === 'object' || key === 'history') continue;

        const row = document.createElement('div');
        row.className = 'detail-row';

        const label = KOREAN_LABELS[key] || key.toUpperCase();

        let displayVal = val;

        // Format numbers
        if (typeof val === 'number') {
            if (key.includes('pct')) {
                displayVal = val.toFixed(2) + '%';
            } else if (key.includes('price') || key.includes('value') || key.includes('pnl') || key.includes('cash') || key.includes('equity')) {
                displayVal = formatCurrency(val);
            } else {
                displayVal = val.toLocaleString();
            }
        }

        row.innerHTML = `
            <span class="detail-label">${label}</span>
            <span class="detail-value">${displayVal}</span>
        `;

        // Colorize PnL logic
        if (key === 'pnl' || key === 'pnl_pct' || key === 'change' || key === 'change_pct') {
            const valNum = parseFloat(val);
            const valEl = row.querySelector('.detail-value');
            if (valNum > 0) valEl.classList.add('up');
            if (valNum < 0) valEl.classList.add('down');
        }

        bodyEl.appendChild(row);
    }

    // History chart placeholder if available? 
    // For now simple KV list.

    modal.classList.remove('hidden');
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initCommandPalette();
    initKeyboardShortcuts();
    renderShortcutTable(); // Render help table
    initModalLogic(); // New
});
