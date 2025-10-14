const state = {
    settings: null,
    directoryPath: null,
    favorites: [],
    file: null,
    cellIndex: 0,
};

const els = {
    status: document.getElementById('status'),
    pathInput: document.getElementById('path-input'),
    pathGo: document.getElementById('path-go'),
    tree: document.getElementById('browser-tree'),
    favorites: document.getElementById('favorites-list'),
    filePath: document.getElementById('file-path'),
    markdownView: document.getElementById('markdown-view'),
    cellMeta: document.getElementById('cell-meta'),
    prevComment: document.getElementById('prev-comment'),
    nextComment: document.getElementById('next-comment'),
    stopComment: document.getElementById('stop-comment'),
    refresh: document.getElementById('refresh'),
    commentList: document.getElementById('comments-list'),
    commentForm: document.getElementById('comment-form'),
    commentText: document.getElementById('comment-text'),
    commentStatus: document.getElementById('comment-status'),
    copyCell: document.getElementById('copy-cell'),
    starButton: document.getElementById('toggle-star')
};

async function fetchJSON(url, options = {}) {
    const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    if (!res.ok) {
        const message = await res.text();
        throw new Error(message || res.statusText);
    }
    return res.json();
}

function updateStatus(message, timeout = 0) {
    els.status.textContent = message;
    if (timeout) {
        setTimeout(() => {
            els.status.textContent = '';
        }, timeout);
    }
}

async function loadSettings() {
    try {
        const data = await fetchJSON('/api/settings');
        state.settings = data;
        state.directoryPath = data.current_directory || data.home_directory;
        els.pathInput.value = state.directoryPath;
        updateStatus('Settings loaded');
        await loadTree(state.directoryPath);
        await loadFavorites();
        if (data.session && data.session.current_file) {
            await loadFile(data.session.current_file, data.session.current_cell || 0);
        }
    } catch (err) {
        console.error(err);
        updateStatus(`Failed to load settings: ${err.message}`);
    }
}

async function loadTree(path) {
    try {
        const params = new URLSearchParams();
        if (path) params.set('path', path);
        const data = await fetchJSON(`/api/tree?${params.toString()}`);
        state.directoryPath = data.path;
        els.pathInput.value = state.directoryPath;
        renderTree(data.entries);
        updateStatus(`Browsing ${data.path}`);
    } catch (err) {
        console.error(err);
        updateStatus(`Failed to load directory: ${err.message}`);
    }
}

function renderTree(entries) {
    els.tree.innerHTML = '';
    entries.forEach((entry) => {
        const li = document.createElement('li');
        li.textContent = `${entry.is_dir ? '📁' : entry.is_markdown ? '📄' : '📃'} ${entry.name}`;
        if (entry.starred) li.classList.add('active');
        li.dataset.path = entry.path;
        li.dataset.type = entry.is_dir ? 'dir' : (entry.is_markdown ? 'md' : 'file');
        li.addEventListener('click', () => handleTreeClick(li));
        els.tree.appendChild(li);
    });
}

async function handleTreeClick(node) {
    const path = node.dataset.path;
    const type = node.dataset.type;
    if (type === 'dir') {
        await loadTree(path);
    } else if (type === 'md') {
        await loadFile(path, 0);
    } else {
        updateStatus('Only markdown files are supported');
    }
}

async function loadFavorites() {
    try {
        const list = await fetchJSON('/api/favorites');
        state.favorites = list;
        els.favorites.innerHTML = '';
        list.forEach((item) => {
            const li = document.createElement('li');
            li.textContent = `${item.is_dir ? '📁' : '📄'} ${item.name}`;
            li.dataset.path = item.path;
            li.dataset.type = item.is_dir ? 'dir' : 'md';
            li.addEventListener('click', () => handleTreeClick(li));
            els.favorites.appendChild(li);
        });
    } catch (err) {
        console.error(err);
        updateStatus(`Failed to load favorites: ${err.message}`);
    }
}

async function loadFile(path, cellIndex = 0) {
    try {
        const params = new URLSearchParams({ path });
        const data = await fetchJSON(`/api/file?${params.toString()}`);
        state.file = data;
        const safeIndex = Math.max(0, Math.min(cellIndex, data.cells.length - 1));
        state.cellIndex = Number.isFinite(safeIndex) ? safeIndex : 0;
        els.filePath.textContent = data.path;
        els.starButton.classList.toggle('active', data.starred);
        renderCell();
        await saveSession();
        updateStatus(`Loaded ${data.title}`);
    } catch (err) {
        console.error(err);
        updateStatus(`Failed to load file: ${err.message}`);
    }
}

