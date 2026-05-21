// ========================================
// RESUME AI - MAIN JAVASCRIPT (COMPLETE)
// ========================================

const BACKEND_URL = 'https://resume-analyzer-rag-production.up.railway.app';
let currentResult = null;
let analysisHistory = [];
let authToken = localStorage.getItem('authToken');
let currentUser = null;

// ========================================
// AUTHENTICATION CHECK FUNCTION
// ========================================

function checkAuthAndRedirect() {
    if (!authToken) {
        showToast('Please login to use the analyzer', 'error');
        openAuthModal('login');
        return false;
    }
    return true;
}

function isAuthenticated() {
    return authToken !== null;
}

// ========================================
// ROBOT ANIMATION FUNCTIONS
// ========================================

function startRobotAnalysis() {
    const screenText = document.querySelector('.screen-text');
    const robotHead = document.querySelector('.robot-head');
    
    if (screenText) screenText.textContent = '🔍 ANALYZING...';
    if (robotHead) {
        robotHead.style.animation = 'robotGlow 0.3s ease-in-out infinite';
    }
}

function stopRobotAnalysis() {
    const screenText = document.querySelector('.screen-text');
    const robotHead = document.querySelector('.robot-head');
    
    if (screenText) screenText.textContent = '✅ ANALYSIS DONE!';
    if (robotHead) {
        robotHead.style.animation = 'robotScan 3s linear infinite';
    }
    
    setTimeout(() => {
        if (screenText) screenText.textContent = 'AI ANALYZING...';
    }, 3000);
}

// ========================================
// PAGE LOAD
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('ResumeAI loaded');
    
    // Load saved history
    loadHistory();
    
    // Update stats on home page
    updateHomeStats();
    displayRecentHistory();
    
    // Setup navigation
    setupNavigation();
    
    // Setup analyzer if on analyzer page
    if (document.getElementById('uploadArea')) {
        setupUpload();
        setupTextarea();
    }
    
    // Setup FAQ toggles
    setupFAQ();
    
    // Check authentication
    if (authToken) {
        verifyToken();
    }
    
    // Update navbar buttons
    updateNavbarButtons();
    
    // Setup stars animation
    createStars();
    createShootingStars();
    createAIIcons();
    setupRobotInteraction();
});

// ========================================
// NAVIGATION
// ========================================
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const homeContainer = document.getElementById('homeContainer');
    const analyzerContainer = document.getElementById('analyzerContainer');
    const historyPage = document.getElementById('historyPage');
    const helpPage = document.getElementById('helpPage');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.getAttribute('data-page');
            
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            if (homeContainer) homeContainer.style.display = 'none';
            if (analyzerContainer) analyzerContainer.style.display = 'none';
            if (historyPage) historyPage.style.display = 'none';
            if (helpPage) helpPage.style.display = 'none';
            
            if (page === 'home' && homeContainer) {
                homeContainer.style.display = 'block';
                updateHomeStats();
                displayRecentHistory();
            } else if (page === 'analyzer' && analyzerContainer) {
                // Check authentication before showing analyzer
                if (checkAuthAndRedirect()) {
                    analyzerContainer.style.display = 'block';
                } else {
                    // Stay on home page
                    homeContainer.style.display = 'block';
                    document.querySelector('.nav-link[data-page="home"]').classList.add('active');
                    this.classList.remove('active');
                }
            } else if (page === 'history' && historyPage) {
                if (checkAuthAndRedirect()) {
                    historyPage.style.display = 'block';
                    displayFullHistory();
                } else {
                    homeContainer.style.display = 'block';
                    document.querySelector('.nav-link[data-page="home"]').classList.add('active');
                    this.classList.remove('active');
                }
            } else if (page === 'help' && helpPage) {
                helpPage.style.display = 'block';
            }
        });
    });
}

function switchToAnalyzer() {
    if (checkAuthAndRedirect()) {
        const analyzerLink = document.querySelector('.nav-link[data-page="analyzer"]');
        if (analyzerLink) analyzerLink.click();
    }
}

