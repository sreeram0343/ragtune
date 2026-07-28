// RAGTUNE Enterprise Web Dashboard Application Logic

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initQueryForm();
    loadHITLQueue();
    loadSchemaCatalog();
});

// Navigation Handling
function initNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');

            navButtons.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const targetPane = document.getElementById(`tab-${targetTab}`);
            if (targetPane) targetPane.classList.add('active');

            if (targetTab === 'hitl') loadHITLQueue();
            if (targetTab === 'schema') loadSchemaCatalog();
        });
    });
}

// Global Preset Setter
window.setPresetQuery = function(queryText) {
    const input = document.getElementById('query-input');
    if (input) {
        input.value = queryText;
        input.focus();
    }
};

// Query Submission Logic
function initQueryForm() {
    const submitBtn = document.getElementById('submit-query-btn');
    const queryInput = document.getElementById('query-input');

    if (submitBtn && queryInput) {
        submitBtn.addEventListener('click', async () => {
            const query = queryInput.value.trim();
            if (!query) return;

            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <svg class="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"></path></svg>
                Processing Reasoning Engine...
            `;

            try {
                const response = await fetch('/api/v1/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        query: query,
                        role: 'ANALYST',
                        tenant_id: 'tenant_enterprise_default'
                    })
                });

                if (!response.ok) {
                    throw new Error(`Server returned status ${response.status}`);
                }

                const data = await response.json();
                renderQueryResults(data);
            } catch (err) {
                alert(`Error executing query: ${err.message}`);
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
                    Execute Reasoning Engine
                `;
            }
        });
    }
}

// Render Results Output
function renderQueryResults(data) {
    // 1. Show Telemetry Banner
    const banner = document.getElementById('results-banner');
    if (banner) {
        banner.classList.remove('hidden');
        document.getElementById('res-intent').textContent = data.intent_route;
        document.getElementById('res-confidence').textContent = `${(data.overall_confidence * 100).toFixed(1)}%`;
        document.getElementById('res-latency').textContent = `${data.execution_time_ms} ms`;
        document.getElementById('res-cache').textContent = data.cache_hit ? 'HIT (0ms)' : 'MISS (Fresh)';
        document.getElementById('res-trace').textContent = data.trace_id || '--';
    }

    // 2. Render Narrative Output
    const narrativeOut = document.getElementById('narrative-output');
    if (narrativeOut) {
        narrativeOut.innerHTML = formatMarkdown(data.response);
    }

    // 3. Render SQL Results (if available)
    const sqlCard = document.getElementById('sql-results-card');
    if (data.generated_sql && sqlCard) {
        sqlCard.classList.remove('hidden');
        document.getElementById('sql-statement-view').textContent = data.generated_sql;
        document.getElementById('sql-rows-count').textContent = `${data.sql_rows.length} rows`;

        const headersRow = document.getElementById('sql-table-headers');
        const tableBody = document.getElementById('sql-table-body');
        headersRow.innerHTML = '';
        tableBody.innerHTML = '';

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
                tableBody.appendChild(tr);
            });
        }
    } else if (sqlCard) {
        sqlCard.classList.add('hidden');
    }

    // 4. Render RAG Evidence Chunks
    const ragCard = document.getElementById('rag-evidence-card');
    const chunksList = document.getElementById('evidence-chunks-list');
    if (data.retrieved_chunks && data.retrieved_chunks.length > 0 && ragCard && chunksList) {
        ragCard.classList.remove('hidden');
        document.getElementById('rag-chunks-count').textContent = `${data.retrieved_chunks.length} chunks`;
        chunksList.innerHTML = '';

        data.retrieved_chunks.forEach(chunk => {
            const div = document.createElement('div');
            div.className = 'chunk-item';
            div.innerHTML = `
                <div class="chunk-header">
                    <span>${escapeHtml(chunk.title || 'Document')}</span>
                    <span class="badge">Relevance: ${((chunk.rerank_score || chunk.rrf_score || 0) * 100).toFixed(1)}%</span>
                </div>
                <div style="color: #94a3b8;">${escapeHtml(chunk.content || '')}</div>
            `;
            chunksList.appendChild(div);
        });
    } else if (ragCard) {
        ragCard.classList.add('hidden');
    }

    // 5. Update Guardrail Matrix Badges
    if (data.guardrail_matrix && data.guardrail_matrix.length > 0) {
        data.guardrail_matrix.forEach(layer => {
            const card = document.querySelector(`.layer-card[data-layer="${layer.layer_num}"]`);
            if (card) {
                const pill = card.querySelector('.status-pill');
                if (pill) {
                    if (layer.passed) {
                        pill.className = 'status-pill pass';
                        pill.textContent = 'PASS';
                    } else {
                        pill.className = 'status-pill fail';
                        pill.textContent = 'FAIL';
                    }
                }
            }
        });
    }

    // 6. Fetch and Render XAI Timeline
    if (data.trace_id) {
        fetchXAITrace(data.trace_id);
    }
}

