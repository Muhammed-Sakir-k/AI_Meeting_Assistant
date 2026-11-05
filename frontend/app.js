// Global Variables
let currentMeetingId = null;
let statusInterval = null;

// DOM Elements
const uploadForm = document.getElementById('uploadForm');
const audioFileInput = document.getElementById('audioFile');
const meetingTitleInput = document.getElementById('meetingTitle');
const btnUpload = document.getElementById('btnUpload');
const searchQuery = document.getElementById('searchQuery');
const btnRefresh = document.getElementById('btnRefresh');
const meetingList = document.getElementById('meetingList');

const welcomeView = document.getElementById('welcomeView');
const meetingView = document.getElementById('meetingView');

const activeMeetingTitle = document.getElementById('activeMeetingTitle');
const activeMeetingDate = document.getElementById('activeMeetingDate');
const activeMeetingLang = document.getElementById('activeMeetingLang');
const activeMeetingConfidence = document.getElementById('activeMeetingConfidence');

const btnExportPdf = document.getElementById('btnExportPdf');
const btnExportDocx = document.getElementById('btnExportDocx');

const statusIndicator = document.getElementById('statusIndicator');
const statusMessage = document.getElementById('statusMessage');
const statusBar = document.getElementById('statusBar');

const summaryText = document.getElementById('summaryText');
const decisionsList = document.getElementById('decisionsList');
const actionItemsTableBody = document.getElementById('actionItemsTableBody');
const transcriptContent = document.getElementById('transcriptContent');

const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toastMessage');
const toastIcon = document.getElementById('toastIcon');

// Setup Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadMeetingHistory();
    
    uploadForm.addEventListener('submit', handleUpload);
    btnRefresh.addEventListener('click', loadMeetingHistory);
    searchQuery.addEventListener('input', debounce(handleSearch, 300));
    
    btnExportPdf.addEventListener('click', () => downloadReport('pdf'));
    btnExportDocx.addEventListener('click', () => downloadReport('docx'));
});

// Toast Notification System
function showToast(message, type = 'info') {
    toastMessage.textContent = message;
    
    // Set icons and borders
    toast.className = 'toast'; // Reset
    if (type === 'success') {
        toast.style.borderLeftColor = 'var(--success)';
        toastIcon.className = 'fa-solid fa-circle-check';
        toastIcon.style.color = 'var(--success)';
    } else if (type === 'error') {
        toast.style.borderLeftColor = 'var(--danger)';
        toastIcon.className = 'fa-solid fa-circle-exclamation';
        toastIcon.style.color = 'var(--danger)';
    } else if (type === 'warning') {
        toast.style.borderLeftColor = 'var(--warning)';
        toastIcon.className = 'fa-solid fa-triangle-exclamation';
        toastIcon.style.color = 'var(--warning)';
    } else {
        toast.style.borderLeftColor = 'var(--secondary)';
        toastIcon.className = 'fa-solid fa-circle-info';
        toastIcon.style.color = 'var(--secondary)';
    }
    
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 4000);
}

// Debounce helper for search
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Fetch and Render Meeting Sidebar List
async function loadMeetingHistory() {
    try {
        meetingList.innerHTML = '<div class="list-loader"><i class="fa-solid fa-spinner fa-spin"></i> Loading...</div>';
        const response = await fetch('/search?q=');
        if (!response.ok) throw new Error("Failed to load meetings.");
        
        const meetings = await response.json();
        renderMeetingList(meetings);
    } catch (error) {
        showToast("Error loading meeting history.", "error");
        meetingList.innerHTML = '<div class="list-loader">Failed to load history</div>';
    }
}

function renderMeetingList(meetings) {
    if (meetings.length === 0) {
        meetingList.innerHTML = '<div class="list-loader">No meetings found</div>';
        return;
    }
    
    meetingList.innerHTML = '';
    
    // Sort by meeting_id descending (newest first)
    meetings.sort((a, b) => b.meeting_id - a.meeting_id);
    
    meetings.forEach(m => {
        const li = document.createElement('li');
        li.className = `meeting-item ${m.meeting_id === currentMeetingId ? 'active' : ''}`;
        li.dataset.id = m.meeting_id;
        
        const dateObj = m.date ? new Date(m.date) : new Date();
        const formattedDate = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        
        li.innerHTML = `
            <div class="item-title">${escapeHtml(m.title)}</div>
            <div class="item-meta">
                <span>${formattedDate}</span>
                <span>${m.language ? m.language.toUpperCase() : 'EN'}</span>
            </div>
        `;
        
        li.addEventListener('click', () => selectMeeting(m.meeting_id));
        meetingList.appendChild(li);
    });
}

// Live Search Handler
async function handleSearch() {
    const query = searchQuery.value.trim();
    try {
        const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error("Search failed.");
        const meetings = await response.json();
        renderMeetingList(meetings);
    } catch (error) {
        console.error(error);
    }
}