function switchToHome() {
    const homeLink = document.querySelector('.nav-link[data-page="home"]');
    if (homeLink) homeLink.click();
}

// ========================================
// UPLOAD FUNCTIONALITY
// ========================================
function setupUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('resumeFile');
    
    if (!uploadArea || !fileInput) return;
    
    uploadArea.onclick = () => {
        if (checkAuthAndRedirect()) {
            fileInput.click();
        }
    };
    
    fileInput.onchange = async (e) => {
        const file = e.target.files[0];
        if (file && checkAuthAndRedirect()) {
            await uploadFile(file);
        }
    };
}

async function uploadFile(file) {
    if (!checkAuthAndRedirect()) return;
    
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
        } else if (response.status === 401) {
            showToast('Session expired. Please login again.', 'error');
            logout();
            openAuthModal('login');
        } else {
            showToast(data.detail || 'Upload failed', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showToast('Connection error: ' + error.message, 'error');
    }
}

function clearResume() {
    document.getElementById('resumeInfo').style.display = 'none';
    document.getElementById('uploadArea').style.display = 'block';
    document.getElementById('resumeFile').value = '';
}

// ========================================
// TEXTAREA COUNTER
// ========================================
function setupTextarea() {
    const textarea = document.getElementById('jobDescription');
    if (!textarea) return;
    
    textarea.oninput = function() {
        const charCount = document.getElementById('charCount');
        const wordCount = document.getElementById('wordCount');
        if (charCount) charCount.innerHTML = this.value.length;
        if (wordCount) wordCount.innerHTML = this.value.split(/\s+/).filter(w => w.length).length;
    };
}

// ========================================
// ANALYZE FUNCTION
// ========================================
async function analyzeResume() {
    if (!checkAuthAndRedirect()) return;
    
    const jobDesc = document.getElementById('jobDescription').value;
    
    if (!jobDesc) {
        showToast('Please enter a job description', 'error');
        return;
    }
    
    const loading = document.getElementById('loadingOverlay');
    loading.style.display = 'flex';
    startRobotAnalysis();
    
    try {
        const response = await fetch(`${BACKEND_URL}/api/analyze`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                job_description: jobDesc, 
                token: authToken 
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentResult = data;
            displayResults(data);
            saveToHistory(data);
            showToast('Analysis complete!', 'success');
            stopRobotAnalysis();
        } else if (response.status === 401) {
            showToast('Session expired. Please login again.', 'error');
            logout();
            openAuthModal('login');
        } else {
            throw new Error(data.detail || 'Analysis failed');
        }
    } catch (error) {
        console.error('Analysis error:', error);
        showToast('Error: ' + error.message, 'error');
        stopRobotAnalysis();
    } finally {
        loading.style.display = 'none';
    }
}

function displayResults(data) {
    const resultsDiv = document.getElementById('resultsSection');
    if (!resultsDiv) return;
    
    resultsDiv.style.display = 'block';
    
    const score = data.match_score || 0;
    const missing = data.missing_keywords || [];
    
    document.getElementById('matchScore').innerHTML = score + '%';
    document.getElementById('scoreProgress').style.width = score + '%';
    document.getElementById('missingCount').innerHTML = missing.length;
    document.getElementById('sectionsMatched').innerHTML = data.relevant_chunks?.length || 0;
    document.getElementById('resumeLength').innerHTML = data.resume_length || 0;
    
    const keywordsDiv = document.getElementById('missingKeywords');
    if (keywordsDiv) {
        keywordsDiv.innerHTML = '';
        if (missing.length > 0) {
            missing.forEach(kw => {
                const tag = document.createElement('span');
                tag.className = 'keyword-tag';
                tag.innerHTML = kw;
                keywordsDiv.appendChild(tag);
            });
        } else {
            keywordsDiv.innerHTML = '<p>No missing keywords found!</p>';
        }
    }
    
    const analysisDiv = document.getElementById('analysisReport');
    if (analysisDiv) {
        analysisDiv.style.whiteSpace = 'pre-wrap';
        analysisDiv.style.fontFamily = 'monospace';
        analysisDiv.style.fontSize = '13px';
        analysisDiv.style.backgroundColor = 'rgba(0,0,0,0.2)';
        analysisDiv.style.padding = '15px';
        analysisDiv.style.borderRadius = '10px';
        analysisDiv.innerHTML = data.analysis || 'No analysis available';
    }
    
    resultsDiv.scrollIntoView({ behavior: 'smooth' });
}

