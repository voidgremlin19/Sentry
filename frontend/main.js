import Chart from 'chart.js/auto';

const API_BASE = "http://localhost:8000/api";

let tracesData = [];
let globalSearchTerm = '';
let selectedModelFilter = null;

// Boot Sequence
async function runBootSequence() {
    return new Promise(resolve => {
        setTimeout(() => {
            const loader = document.getElementById('terminal-loader');
            loader.style.opacity = '0';
            setTimeout(() => {
                loader.style.display = 'none';
                
                const app = document.getElementById('app');
                app.classList.remove('hidden-initially');
                app.classList.add('fade-in-active');
                
                // Trigger stagger animations
                const staggerItems = document.querySelectorAll('.stagger-item');
                staggerItems.forEach((item, index) => {
                    setTimeout(() => {
                        item.classList.add('visible');
                    }, index * 150);
                });
                
                resolve();
            }, 1000);
        }, 1500);
    });
}

// Typewriter / Counter Animation
function animateValue(obj, start, end, duration, isPercentage = false) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        
        let current = start + progress * (end - start);
        if (isPercentage) {
            obj.innerHTML = current.toFixed(1) + '%';
        } else {
            obj.innerHTML = Math.floor(current);
        }
        
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Typewriter for raw output
function typeWriter(element, text, speed = 5) {
    element.innerHTML = '';
    let i = 0;
    function type() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    type();
}

async function fetchData() {
    try {
        const [summaryRes, modelsRes, categoriesRes, tracesRes] = await Promise.all([
            fetch(`${API_BASE}/summary`),
            fetch(`${API_BASE}/stats/models`),
            fetch(`${API_BASE}/stats/categories`),
            fetch(`${API_BASE}/traces`)
        ]);

        const summary = await summaryRes.json();
        const models = await modelsRes.json();
        const categories = await categoriesRes.json();
        tracesData = await tracesRes.json();

        if (summary.error) {
            console.warn("No data available yet");
            await runBootSequence();
            return;
        }

        updateSummary(summary);
        renderCharts(models, categories);
        populateFilters();
        renderTable();
        
        setupNavigation();
        
        await runBootSequence();
    } catch (e) {
        console.error("Error fetching data. Is the backend running?", e);
        document.querySelector('.terminal-text p').innerHTML = "> ERROR: Connection failed. Check backend.";
    }
}

function updateSummary(summary) {
    const totalEl = document.getElementById('total-traces');
    const metaEl = document.getElementById('meta-leak-rate');
    const contentEl = document.getElementById('content-leak-rate');
    const cleanEl = document.getElementById('clean-rate');
    
    // Set target values for hover effects or future updates
    totalEl.setAttribute('data-target', summary.total_traces);
    
    // Animate them
    setTimeout(() => {
        animateValue(totalEl, parseInt(totalEl.innerText) || 0, summary.total_traces, 1000, false);
        animateValue(metaEl, parseFloat(metaEl.innerText) || 0, summary.meta_leak_rate * 100, 1000, true);
        animateValue(contentEl, parseFloat(contentEl.innerText) || 0, summary.content_leak_rate * 100, 1000, true);
        animateValue(cleanEl, parseFloat(cleanEl.innerText) || 0, summary.clean_rate * 100, 1000, true);
    }, 100); 
}

function updateDashboardMetrics(modelName = null) {
    let filteredTraces = tracesData;
    if (modelName) {
        filteredTraces = tracesData.filter(t => t.model === modelName);
    }
    
    if (filteredTraces.length === 0) return;
    
    const total = filteredTraces.length;
    const metaLeaks = filteredTraces.filter(t => t.heuristic_meta_leak || t.judge_meta_leak).length;
    const contentLeaks = filteredTraces.filter(t => t.heuristic_content_leak || t.judge_content_leak).length;
    const clean = filteredTraces.filter(t => t.is_clean).length;
    
    const summary = {
        total_traces: total,
        meta_leak_rate: metaLeaks / total,
        content_leak_rate: contentLeaks / total,
        clean_rate: clean / total
    };
    
    updateSummary(summary);
}

