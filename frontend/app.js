// ==========================================================================
// RAGTUNE Enterprise AI Operating System - Application Engine
// Inspired by Apple, Linear, Vercel & OpenAI Enterprise
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initCommandPalette();
    initChatWorkspace();
    initSQLAnalyst();
    loadHITLQueue();
    loadSchemaCatalog();
    checkHealthStatus();
});

// Toast Notification Helper
window.showToast = function(message, type = 'info', duration = 3500) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let iconSvg = '';
    if (type === 'success') {
        iconSvg = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
    } else if (type === 'error' || type === 'danger') {
        iconSvg = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
    } else {
        iconSvg = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="3"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;
    }

    toast.innerHTML = `
        ${iconSvg}
        <div style="flex:1;">${escapeHtml(message)}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(8px)';
        setTimeout(() => toast.remove(), 250);
    }, duration);
};

// Pane Switcher & Navigation
function initNavigation() {
    const navItems = document.querySelectorAll('.sidebar-nav .nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const paneId = item.getAttribute('data-pane');
            if (paneId) switchPane(paneId);
        });
    });
}

window.switchPane = function(paneId) {
    const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
    const panes = document.querySelectorAll('.workspace-pane');

    navItems.forEach(item => {
        if (item.getAttribute('data-pane') === paneId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    panes.forEach(pane => {
        if (pane.id === `pane-${paneId}`) {
            pane.classList.add('active');
        } else {
            pane.classList.remove('active');
        }
    });

    if (paneId === 'hitl') loadHITLQueue();
    if (paneId === 'sql-analyst') loadSchemaCatalog();

    closeCommandPalette();
};

// ⌘K Command Palette Overlay Logic
function initCommandPalette() {
    const modal = document.getElementById('cmd-modal-overlay');
    const input = document.getElementById('cmd-input');

    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            toggleCommandPalette();
        }
        if (e.key === 'Escape' && modal.classList.contains('open')) {
            closeCommandPalette();
        }
    });

    if (input) {
        input.addEventListener('input', () => {
            const query = input.value.toLowerCase().trim();
            const items = document.querySelectorAll('.cmd-item');
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                if (text.includes(query)) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
}

window.toggleCommandPalette = function() {
    const modal = document.getElementById('cmd-modal-overlay');
    const input = document.getElementById('cmd-input');
    if (modal) {
        modal.classList.toggle('open');
        if (modal.classList.contains('open') && input) {
            input.value = '';
            input.focus();
        }
    }
};

window.closeCommandPalette = function() {
    const modal = document.getElementById('cmd-modal-overlay');
    if (modal) modal.classList.remove('open');
};

// AI Chat Workspace Logic
function initChatWorkspace() {
    const sendBtn = document.getElementById('send-query-btn');
    const input = document.getElementById('chat-prompt-input');

    if (sendBtn && input) {
        sendBtn.addEventListener('click', () => submitChatQuery());
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitChatQuery();
            }
        });
    }
}

window.sendPresetQuery = function(presetText) {
    const input = document.getElementById('chat-prompt-input');
    if (input) {
        input.value = presetText;
        submitChatQuery();
    }
};

async function submitChatQuery() {
    const input = document.getElementById('chat-prompt-input');
    const history = document.getElementById('chat-history');
    const sendBtn = document.getElementById('send-query-btn');
    const modelSelect = document.getElementById('chat-model-select');

    if (!input || !history) return;
    const query = input.value.trim();
    if (!query) return;

    // Append User Message
    const userMsg = document.createElement('div');
    userMsg.className = 'chat-msg';
    userMsg.innerHTML = `
        <div class="chat-avatar user">U</div>
        <div class="chat-bubble">
            <strong>${escapeHtml(query)}</strong>
        </div>
    `;
    history.appendChild(userMsg);

    input.value = '';
    sendBtn.disabled = true;
    sendBtn.innerHTML = `Running Engine...`;
    history.scrollTop = history.scrollHeight;

    // AI Response Placeholder
    const aiMsg = document.createElement('div');
    aiMsg.className = 'chat-msg';
    aiMsg.innerHTML = `
        <div class="chat-avatar">AI</div>
        <div class="chat-bubble">
            <div class="loading-state" style="color:var(--text-muted);">Reasoning through pipeline...</div>
        </div>
    `;
    history.appendChild(aiMsg);
    history.scrollTop = history.scrollHeight;

    try {
        const res = await fetch('/api/v1/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                role: 'ANALYST',
                tenant_id: 'tenant_enterprise_default'
            })
        });

        if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
        const data = await res.json();

        // Render AI Answer
        const bubble = aiMsg.querySelector('.chat-bubble');
        let sqlBadge = data.generated_sql ? `<div style="font-family:var(--font-mono); font-size:0.8rem; background:var(--bg-muted); padding:0.5rem; border-radius:var(--radius-sm); margin:0.5rem 0; border:1px solid var(--border);">${escapeHtml(data.generated_sql)}</div>` : '';

        bubble.innerHTML = `
            <div>${formatMarkdown(data.response)}</div>
            ${sqlBadge}
            <div class="chat-meta-bar">
                <span class="badge-mono badge-success">${data.intent_route}</span>
                <span class="badge-mono">Confidence: ${(data.overall_confidence * 100).toFixed(1)}%</span>
                <span class="badge-mono">Latency: ${data.execution_time_ms} ms</span>
                <button class="btn btn-outline btn-sm" onclick="inspectXAITrace('${data.trace_id}')">Inspect XAI Trace</button>
            </div>
        `;

        if (data.hitl_flagged) {
            showToast(`Flagged for HITL review (Ticket: ${data.hitl_ticket_id})`, 'warning', 5000);
            loadHITLQueue();
        } else {
            showToast('Query executed successfully', 'success');
        }
    } catch (err) {
        const bubble = aiMsg.querySelector('.chat-bubble');
        bubble.innerHTML = `<span style="color:var(--danger);">Error: ${escapeHtml(err.message)}</span>`;
        showToast(`Execution failed: ${err.message}`, 'danger');
    } finally {
        sendBtn.disabled = false;
        sendBtn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            Run Query
        `;
        history.scrollTop = history.scrollHeight;
    }
}