// Handle Upload File Form Submission
async function handleUpload(e) {
    e.preventDefault();
    
    const file = audioFileInput.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    if (meetingTitleInput.value.trim()) {
        formData.append('title', meetingTitleInput.value.trim());
    }
    
    // Disable UI
    btnUpload.disabled = true;
    btnUpload.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Uploading...';
    showToast("Uploading audio file...", "info");
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        // Handle Duplicate Upload (HTTP 409 Conflict)
        if (response.status === 409) {
            const result = await response.json();
            showToast("Duplicate upload detected. Loading existing records.", "warning");
            selectMeeting(result.meeting_id);
            uploadForm.reset();
            loadMeetingHistory();
            return;
        }
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Upload failed.");
        }
        
        const result = await response.json();
        showToast("Audio uploaded. Starting pipeline...", "success");
        
        // Clear input form
        uploadForm.reset();
        
        // Refresh history to show the queued item
        await loadMeetingHistory();
        
        // Auto select and start polling for this new meeting
        selectMeeting(result.meeting_id);
        
    } catch (error) {
        showToast(error.message, "error");
    } finally {
        btnUpload.disabled = false;
        btnUpload.innerHTML = '<i class="fa-solid fa-play"></i> Process Audio';
    }
}

// Set Active Meeting and Load Dashboard
function selectMeeting(meetingId) {
    // Clear previous polling if active
    if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
    }
    
    currentMeetingId = meetingId;
    
    // Highlight selected in sidebar
    document.querySelectorAll('.meeting-item').forEach(item => {
        item.classList.remove('active');
        if (parseInt(item.dataset.id) === meetingId) {
            item.classList.add('active');
        }
    });
    
    // Switch views
    welcomeView.classList.add('hidden');
    meetingView.classList.remove('hidden');
    
    // Clear UI content to show loading state
    clearMeetingDetails();
    
    // Start tracking status and loading data
    pollPipelineStatus();
}

// Clear Dashboard Data Fields
function clearMeetingDetails() {
    activeMeetingTitle.textContent = "Loading meeting details...";
    activeMeetingDate.innerHTML = "";
    activeMeetingLang.innerHTML = "";
    activeMeetingConfidence.innerHTML = "";
    
    summaryText.textContent = "Waiting for analysis...";
    decisionsList.innerHTML = '<li>Waiting for analysis...</li>';
    actionItemsTableBody.innerHTML = '<tr><td colspan="3" class="list-loader">Waiting for analysis...</td></tr>';
    transcriptContent.innerHTML = '<div class="list-loader">Waiting for analysis...</div>';
    
    statusIndicator.classList.add('hidden');
}

// Mapping of Pipeline Stages to Progress Percentage
const STAGE_PROGRESS = {
    'queued': { pct: '10%', msg: 'Added to processing queue...' },
    'preprocessing': { pct: '30%', msg: 'Noise reduction and volume normalization in progress...' },
    'transcribing': { pct: '55%', msg: 'Running Whisper speech-to-text (Malayalam + English)...' },
    'nlp_extraction': { pct: '75%', msg: 'Analyzing context with BERT and mapping tasks with spaCy...' },
    'summarizing': { pct: '90%', msg: 'Generating executive summaries and key decisions...' },
    'saving': { pct: '95%', msg: 'Storing analysis results into the database...' },
    'completed': { pct: '100%', msg: 'Completed.' },
    'failed': { pct: '100%', msg: 'Processing failed.' }
};

// Check Pipeline Status & Poll until Complete
async function pollPipelineStatus() {
    const fetchStatus = async () => {
        try {
            const response = await fetch(`/status/${currentMeetingId}`);
            if (!response.ok) throw new Error("Could not check status.");
            
            const data = await response.json();
            const status = data.status.toLowerCase();
            const message = data.message;
            
            // Render Status Bar
            if (status !== 'completed' && !status.startsWith('failed')) {
                // In progress
                statusIndicator.classList.remove('hidden');
                
                const progressInfo = STAGE_PROGRESS[status] || { pct: '40%', msg: message };
                statusBar.style.width = progressInfo.pct;
                statusBar.style.background = 'linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%)';
                statusMessage.textContent = progressInfo.msg;
                
            } else if (status.startsWith('failed') || status === 'failed') {
                // Failed
                statusIndicator.classList.remove('hidden');
                statusBar.style.width = '100%';
                statusBar.style.background = 'var(--danger)';
                statusMessage.innerHTML = `<span style="color: var(--danger)"><i class="fa-solid fa-circle-exclamation"></i> ${message}</span>`;
                
                showToast("Meeting processing failed.", "error");
                clearInterval(statusInterval);
                statusInterval = null;
                
            } else if (status === 'completed') {
                // Completed successfully
                statusIndicator.classList.add('hidden');
                
                clearInterval(statusInterval);
                statusInterval = null;
                
                // Load actual DB values
                loadMeetingDetails();
            }
        } catch (error) {
            showToast("Failed to fetch pipeline status.", "error");
        }
    };
    
    // Run immediately first
    await fetchStatus();
    
    // Set Interval to poll every 2 seconds
    if (currentMeetingId) {
        statusInterval = setInterval(fetchStatus, 2000);
    }
}