// ========================================
// HISTORY FUNCTIONS
// ========================================
function saveToHistory(data) {
    const item = {
        id: Date.now(),
        date: new Date().toLocaleString(),
        score: data.match_score,
        missing: data.missing_keywords?.length || 0
    };
    analysisHistory.unshift(item);
    if (analysisHistory.length > 10) analysisHistory.pop();
    localStorage.setItem('resumeHistory', JSON.stringify(analysisHistory));
    
    updateHomeStats();
    displayRecentHistory();
}

function loadHistory() {
    const saved = localStorage.getItem('resumeHistory');
    if (saved) {
        analysisHistory = JSON.parse(saved);
    }
}

function updateHomeStats() {
    const avgScoreEl = document.getElementById('avgScoreHome');
    const totalEl = document.getElementById('totalAnalysesHome');
    const bestEl = document.getElementById('bestScoreHome');
    
    if (!avgScoreEl) return;
    
    if (analysisHistory.length === 0) {
        avgScoreEl.innerHTML = '0%';
        totalEl.innerHTML = '0';
        bestEl.innerHTML = '0%';
        return;
    }
    
    const total = analysisHistory.length;
    const avg = analysisHistory.reduce((sum, h) => sum + h.score, 0) / total;
    const best = Math.max(...analysisHistory.map(h => h.score));
    
    avgScoreEl.innerHTML = avg.toFixed(1) + '%';
    totalEl.innerHTML = total;
    bestEl.innerHTML = best + '%';
}

function displayRecentHistory() {
    const container = document.getElementById('recentHistory');
    if (!container) return;
    
    if (analysisHistory.length === 0) {
        container.innerHTML = '<div class="history-item">No recent analyses. Start analyzing!</div>';
        return;
    }
    
    container.innerHTML = analysisHistory.slice(0, 3).map(h => `
        <div class="history-item">
            <div><strong>${h.date}</strong></div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #6366f1;">${h.score}%</div>
            <div style="font-size: 0.7rem; color: #64748b;">${h.missing} keywords missing</div>
        </div>
    `).join('');
}

function displayFullHistory() {
    const container = document.getElementById('fullHistory');
    if (!container) return;
    
    if (analysisHistory.length === 0) {
        container.innerHTML = '<div class="history-item">No history yet. Start analyzing!</div>';
        return;
    }
    
    container.innerHTML = analysisHistory.map(h => `
        <div class="history-item">
            <div><strong>${h.date}</strong></div>
            <div style="font-size: 1.5rem; font-weight: 700; color: #6366f1;">${h.score}%</div>
            <div style="font-size: 0.7rem; color: #64748b;">${h.missing} keywords missing</div>
        </div>
    `).join('');
}