// SQL Analyst Logic
function initSQLAnalyst() {}

window.executeSQLQuery = async function() {
    const input = document.getElementById('sql-analyst-input');
    if (!input) return;
    const query = input.value.trim();
    if (!query) return;

    try {
        const res = await fetch('/api/v1/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, role: 'ANALYST', tenant_id: 'tenant_enterprise_default' })
        });
        const data = await res.json();
        document.getElementById('sql-compiled-code').textContent = data.generated_sql || query;

        const headersRow = document.getElementById('sql-results-headers');
        const bodyRows = document.getElementById('sql-results-rows');
        headersRow.innerHTML = '';
        bodyRows.innerHTML = '';

        if (data.sql_columns && data.sql_columns.length > 0) {
            data.sql_columns.forEach(col => {
                const th = document.createElement('th');
                th.textContent = col;
                headersRow.appendChild(th);
            });

            data.sql_rows.forEach(row => {
                const tr = document.createElement('tr');
                data.sql_columns.forEach(col => {
                    const td = document.createElement('td');
                    td.textContent = row[col] !== undefined ? row[col] : '';
                    tr.appendChild(td);
                });
                bodyRows.appendChild(tr);
            });
        }
        showToast('SQL Execution complete', 'success');
    } catch (e) {
        showToast('SQL Execution failed', 'danger');
    }
};

// Inspect XAI Trace in Context Drawer
window.inspectXAITrace = async function(traceId) {
    const drawer = document.getElementById('drawer-content');
    if (!drawer || !traceId) return;

    try {
        const res = await fetch(`/api/v1/xai/${traceId}`);
        if (!res.ok) return;
        const trace = await res.json();

        drawer.innerHTML = `
            <h4 style="font-size:0.85rem; font-weight:700; margin-bottom:0.5rem;">Trace ID: ${trace.trace_id}</h4>
            <div style="font-size:0.75rem; color:var(--text-secondary); margin-bottom:1rem;">Query: "${escapeHtml(trace.user_query)}"</div>
            <div style="display:flex; flex-direction:column; gap:0.6rem;">
                ${trace.execution_steps.map(step => `
                    <div class="card-flat" style="padding:0.65rem;">
                        <div style="display:flex; justify-content:space-between; font-weight:600; font-size:0.8rem;">
                            <span>${escapeHtml(step.agent_node)}</span>
                            <span style="color:var(--text-muted); font-size:0.7rem;">${step.latency_ms} ms</span>
                        </div>
                        <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:0.25rem;">${escapeHtml(step.action_taken)}</div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (e) {
        console.error(e);
    }
};