// Load final parsed data from DB
async function loadMeetingDetails() {
    try {
        // 1. Fetch metadata (we do a search to get metadata like title, language, etc.)
        const responseHistory = await fetch(`/search?q=`);
        const meetings = await responseHistory.json();
        const meetingMeta = meetings.find(m => m.meeting_id === currentMeetingId);
        
        if (meetingMeta) {
            activeMeetingTitle.textContent = meetingMeta.title;
            const dateObj = meetingMeta.date ? new Date(meetingMeta.date) : new Date();
            activeMeetingDate.innerHTML = `<i class="fa-regular fa-calendar"></i> ${dateObj.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })}`;
            activeMeetingLang.innerHTML = `<i class="fa-solid fa-language"></i> ${meetingMeta.language ? meetingMeta.language.toUpperCase() : 'EN-US'}`;
        }
        
        // 2. Fetch Transcript
        const resTrans = await fetch(`/transcript/${currentMeetingId}`);
        if (resTrans.ok) {
            const trans = await resTrans.json();
            activeMeetingConfidence.innerHTML = `<i class="fa-solid fa-circle-check"></i> Conf: ${Math.round(parseFloat(trans.confidence_score) * 100)}%`;
            renderTranscript(trans.segments);
        }
        
        // 3. Fetch Summary & Decisions
        const resSum = await fetch(`/summary/${currentMeetingId}`);
        if (resSum.ok) {
            const sumData = await resSum.json();
            summaryText.textContent = sumData.summary_text;
            renderDecisions(sumData.key_decisions);
        }
        
        // 4. Fetch Action Items
        const resActions = await fetch(`/actions/${currentMeetingId}`);
        if (resActions.ok) {
            const actions = await resActions.json();
            renderActionItems(actions);
        }
        
    } catch (error) {
        showToast("Error loading meeting details.", "error");
    }
}

// Render Transcript Segments with Low Confidence Flagging
function renderTranscript(segments) {
    if (!segments || segments.length === 0) {
        transcriptContent.innerHTML = '<div class="list-loader">No transcript text segments loaded.</div>';
        return;
    }
    
    transcriptContent.innerHTML = '';
    
    segments.forEach(seg => {
        const segDiv = document.createElement('div');
        segDiv.className = 'transcript-segment';
        
        // Format Timestamp
        const minutes = Math.floor(seg.start / 60);
        const seconds = Math.floor(seg.start % 60);
        const timeStr = `[${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}]`;
        
        let textContent = escapeHtml(seg.text);
        
        // Flag Low Confidence Segment
        if (seg.is_low_confidence) {
            textContent = `
                <span class="low-confidence" title="Low confidence speech detection">
                    ${textContent}
                    <span class="low-confidence-badge">
                        <i class="fa-solid fa-triangle-exclamation"></i> review (${Math.round(seg.confidence * 100)}%)
                    </span>
                </span>
            `;
        }
        
        segDiv.innerHTML = `
            <div class="seg-time">${timeStr}</div>
            <div class="seg-text">${textContent}</div>
        `;
        transcriptContent.appendChild(segDiv);
    });
}

// Render Key Decisions
function renderDecisions(decisions) {
    if (!decisions || decisions.length === 0) {
        decisionsList.innerHTML = '<li style="color: var(--text-muted)">No specific decisions recorded.</li>';
        return;
    }
    
    decisionsList.innerHTML = '';
    decisions.forEach(dec => {
        const li = document.createElement('li');
        li.textContent = dec;
        decisionsList.appendChild(li);
    });
}

// Render Action Items Table
function renderActionItems(actions) {
    if (!actions || actions.length === 0) {
        actionItemsTableBody.innerHTML = '<tr><td colspan="3" class="list-loader" style="color: var(--text-muted)">No action items extracted.</td></tr>';
        return;
    }
    
    actionItemsTableBody.innerHTML = '';
    actions.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${escapeHtml(item.owner)}</td>
            <td>${escapeHtml(item.task)}</td>
            <td>${escapeHtml(item.deadline)}</td>
        `;
        actionItemsTableBody.appendChild(tr);
    });
}

// Trigger Report Downloads
function downloadReport(format) {
    if (!currentMeetingId) return;
    window.location.href = `/report/${currentMeetingId}?format=${format}`;
}

// HTML Escaping Utility
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}