function renderCharts(models, categories) {
    Chart.defaults.color = '#5e5e5e'; // Muted charcoal text
    Chart.defaults.borderColor = '#e2dcd0'; // Beige flat borders
    Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
    Chart.defaults.font.size = 13;
    
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }
        },
        scales: {
            y: {
                beginAtZero: true,
                max: 1,
                grid: { color: 'rgba(0,0,0,0.05)', drawBorder: false }, // Very faint grid lines
                ticks: {
                    callback: function(value) { return (value * 100) + '%'; }
                }
            },
            x: {
                grid: { display: false, drawBorder: false }
            }
        },
        animation: {
            duration: 1000,
            easing: 'easeOutQuart'
        }
    };

    // Model Chart (Line chart)
    const ctxModel = document.getElementById('modelChart').getContext('2d');
    new Chart(ctxModel, {
        type: 'line',
        data: {
            labels: models.map(m => m.model),
            datasets: [{
                label: 'Meta-Leak Rate',
                data: models.map(m => m.heuristic_content_leak), // fallback
                backgroundColor: 'rgba(164, 97, 255, 0.1)', // Light purple fill
                borderColor: '#a461ff', // Purple line
                borderWidth: 2,
                pointBackgroundColor: '#fff', // White point
                pointBorderColor: '#a461ff', // Purple point border
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
                tension: 0.2, // Slight, elegant curve
                fill: true
            }]
        },
        options: chartOptions
    });

    // Category Chart (Bar chart)
    const ctxCategory = document.getElementById('categoryChart').getContext('2d');
    new Chart(ctxCategory, {
        type: 'bar',
        data: {
            labels: categories.map(c => c.category),
            datasets: [{
                label: 'Content-Leak Rate',
                data: categories.map(c => c.heuristic_content_leak),
                backgroundColor: '#a17010', // Deep Gold
                borderColor: 'transparent',
                borderRadius: 4,
                barPercentage: 0.5
            }]
        },
        options: chartOptions
    });
}

function populateFilters() {
    const modelSelect = document.getElementById('filter-model');
    const categorySelect = document.getElementById('filter-category');
    const modelPillsContainer = document.getElementById('dynamic-model-pills');
    
    const models = [...new Set(tracesData.map(t => t.model))];
    const categories = [...new Set(tracesData.map(t => t.category))];

    models.forEach(m => {
        // Dropdown option
        const opt = document.createElement('option');
        opt.value = m;
        opt.innerText = m;
        modelSelect.appendChild(opt);
        
        // Render dynamic pill
        if (modelPillsContainer) {
            const count = tracesData.filter(t => t.model === m).length;
            const pillSpan = document.createElement('span');
            pillSpan.className = 'pill selectable-pill';
            pillSpan.style.cursor = 'pointer';
            pillSpan.innerHTML = `${m} <span class="pill-count">${count}</span>`;
            
            pillSpan.addEventListener('click', () => {
                const isAlreadySelected = pillSpan.classList.contains('active-pill');
                document.querySelectorAll('.selectable-pill').forEach(p => {
                    p.classList.remove('active-pill');
                    p.style.backgroundColor = 'rgba(0,0,0,0.03)';
                });
                
                if (isAlreadySelected) {
                    selectedModelFilter = null;
                    updateDashboardMetrics(null);
                } else {
                    selectedModelFilter = m;
                    pillSpan.classList.add('active-pill');
                    pillSpan.style.backgroundColor = 'rgba(0,0,0,0.1)';
                    updateDashboardMetrics(m);
                }
            });
            
            modelPillsContainer.appendChild(pillSpan);
        }
    });

    categories.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c;
        opt.innerText = c;
        categorySelect.appendChild(opt);
    });
    
    populateRecentTraces();
}

function populateRecentTraces() {
    const container = document.getElementById('recent-traces-list');
    if (!container) return;
    container.innerHTML = '';
    
    // Get last 5 traces
    const recent = tracesData.slice(-5).reverse();
    recent.forEach((t) => {
        const btn = document.createElement('button');
        btn.className = 'pill';
        btn.style.cursor = 'pointer';
        let status = t.is_clean ? '🟢' : '🔴';
        btn.innerHTML = `${status} ${t.prompt_id} <span class="pill-count">${t.model}</span>`;
        btn.addEventListener('click', () => openModal(t));
        container.appendChild(btn);
    });
}