// Fetch XAI Execution Graph Trace
async function fetchXAITrace(traceId) {
    const timeline = document.getElementById('xai-timeline');
    if (!timeline) return;

    try {
        const res = await fetch(`/api/v1/xai/${traceId}`);
        if (!res.ok) return;
        const trace = await res.json();

        timeline.innerHTML = '';
        trace.execution_steps.forEach(step => {
            const stepDiv = document.createElement('div');
            stepDiv.className = 'timeline-step';
            stepDiv.innerHTML = `
                <div style="flex:1;">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="step-node">${escapeHtml(step.agent_node)}</span>
                        <span class="step-time">${step.latency_ms} ms</span>
                    </div>
                    <div style="color: #cbd5e1; margin-top:0.2rem;">${escapeHtml(step.action_taken)}</div>
                </div>
            `;
            timeline.appendChild(stepDiv);
        });
    } catch (e) {
        console.error('Failed to load XAI trace', e);
    }
}

// Load HITL Queue Tickets
window.loadHITLQueue = async function() {
    const queueContainer = document.getElementById('hitl-queue-container');
    const badgeCount = document.getElementById('hitl-badge-count');
    if (!queueContainer) return;

    try {
        const res = await fetch('/api/v1/hitl/queue');
        const data = await res.json();

        if (badgeCount) badgeCount.textContent = data.pending_count || 0;

        if (!data.tickets || data.tickets.length === 0) {
            queueContainer.innerHTML = '<div class="empty-state">No pending tickets requiring Human-in-the-Loop approval.</div>';
            return;
        }

        queueContainer.innerHTML = '';
        data.tickets.forEach(ticket => {
            const card = document.createElement('div');
            card.className = 'ticket-card';
            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="color: var(--warning);">Ticket ID: ${ticket.ticket_id}</strong>
                    <span class="badge">User: ${ticket.user_id}</span>
                </div>
                <div style="margin: 0.5rem 0; font-size: 0.9rem;"><strong>Original Query:</strong> "${escapeHtml(ticket.original_query)}"</div>
                <div style="color: #f87171; font-size: 0.85rem;"><strong>Flag Reason:</strong> ${escapeHtml(ticket.reason)}</div>
                <div class="ticket-actions">
                    <button class="btn-success" onclick="resolveTicket('${ticket.ticket_id}', 'APPROVE')">Approve Query</button>
                    <button class="btn-danger" onclick="resolveTicket('${ticket.ticket_id}', 'REJECT')">Reject Query</button>
                </div>
            `;
            queueContainer.appendChild(card);
        });
    } catch (e) {
        console.error('Failed to load HITL queue', e);
    }
};

// Resolve HITL Ticket Action
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
            alert(`Ticket ${ticketId} resolved as ${action}`);
            loadHITLQueue();
        } else {
            alert('Failed to resolve ticket');
        }
    } catch (e) {
        alert('Error resolving ticket');
    }
};

// Load Database Schema Catalog
async function loadSchemaCatalog() {
    const container = document.getElementById('schema-catalog-container');
    if (!container) return;

    try {
        const res = await fetch('/api/v1/schema');
        const data = await res.json();

        if (!data.schema || data.schema.length === 0) {
            container.innerHTML = '<div class="empty-state">No tables found in database.</div>';
            return;
        }

        container.innerHTML = '';
        data.schema.forEach(table => {
            const card = document.createElement('div');
            card.className = 'table-schema-card';

            const colsHtml = table.columns.map(c => 
                `<li style="margin-bottom:0.25rem;"><code>${c.name}</code> <span style="color: #64748b;">(${c.type})</span> ${c.primary_key ? '<span class="badge" style="color:#818cf8;">PK</span>' : ''}</li>`
            ).join('');

            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
                    <h3 style="color:#a5b4fc;">${escapeHtml(table.table_name)}</h3>
                    <span class="badge">${table.row_count} rows</span>
                </div>
                <ul style="list-style:none; font-size:0.85rem;">${colsHtml}</ul>
            `;
            container.appendChild(card);
        });
    } catch (e) {
        console.error('Failed to load schema catalog', e);
    }
}

// Helpers
function escapeHtml(str) {
    return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function formatMarkdown(text) {
    if (!text) return '';
    let formatted = escapeHtml(text);
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/`([^`]+)`/g, '<code class="font-mono" style="background:rgba(255,255,255,0.08); padding:0.1rem 0.3rem; border-radius:4px;">$1</code>');
    return formatted;
}
