// ========================================
// RESUME AI - COMPLETE WORKING FRONTEND
// ========================================

const BACKEND_URL = 'https://resume-analyzer-rag-production.up.railway.app';

let authToken = localStorage.getItem('authToken');
let currentUser = null;

// ========================================
// PAGE LOAD
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('ResumeAI loaded');
    
    if (authToken) {
        verifyToken();
    }
    
    updateNavbarButtons();
    
    // Setup upload and analyze if on analyzer page
    if (document.getElementById('uploadArea')) {
        setupUpload();
        setupAnalyze();
    }
});

// ========================================
// NAVBAR BUTTONS
// ========================================
function updateNavbarButtons() {
    const navButtons = document.querySelector('.nav-buttons');
    if (!navButtons) return;
    
    if (currentUser) {
        navButtons.innerHTML = `
            <span style="color: #6366f1;">👤 ${currentUser.name}</span>
            <button class="btn-outline-nav" onclick="logout()">Logout</button>
        `;
    } else {
        navButtons.innerHTML = `
            <button class="btn-outline-nav" onclick="showLoginModal()">Login</button>
            <button class="btn-primary-nav" onclick="showRegisterModal()">Sign Up</button>
        `;
    }
}

// ========================================
// LOGIN MODAL
// ========================================
function showLoginModal() {
    const email = prompt('Enter your email:');
    if (!email) return;
    const password = prompt('Enter your password:');
    if (!password) return;
    login(email, password);
}

function showRegisterModal() {
    const name = prompt('Enter your name:');
    if (!name) return;
    const email = prompt('Enter your email:');
    if (!email) return;
    const password = prompt('Enter your password (min 6 characters):');
    if (!password || password.length < 6) {
        alert('Password must be at least 6 characters');
        return;
    }
    register(name, email, password);
}

// ========================================
// REGISTER
// ========================================
async function register(name, email, password) {
    showToast('Registering...', 'info');
    
    try {
        const response = await fetch(`${BACKEND_URL}/api/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            showToast('Registration successful!', 'success');
            updateNavbarButtons();
            location.reload();
        } else {
            showToast(data.detail || 'Registration failed', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// ========================================
// LOGIN
// ========================================
async function login(email, password) {
    showToast('Logging in...', 'info');
    
    try {
        const response = await fetch(`${BACKEND_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            showToast('Login successful!', 'success');
            updateNavbarButtons();
            location.reload();
        } else {
            showToast(data.detail || 'Login failed', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// ========================================
// LOGOUT
// ========================================
async function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    showToast('Logged out', 'success');
    updateNavbarButtons();
    location.reload();
}

// ========================================
// VERIFY TOKEN
// ========================================
async function verifyToken() {
    try {
        const response = await fetch(`${BACKEND_URL}/api/auth/verify?token=${authToken}`);
        const data = await response.json();
        
        if (data.valid) {
            currentUser = data.user;
            updateNavbarButtons();
        } else {
            logout();
        }
    } catch (error) {
        logout();
    }
}

// ========================================
// UPLOAD SETUP
// ========================================
function setupUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('resumeFile');
    
    if (!uploadArea || !fileInput) return;
    
    uploadArea.onclick = () => {
        if (authToken) {
            fileInput.click();
        } else {
            showToast('Please login first', 'error');
            showLoginModal();
        }
    };
    
    fileInput.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        showToast('Uploading...', 'info');
        
        try {
            const response = await fetch(`${BACKEND_URL}/api/upload?token=${authToken}`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                document.getElementById('resumeName').innerHTML = file.name;
                document.getElementById('resumeInfo').style.display = 'flex';
                document.getElementById('uploadArea').style.display = 'none';
                showToast('Resume uploaded!', 'success');
            } else {
                showToast(data.detail || 'Upload failed', 'error');
            }
        } catch (error) {
            showToast('Error: ' + error.message, 'error');
        }
    };
}

// ========================================
// ANALYZE SETUP
// ========================================
function setupAnalyze() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (!analyzeBtn) return;
    
    analyzeBtn.onclick = async () => {
        const jobDesc = document.getElementById('jobDescription').value;
        
        if (!jobDesc) {
            showToast('Please enter a job description', 'error');
            return;
        }
        
        if (!authToken) {
            showToast('Please login first', 'error');
            showLoginModal();
            return;
        }
        
        showToast('Analyzing...', 'info');
        
        try {
            const response = await fetch(`${BACKEND_URL}/api/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ job_description: jobDesc, token: authToken })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                displayResults(data);
                showToast('Analysis complete!', 'success');
            } else {
                showToast(data.detail || 'Analysis failed', 'error');
            }
        } catch (error) {
            showToast('Error: ' + error.message, 'error');
        }
    };
}

// ========================================
// DISPLAY RESULTS
// ========================================
function displayResults(data) {
    const resultsDiv = document.getElementById('resultsSection');
    if (!resultsDiv) return;
    
    resultsDiv.style.display = 'block';
    
    document.getElementById('matchScore').innerHTML = data.match_score + '%';
    document.getElementById('scoreProgress').style.width = data.match_score + '%';
    document.getElementById('missingCount').innerHTML = data.missing_keywords?.length || 0;
    document.getElementById('resumeLength').innerHTML = data.resume_length || 0;
    
    const keywordsDiv = document.getElementById('missingKeywords');
    if (keywordsDiv) {
        keywordsDiv.innerHTML = '';
        if (data.missing_keywords && data.missing_keywords.length > 0) {
            data.missing_keywords.forEach(kw => {
                const tag = document.createElement('span');
                tag.className = 'keyword-tag';
                tag.innerHTML = kw;
                keywordsDiv.appendChild(tag);
            });
        }
    }
    
    const analysisDiv = document.getElementById('analysisReport');
    if (analysisDiv) {
        analysisDiv.style.whiteSpace = 'pre-wrap';
        analysisDiv.style.fontFamily = 'monospace';
        analysisDiv.style.fontSize = '13px';
        analysisDiv.style.padding = '15px';
        analysisDiv.innerHTML = data.analysis || 'No analysis available';
    }
    
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
}

// ========================================
// TOAST NOTIFICATION
// ========================================
function showToast(message, type) {
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.style.position = 'fixed';
        toast.style.bottom = '20px';
        toast.style.right = '20px';
        toast.style.padding = '12px 20px';
        toast.style.borderRadius = '8px';
        toast.style.color = 'white';
        toast.style.zIndex = '9999';
        document.body.appendChild(toast);
    }
    
    toast.style.backgroundColor = type === 'success' ? '#48bb78' : type === 'error' ? '#ef4444' : '#6366f1';
    toast.innerHTML = message;
    toast.style.display = 'block';
    
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

// ========================================
// GLOBAL FUNCTIONS
// ========================================
window.showLoginModal = showLoginModal;
window.showRegisterModal = showRegisterModal;
window.logout = logout;
window.clearResume = function() {
    document.getElementById('resumeInfo').style.display = 'none';
    document.getElementById('uploadArea').style.display = 'block';
    document.getElementById('resumeFile').value = '';
};