function renderTable() {
    const tbody = document.getElementById('traces-body');
    tbody.innerHTML = '';

    const modelFilter = document.getElementById('filter-model').value;
    const catFilter = document.getElementById('filter-category').value;
    const leakFilter = document.getElementById('filter-leak').value;

    let filtered = tracesData.filter(t => {
        if (modelFilter !== 'all' && t.model !== modelFilter) return false;
        if (catFilter !== 'all' && t.category !== catFilter) return false;
        
        if (leakFilter === 'meta') {
            if (!(t.heuristic_meta_leak || t.judge_meta_leak)) return false;
        } else if (leakFilter === 'content') {
            if (!(t.heuristic_content_leak || t.judge_content_leak)) return false;
        } else if (leakFilter === 'clean') {
            if (!t.is_clean) return false;
        }

        if (globalSearchTerm) {
            const term = globalSearchTerm.toLowerCase();
            const searchableText = `${t.prompt_id} ${t.model} ${t.category}`.toLowerCase();
            if (!searchableText.includes(term)) return false;
        }
        
        return true;
    });

    filtered.forEach((t, index) => {
        const tr = document.createElement('tr');
        
        let badgeHtml = '';
        if (t.heuristic_meta_leak || t.judge_meta_leak) {
            badgeHtml = '<span class="badge badge-danger">Meta-Leak</span>';
        } else if (t.heuristic_content_leak || t.judge_content_leak) {
            badgeHtml = '<span class="badge badge-warning">Content-Leak</span>';
        } else if (t.is_clean) {
            badgeHtml = '<span class="badge badge-success">Clean</span>';
        } else {
            badgeHtml = '<span class="badge badge-neutral">Unknown</span>';
        }
        
        tr.innerHTML = `
            <td><strong>${t.prompt_id}</strong></td>
            <td>${t.model}</td>
            <td>${t.category}</td>
            <td>${badgeHtml}</td>
            <td><button class="action-btn view-details-btn" data-index="${index}">View</button></td>
        `;
        tbody.appendChild(tr);
    });

    document.querySelectorAll('.view-details-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const index = e.target.getAttribute('data-index');
            openModal(filtered[index]);
        });
    });
}

function openModal(trace) {
    const modal = document.getElementById('trace-modal');
    document.getElementById('modal-title').innerText = `Trace Details: ${trace.prompt_id}`;
    document.getElementById('modal-heuristic-evidence').innerText = trace.heuristic_evidence || 'No heuristic evidence found.';
    document.getElementById('modal-judge-evidence').innerText = trace.judge_evidence || 'No judge evidence found.';
    
    const rawOut = document.getElementById('modal-raw-output');
    rawOut.innerHTML = '';
    
    modal.classList.remove('hidden');
    
    setTimeout(() => {
        typeWriter(rawOut, trace.raw_output || 'No trace output available.', 1);
    }, 300);
}

// Event Listeners

// Tab functionality
document.querySelectorAll('.library-tabs .tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
        const target = e.currentTarget.getAttribute('data-tab');
        
        if (target === 'data') {
            document.querySelector('[data-target="view-explorer"]').click();
            return;
        }
        
        document.querySelectorAll('.library-tabs .tab').forEach(t => t.classList.remove('active'));
        e.currentTarget.classList.add('active');
        
        const grid = document.querySelector('.dashboard-grid');
        const charts = document.querySelector('.charts-section');
        
        if (target === 'metrics') {
            grid.style.display = 'grid';
            charts.style.display = 'none';
        } else if (target === 'charts') {
            grid.style.display = 'none';
            charts.style.display = 'flex';
            charts.style.flexDirection = 'column';
            charts.style.gap = '2rem';
        }
    });
});

document.getElementById('filter-model').addEventListener('change', renderTable);
document.getElementById('filter-category').addEventListener('change', renderTable);
document.getElementById('filter-leak').addEventListener('change', renderTable);

document.getElementById('global-search').addEventListener('input', (e) => {
    globalSearchTerm = e.target.value;
    
    // Automatically switch to Trace Explorer view when searching
    if (globalSearchTerm.length > 0) {
        const explorerTab = document.querySelector('[data-target="view-explorer"]');
        if (explorerTab && !explorerTab.classList.contains('active')) {
            explorerTab.click(); // Re-use the setupNavigation logic to switch views
        }
    }
    
    renderTable();
});

document.querySelector('.close').addEventListener('click', () => {
    document.getElementById('trace-modal').classList.add('hidden');
});

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const views = document.querySelectorAll('.app-view');
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            views.forEach(view => view.classList.add('hidden-view'));
            
            const targetId = item.getAttribute('data-target');
            const targetView = document.getElementById(targetId);
            if (targetView) {
                targetView.classList.remove('hidden-view');
                // Re-trigger stagger animation if needed
                const staggers = targetView.querySelectorAll('.stagger-item');
                staggers.forEach(el => el.classList.remove('visible'));
                setTimeout(() => {
                    staggers.forEach(el => el.classList.add('visible'));
                }, 50);
            }
            
            const pageTitle = document.getElementById('page-title');
            if (targetId === 'view-dashboard') {
                pageTitle.innerText = "Sentry Dashboard";
            } else if (targetId === 'view-explorer') {
                pageTitle.innerText = "Trace Explorer";
            } else if (targetId === 'view-analytics') {
                pageTitle.innerText = "Model Analytics";
            } else if (targetId === 'view-rules') {
                pageTitle.innerText = "Rules & Heuristics";
            }
        });
    });
}

// Run
fetchData();
setupNavigation();