// ========================================
// REPORT FUNCTIONS
// ========================================
function downloadReport() {
    if (!currentResult) {
        showToast('No analysis to download', 'error');
        return;
    }
    
    const content = `RESUME ANALYSIS REPORT
Date: ${new Date().toLocaleString()}
Match Score: ${currentResult.match_score}%

Missing Keywords:
${currentResult.missing_keywords?.join(', ') || 'None'}

Analysis:
${currentResult.analysis}
`;
    
    const blob = new Blob([content], { type: 'text/plain' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `resume_analysis_${Date.now()}.txt`;
    link.click();
}

function copyReport() {
    if (!currentResult) {
        showToast('No analysis to copy', 'error');
        return;
    }
    
    const text = `Score: ${currentResult.match_score}%\nMissing: ${currentResult.missing_keywords?.join(', ')}\n\n${currentResult.analysis}`;
    navigator.clipboard.writeText(text);
    showToast('Copied to clipboard!', 'success');
}

// ========================================
// FAQ FUNCTIONS
// ========================================
function setupFAQ() {
    const faqQuestions = document.querySelectorAll('.faq-question');
    faqQuestions.forEach(question => {
        question.addEventListener('click', function() {
            const answer = this.nextElementSibling;
            answer.classList.toggle('show');
            const icon = this.querySelector('i');
            if (icon) {
                icon.style.transform = answer.classList.contains('show') ? 'rotate(180deg)' : 'rotate(0deg)';
            }
        });
    });
}

// ========================================
// TOAST NOTIFICATION
// ========================================
function showToast(message, type) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    toast.innerHTML = message;
    toast.style.background = type === 'success' ? '#48bb78' : type === 'error' ? '#ef4444' : '#6366f1';
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ========================================
// ANIMATED BACKGROUND FUNCTIONS
// ========================================

function createStars() {
    const starsContainer = document.getElementById('starsContainer');
    if (!starsContainer) return;
    
    starsContainer.innerHTML = '';
    const starCount = 150;
    
    for (let i = 0; i < starCount; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        
        const random = Math.random();
        if (random < 0.6) {
            star.classList.add('small');
        } else if (random < 0.85) {
            star.classList.add('medium');
        } else {
            star.classList.add('large');
        }
        
        star.style.left = Math.random() * 100 + '%';
        star.style.top = Math.random() * 100 + '%';
        star.style.animationDelay = Math.random() * 5 + 's';
        star.style.animationDuration = (Math.random() * 8 + 5) + 's';
        
        starsContainer.appendChild(star);
    }
}

function createShootingStars() {
    setInterval(() => {
        const starsContainer = document.getElementById('starsContainer');
        if (!starsContainer) return;
        
        const shootingStar = document.createElement('div');
        shootingStar.className = 'shooting-star';
        shootingStar.style.top = Math.random() * 50 + '%';
        shootingStar.style.left = Math.random() * 60 + 20 + '%';
        shootingStar.style.animationDelay = '0s';
        shootingStar.style.animationDuration = (Math.random() * 1 + 1.5) + 's';
        starsContainer.appendChild(shootingStar);
        
        setTimeout(() => {
            if (shootingStar && shootingStar.remove) {
                shootingStar.remove();
            }
        }, 3000);
    }, 8000);
}

function createAIIcons() {
    const icons = [
        'fa-brain', 'fa-robot', 'fa-microchip', 'fa-chart-line', 
        'fa-magic', 'fa-cogs', 'fa-database', 'fa-cloud-upload-alt',
        'fa-code', 'fa-terminal', 'fa-server', 'fa-shield-alt'
    ];
    
    setInterval(() => {
        const icon = document.createElement('div');
        icon.className = 'ai-icon';
        const randomIcon = icons[Math.floor(Math.random() * icons.length)];
        icon.innerHTML = `<i class="fas ${randomIcon}"></i>`;
        icon.style.left = Math.random() * 100 + '%';
        icon.style.animationDuration = 12 + Math.random() * 8 + 's';
        icon.style.animationDelay = '0s';
        document.body.appendChild(icon);
        
        setTimeout(() => {
            if (icon && icon.remove) {
                icon.remove();
            }
        }, 20000);
    }, 4000);
}

function setupRobotInteraction() {
    const robot = document.getElementById('robotContainer');
    if (!robot) return;
    
    const messages = [
        "🤖 Ready to analyze!",
        "📄 Upload your resume",
        "🎯 Finding the best match",
        "💡 AI analysis ready",
        "🚀 Let's optimize!"
    ];
    
    let messageIndex = 0;
    
    robot.addEventListener('click', () => {
        const screenText = document.querySelector('.screen-text');
        if (screenText) {
            screenText.textContent = messages[messageIndex % messages.length];
            messageIndex++;
            setTimeout(() => {
                screenText.textContent = 'AI ANALYZING...';
            }, 2000);
        }
    });
}

// ========================================
// AUTHENTICATION FUNCTIONS
// ========================================

function updateNavbarButtons() {
    const navButtons = document.querySelector('.nav-buttons');
    if (!navButtons) return;
    
    if (currentUser) {
        navButtons.innerHTML = `
            <span style="color: #6366f1; display: flex; align-items: center; gap: 8px;">
                <i class="fas fa-user-circle"></i> ${currentUser.name}
            </span>
            <button class="btn-outline-nav" onclick="logout()">
                <i class="fas fa-sign-out-alt"></i> Logout
            </button>
        `;
    } else {
        navButtons.innerHTML = `
            <button class="btn-outline-nav" onclick="openAuthModal('login')">
                <i class="fas fa-sign-in-alt"></i> Login
            </button>
            <button class="btn-primary-nav" onclick="openAuthModal('signup')">
                <i class="fas fa-user-plus"></i> Sign Up
            </button>
        `;
    }
}

function openAuthModal(type) {
    const modal = document.getElementById('authModal');
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    const modalTitle = document.getElementById('authModalTitle');
    
    if (type === 'login') {
        loginForm.style.display = 'block';
        signupForm.style.display = 'none';
        modalTitle.innerHTML = 'Login to ResumeAI';
    } else {
        loginForm.style.display = 'none';
        signupForm.style.display = 'block';
        modalTitle.innerHTML = 'Create Account';
    }
    
    modal.style.display = 'flex';
}

function closeAuthModal() {
    document.getElementById('authModal').style.display = 'none';
    document.getElementById('loginEmail').value = '';
    document.getElementById('loginPassword').value = '';
    document.getElementById('signupName').value = '';
    document.getElementById('signupEmail').value = '';
    document.getElementById('signupPassword').value = '';
    document.getElementById('signupConfirmPassword').value = '';
}

function switchToSignup() {
    openAuthModal('signup');
}

function switchToLogin() {
    openAuthModal('login');
}

async function registerUser() {
    const name = document.getElementById('signupName').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    const confirmPassword = document.getElementById('signupConfirmPassword').value;
    
    if (!name || !email || !password) {
        showToast('Please fill all fields', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showToast('Passwords do not match', 'error');
        return;
    }
    
    if (password.length < 6) {
        showToast('Password must be at least 6 characters', 'error');
        return;
    }
    
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
            showToast('Registration successful! Welcome ' + name, 'success');
            closeAuthModal();
            updateNavbarButtons();
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.detail || 'Registration failed', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function loginUser() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    if (!email || !password) {
        showToast('Please enter email and password', 'error');
        return;
    }
    
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
            showToast('Welcome back ' + currentUser.name + '!', 'success');
            closeAuthModal();
            updateNavbarButtons();
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.detail || 'Invalid credentials', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function logout() {
    try {
        await fetch(`${BACKEND_URL}/api/auth/logout`, { method: 'POST' });
    } catch (error) {}
    
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    showToast('Logged out successfully', 'success');
    updateNavbarButtons();
    
    // Redirect to home page
    switchToHome();
}

async function verifyToken() {
    if (!authToken) return;
    
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
// EXPORT FUNCTIONS FOR GLOBAL ACCESS
// ========================================
window.switchToAnalyzer = switchToAnalyzer;
window.switchToHome = switchToHome;
window.analyzeResume = analyzeResume;
window.clearResume = clearResume;
window.downloadReport = downloadReport;
window.copyReport = copyReport;
window.openAuthModal = openAuthModal;
window.closeAuthModal = closeAuthModal;
window.switchToSignup = switchToSignup;
window.switchToLogin = switchToLogin;
window.registerUser = registerUser;
window.loginUser = loginUser;
window.logout = logout;