// HITL Queue Handling
window.loadHITLQueue = async function() {
    const queueList = document.getElementById('hitl-queue-list');
    const badge = document.getElementById('sidebar-hitl-badge');
    if (!queueList) return;

    try {
        const res = await fetch('/api/v1/hitl/queue');
        const data = await res.json();

        if (badge) badge.textContent = data.pending_count || 0;

        if (!data.tickets || data.tickets.length === 0) {
            queueList.innerHTML = `<div class="card-flat" style="text-align:center; color:var(--text-muted); padding:2rem;">No pending tickets requiring Human-in-the-Loop approval.</div>`;
            return;
        }

        queueList.innerHTML = '';
        data.tickets.forEach(ticket => {
            const card = document.createElement('div');
            card.className = 'card-flat';
            card.style.borderLeft = '4px solid var(--warning)';
            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong>Ticket ID: ${ticket.ticket_id}</strong>
                    <span class="badge-mono badge-warning">User: ${ticket.user_id}</span>
                </div>
                <div style="margin:0.5rem 0; font-size:0.85rem;"><strong>Original Query:</strong> "${escapeHtml(ticket.original_query)}"</div>
                <div style="color:var(--danger); font-size:0.8rem; margin-bottom:0.75rem;"><strong>Reason:</strong> ${escapeHtml(ticket.reason)}</div>
                <div style="display:flex; gap:0.5rem;">
                    <button class="btn btn-black btn-sm" onclick="resolveTicket('${ticket.ticket_id}', 'APPROVE')">Approve Query</button>
                    <button class="btn btn-outline btn-sm" onclick="resolveTicket('${ticket.ticket_id}', 'REJECT')">Reject Query</button>
                </div>
            `;
            queueList.appendChild(card);
        });
    } catch (e) {
        console.error(e);
    }
};

window.resolveTicket = async function(ticketId, action) {
    try {
        const res = await fetch('/api/v1/hitl/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ticket_id: ticketId,
                action: action,
                operator_id: 'operator_admin',
                operator_notes: `Manual operator action: ${action}`
            })
        });

        if (res.ok) {
            showToast(`Ticket ${ticketId} resolved as ${action}`, 'success');
            loadHITLQueue();
        } else {
            showToast('Failed to resolve ticket', 'danger');
        }
    } catch (e) {
        showToast('Error resolving ticket', 'danger');
    }
};

// Schema Catalog Loading
async function loadSchemaCatalog() {
    const container = document.getElementById('sql-schema-list');
    if (!container) return;

    try {
        const res = await fetch('/api/v1/schema');
        const data = await res.json();
        if (!data.schema || data.schema.length === 0) return;

        container.innerHTML = '';
        data.schema.forEach(tbl => {
            const div = document.createElement('div');
            div.style.borderBottom = '1px solid var(--border)';
            div.style.paddingBottom = '0.5rem';
            div.innerHTML = `
                <div style="font-weight:600; font-size:0.8rem;">${escapeHtml(tbl.table_name)}</div>
                <div style="font-size:0.725rem; color:var(--text-muted);">${tbl.columns.length} columns • ${tbl.row_count} rows</div>
            `;
            container.appendChild(div);
        });
    } catch (e) {
        console.error(e);
    }
}

// Health Telemetry Check
async function checkHealthStatus() {
    try {
        const res = await fetch('/health');
        if (res.ok) {
            const text = document.getElementById('header-status-text');
            if (text) text.textContent = 'Engine Online';
        }
    } catch (e) {}
}

// Document Upload Simulation Trigger
window.triggerFileUpload = function() {
    const sampleText = "Acme Enterprise Master Service Agreement SLA Uptime Commitment is 99.99% for Severity 1 outages.";
    fetch('/api/v1/ingest/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text: sampleText,
            title: "acme_sla_master_agreement.md",
            doc_id: `doc_${Date.now()}`
        })
    }).then(res => res.json()).then(data => {
        showToast(data.message || 'Document ingested successfully', 'success');
    }).catch(() => showToast('Failed to ingest document', 'danger'));
};

window.inspectNode = function(nodeName) {
    showToast(`Inspecting ${nodeName} execution node`, 'info');
};

window.toggleRightDrawer = function() {};

// Utility Helpers
function escapeHtml(str) {
    return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function formatMarkdown(text) {
    if (!text) return '';
    let formatted = escapeHtml(text);
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/`([^`]+)`/g, '<code class="font-mono" style="background:var(--bg-muted); padding:0.1rem 0.3rem; border-radius:4px; border:1px solid var(--border);">$1</code>');
    return formatted;
}