function renderCell() {
    if (!state.file || !state.file.cells.length) {
        els.markdownView.innerHTML = '<p>No content.</p>';
        els.cellMeta.textContent = '';
        els.commentList.innerHTML = '';
        return;
    }
    const cell = state.file.cells[state.cellIndex];
    els.markdownView.innerHTML = marked.parse(cell.text);
    els.cellMeta.textContent = `Cell ${state.cellIndex + 1} / ${state.file.cells.length}`;
    renderComments(cell);
}

function renderComments(cell) {
    els.commentList.innerHTML = '';
    els.commentStatus.textContent = cell.comments.length ? `${cell.comments.length} comment(s)` : 'No comments yet';
    if (!cell.comments.length) {
        const li = document.createElement('li');
        li.classList.add('muted');
        li.textContent = 'No comments yet for this cell.';
        els.commentList.appendChild(li);
        return;
    }
    cell.comments.forEach((comment, idx) => {
        const li = document.createElement('li');
        const meta = document.createElement('div');
        meta.className = 'meta';
        const confidence = comment.confidence === 'fuzzy' ? '⚠️ outdated?' : '';
        meta.textContent = `#${idx + 1} · ${comment.created_at}${confidence ? ' · ' + confidence : ''}`;
        li.appendChild(meta);
        const body = document.createElement('div');
        body.innerText = comment.text;
        li.appendChild(body);
        els.commentList.appendChild(li);
    });
}

async function saveSession() {
    if (!state.file) return;
    try {
        await fetchJSON('/api/session', {
            method: 'POST',
            body: JSON.stringify({
                current_directory: state.directoryPath,
                current_file: state.file.path,
                current_cell: state.cellIndex,
            }),
        });
    } catch (err) {
        console.error('Failed to save session', err);
    }
}

function showPrevCell() {
    if (!state.file || !state.file.cells.length) return;
    state.cellIndex = (state.cellIndex - 1 + state.file.cells.length) % state.file.cells.length;
    renderCell();
    saveSession();
}

function showNextCell() {
    if (!state.file || !state.file.cells.length) return;
    state.cellIndex = (state.cellIndex + 1) % state.file.cells.length;
    renderCell();
    saveSession();
}

async function submitComment(event) {
    event.preventDefault();
    if (!state.file) return;
    const text = els.commentText.value.trim();
    if (!text) {
        updateStatus('Comment text cannot be empty', 2000);
        return;
    }
    try {
        await fetchJSON('/api/comments', {
            method: 'POST',
            body: JSON.stringify({
                path: state.file.path,
                cell_index: state.cellIndex,
                comment_text: text,
            }),
        });
        els.commentText.value = '';
        await loadFile(state.file.path, state.cellIndex);
        els.commentStatus.textContent = 'Comment saved';
        setTimeout(() => (els.commentStatus.textContent = ''), 2000);
    } catch (err) {
        console.error(err);
        updateStatus(`Failed to save comment: ${err.message}`);
    }
}

async function toggleStar() {
    if (!state.file) return;
    try {
        const result = await fetchJSON('/api/favorites/toggle', {
            method: 'POST',
            body: JSON.stringify({ path: state.file.path }),
        });
        els.starButton.classList.toggle('active', result.starred);
        await loadFavorites();
        updateStatus(result.starred ? 'Added to favorites' : 'Removed from favorites', 2000);
    } catch (err) {
        console.error(err);
        updateStatus(`Failed to toggle favorite: ${err.message}`);
    }
}

async function copyCurrentCell() {
    if (!state.file) return;
    const cell = state.file.cells[state.cellIndex];
    const comments = cell.comments.map((c, idx) => `${idx + 1}. ${c.text}`).join('\n');
    const payload = `File: ${state.file.path}\nCell: ${state.cellIndex + 1} of ${state.file.cells.length}\n\n${cell.text}\n\nComments:\n${comments || 'None'}`;
    try {
        await navigator.clipboard.writeText(payload);
        updateStatus('Cell copied to clipboard', 2000);
    } catch (err) {
        console.error(err);
        updateStatus('Clipboard copy failed');
    }
}

function registerEvents() {
    els.pathGo.addEventListener('click', () => loadTree(els.pathInput.value.trim()));
    els.refresh.addEventListener('click', () => {
        loadTree(state.directoryPath);
        if (state.file) loadFile(state.file.path, state.cellIndex);
    });
    els.prevComment.addEventListener('click', showPrevCell);
    els.nextComment.addEventListener('click', showNextCell);
    els.stopComment.addEventListener('click', copyCurrentCell);
    els.commentForm.addEventListener('submit', submitComment);
    els.copyCell.addEventListener('click', copyCurrentCell);
    els.starButton.addEventListener('click', toggleStar);
    document.getElementById('open-settings').addEventListener('click', () => alert('Settings editing coming soon. Update settings.json manually.'));
    document.getElementById('export').addEventListener('click', () => alert('Export not yet implemented in web UI.'));
}

async function init() {
    registerEvents();
    await loadSettings();
}

window.addEventListener('DOMContentLoaded', init);
