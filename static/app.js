// Main Application JavaScript

// Global Variables
let currentProject = null;
let currentFile = null;
let currentProcess = null;
let terminalOutput = '';
let fileTree = {};
let codeEditor = null;

// Initialize Application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    initializeParticles();
    initializeSidebar();
    initializeThemeToggle();
    initializeTooltips();
    initializeCharts();
    initializeModals();
});

// Initialize App
function initializeApp() {
    // Load user preferences
    loadUserPreferences();

    // Set up event listeners
    document.getElementById('newProjectBtn').addEventListener('click', showNewProjectModal);
    document.getElementById('notificationBtn').addEventListener('click', showNotifications);
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);

    // Initialize sections
    initializeProjectsSection();
    initializeTerminalSection();
    initializeFilesSection();
    initializeBotsSection();
    initializeResourcesSection();
    initializeSettingsSection();
}

// Initialize Particles
function initializeParticles() {
    const particlesContainer = document.getElementById('particles');
    if (!particlesContainer) return;

    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.classList.add('particle');
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;
        particle.style.animationDelay = `${Math.random() * 15}s`;
        particle.style.animationDuration = `${15 + Math.random() * 10}s`;
        particlesContainer.appendChild(particle);
    }
}

// Initialize Sidebar
function initializeSidebar() {
    const sidebarItems = document.querySelectorAll('.sidebar-item');
    sidebarItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();

            // Remove active class from all items
            sidebarItems.forEach(i => i.classList.remove('active'));

            // Add active class to clicked item
            this.classList.add('active');

            // Show corresponding section
            const section = this.getAttribute('data-section');
            showSection(section);

            // Handle logout
            if (section === 'logout') {
                logout();
            }
        });
    });
}

// Initialize Theme Toggle
function initializeThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    const currentTheme = localStorage.getItem('theme') || 'light';

    if (currentTheme === 'dark') {
        themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
    } else {
        themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
    }

    themeToggle.addEventListener('click', toggleTheme);
}

// Initialize Tooltips
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        const tooltip = document.createElement('div');
        tooltip.classList.add('tooltip');
        tooltip.textContent = element.getAttribute('data-tooltip');
        tooltip.style.position = 'absolute';
        tooltip.style.bottom = '100%';
        tooltip.style.right = '50%';
        tooltip.style.transform = 'translateX(50%)';
        tooltip.style.marginBottom = '0.5rem';
        tooltip.style.padding = '0.25rem 0.5rem';
        tooltip.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        tooltip.style.color = 'white';
        tooltip.style.borderRadius = '0.25rem';
        tooltip.style.fontSize = '0.875rem';
        tooltip.style.whiteSpace = 'nowrap';
        tooltip.style.display = 'none';

        element.style.position = 'relative';
        element.appendChild(tooltip);

        element.addEventListener('mouseenter', function() {
            tooltip.style.display = 'block';
        });

        element.addEventListener('mouseleave', function() {
            tooltip.style.display = 'none';
        });
    });
}

// Initialize Charts
function initializeCharts() {
    const ctx = document.getElementById('resourcesChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
            datasets: [{
                label: 'CPU',
                data: [30, 40, 60, 70, 50, 40],
                borderColor: 'rgb(102, 126, 234)',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4
            }, {
                label: 'RAM',
                data: [40, 50, 70, 80, 60, 50],
                borderColor: 'rgb(118, 75, 162)',
                backgroundColor: 'rgba(118, 75, 162, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#e2e8f0'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                }
            }
        }
    });
}

// Initialize Modals
function initializeModals() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        const closeBtn = modal.querySelector('.close-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                modal.classList.remove('show');
            });
        }

        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.classList.remove('show');
            }
        });
    });
}

// Show Section
function showSection(sectionName) {
    // Update page title
    const titles = {
        'projects': 'المشاريع',
        'terminal': 'الطرفية',
        'files': 'الملفات',
        'bots': 'البوتات',
        'resources': 'الموارد',
        'settings': 'الإعدادات'
    };

    document.getElementById('pageTitle').textContent = titles[sectionName] || 'لوحة التحكم';

    // Hide all sections
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => {
        section.style.display = 'none';
    });

    // Show selected section
    const selectedSection = document.getElementById(sectionName + 'Section');
    if (selectedSection) {
        selectedSection.style.display = 'block';
    }
}

// Initialize Projects Section
function initializeProjectsSection() {
    const projectCards = document.querySelectorAll('.project-card');
    projectCards.forEach(card => {
        const runBtn = card.querySelector('.run-btn');
        const stopBtn = card.querySelector('.stop-btn');
        const restartBtn = card.querySelector('.restart-btn');
        const killBtn = card.querySelector('.kill-btn');

        if (runBtn) {
            runBtn.addEventListener('click', function() {
                const projectId = card.getAttribute('data-project-id');
                runProject(projectId);
            });
        }

        if (stopBtn) {
            stopBtn.addEventListener('click', function() {
                const projectId = card.getAttribute('data-project-id');
                stopProject(projectId);
            });
        }

        if (restartBtn) {
            restartBtn.addEventListener('click', function() {
                const projectId = card.getAttribute('data-project-id');
                restartProject(projectId);
            });
        }

        if (killBtn) {
            killBtn.addEventListener('click', function() {
                const projectId = card.getAttribute('data-project-id');
                killProject(projectId);
            });
        }
    });
}

// Initialize Terminal Section
function initializeTerminalSection() {
    const terminalInput = document.getElementById('terminalInput');
    if (terminalInput) {
        terminalInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const command = terminalInput.value;
                executeTerminalCommand(command);
                terminalInput.value = '';
            }
        });
    }
}

// Initialize Files Section
function initializeFilesSection() {
    const fileTreeElement = document.getElementById('fileTree');
    if (fileTreeElement) {
        renderFileTree(fileTreeElement, fileTree);
    }

    const fileEditor = document.getElementById('fileEditor');
    if (fileEditor) {
        codeEditor = CodeMirror(fileEditor, {
            mode: 'python',
            theme: 'monokai',
            lineNumbers: true,
            autoCloseBrackets: true,
            matchBrackets: true,
            indentUnit: 4,
            tabSize: 4,
            lineWrapping: true
        });

        codeEditor.on('change', function() {
            saveFile(currentFile, codeEditor.getValue());
        });
    }

    const fileUpload = document.getElementById('fileUpload');
    if (fileUpload) {
        fileUpload.addEventListener('change', function(e) {
            const files = e.target.files;
            uploadFiles(files);
        });
    }
}

// Initialize Bots Section
function initializeBotsSection() {
    const botCards = document.querySelectorAll('.bot-card');
    botCards.forEach(card => {
        const runBtn = card.querySelector('.bot-run-btn');
        const stopBtn = card.querySelector('.bot-stop-btn');
        const restartBtn = card.querySelector('.bot-restart-btn');

        if (runBtn) {
            runBtn.addEventListener('click', function() {
                const botId = card.getAttribute('data-bot-id');
                runBot(botId);
            });
        }

        if (stopBtn) {
            stopBtn.addEventListener('click', function() {
                const botId = card.getAttribute('data-bot-id');
                stopBot(botId);
            });
        }

        if (restartBtn) {
            restartBtn.addEventListener('click', function() {
                const botId = card.getAttribute('data-bot-id');
                restartBot(botId);
            });
        }
    });
}

// Initialize Resources Section
function initializeResourcesSection() {
    const resourceCards = document.querySelectorAll('.resource-card');
    resourceCards.forEach(card => {
        const refreshBtn = card.querySelector('.refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', function() {
                updateResourceStats();
            });
        }
    });

    updateResourceStats();
}

// Initialize Settings Section
function initializeSettingsSection() {
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveSettings();
        });
    }

    // Load current settings
    loadSettings();
}

// Show New Project Modal
function showNewProjectModal() {
    const modal = document.getElementById('newProjectModal');
    if (modal) {
        modal.classList.add('show');
    }
}

// Show Notifications
function showNotifications() {
    const modal = document.getElementById('notificationsModal');
    if (modal) {
        modal.classList.add('show');
    }
}

// Toggle Theme
function toggleTheme() {
    const themeToggle = document.getElementById('themeToggle');
    const currentTheme = localStorage.getItem('theme') || 'light';

    if (currentTheme === 'light') {
        document.body.classList.add('dark');
        themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        localStorage.setItem('theme', 'dark');
    } else {
        document.body.classList.remove('dark');
        themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        localStorage.setItem('theme', 'light');
    }
}

// Load User Preferences
function loadUserPreferences() {
    const theme = localStorage.getItem('theme') || 'light';
    if (theme === 'dark') {
        document.body.classList.add('dark');
    }
}

// Save Settings
function saveSettings() {
    const settings = {
        theme: document.body.classList.contains('dark') ? 'dark' : 'light',
        notifications: document.getElementById('notificationsToggle').checked,
        autoSave: document.getElementById('autoSaveToggle').checked
    };

    localStorage.setItem('settings', JSON.stringify(settings));
    showToast('تم حفظ الإعدادات بنجاح', 'success');
}

// Load Settings
function loadSettings() {
    const settings = JSON.parse(localStorage.getItem('settings')) || {};

    if (settings.theme === 'dark') {
        document.body.classList.add('dark');
        document.getElementById('themeToggle').innerHTML = '<i class="fas fa-moon"></i>';
    }

    if (settings.notifications !== undefined) {
        document.getElementById('notificationsToggle').checked = settings.notifications;
    }

    if (settings.autoSave !== undefined) {
        document.getElementById('autoSaveToggle').checked = settings.autoSave;
    }
}

// Update Resource Stats
function updateResourceStats() {
    // Fetch and update resource stats
    fetch('/api/resources/stats')
        .then(response => response.json())
        .then(data => {
            // Update CPU
            document.getElementById('cpuPercent').textContent = data.cpu_percent.toFixed(1) + '%';
            document.getElementById('cpuBar').style.width = data.cpu_percent + '%';

            // Update RAM
            document.getElementById('ramPercent').textContent = data.ram_percent.toFixed(1) + '%';
            document.getElementById('ramBar').style.width = data.ram_percent + '%';

            // Update Disk
            document.getElementById('diskPercent').textContent = data.disk_percent.toFixed(1) + '%';
            document.getElementById('diskBar').style.width = data.disk_percent + '%';

            // Update Processes
            document.getElementById('processCount').textContent = data.processes;

            // Update Boot Time
            const bootDate = new Date(data.boot_time * 1000);
            document.getElementById('bootTime').textContent = bootDate.toLocaleString();
        })
        .catch(error => {
            console.error('Error fetching resource stats:', error);
        });
}

// Run Project
function runProject(projectId) {
    fetch(`/api/projects/${projectId}/run`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('تم تشغيل المشروع بنجاح', 'success');
            updateProjectStatus(projectId, 'running');
        } else {
            showToast(data.message || 'فشل تشغيل المشروع', 'error');
        }
    })
    .catch(error => {
        console.error('Error running project:', error);
        showToast('حدث خطأ أثناء تشغيل المشروع', 'error');
    });
}

// Stop Project
function stopProject(projectId) {
    fetch(`/api/projects/${projectId}/stop`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('تم إيقاف المشروع بنجاح', 'success');
            updateProjectStatus(projectId, 'stopped');
        } else {
            showToast(data.message || 'فشل إيقاف المشروع', 'error');
        }
    })
    .catch(error => {
        console.error('Error stopping project:', error);
        showToast('حدث خطأ أثناء إيقاف المشروع', 'error');
    });
}

// Restart Project
function restartProject(projectId) {
    fetch(`/api/projects/${projectId}/restart`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('تم إعادة تشغيل المشروع بنجاح', 'success');
            updateProjectStatus(projectId, 'running');
        } else {
            showToast(data.message || 'فشل إعادة تشغيل المشروع', 'error');
        }
    })
    .catch(error => {
        console.error('Error restarting project:', error);
        showToast('حدث خطأ أثناء إعادة تشغيل المشروع', 'error');
    });
}

// Kill Project
function killProject(projectId) {
    fetch(`/api/projects/${projectId}/kill`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('تم إنهاء المشروع بنجاح', 'success');
            updateProjectStatus(projectId, 'stopped');
        } else {
            showToast(data.message || 'فشل إنهاء المشروع', 'error');
        }
    })
    .catch(error => {
        console.error('Error killing project:', error);
        showToast('حدث خطأ أثناء إنهاء المشروع', 'error');
    });
}

// Update Project Status
function updateProjectStatus(projectId, status) {
    const card = document.querySelector(`[data-project-id="${projectId}"]`);
    if (!card) return;

    const statusBadge = card.querySelector('.status-badge');
    if (statusBadge) {
        statusBadge.textContent = status === 'running' ? 'يعمل' : 'متوقف';
        statusBadge.className = 'status-badge px-2 py-1 rounded-full text-xs ' + 
            (status === 'running' ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400');
    }

    const runBtn = card.querySelector('.run-btn');
    const stopBtn = card.querySelector('.stop-btn');

    if (runBtn && stopBtn) {
        if (status === 'running') {
            runBtn.style.display = 'none';
            stopBtn.style.display = 'inline-block';
        } else {
            runBtn.style.display = 'inline-block';
            stopBtn.style.display = 'none';
        }
    }
}

// Execute Terminal Command
function executeTerminalCommand(command) {
    const terminalOutput = document.getElementById('terminalOutput');
    if (!terminalOutput) return;

    // Add command to output
    terminalOutput.innerHTML += `<div class="terminal-prompt">$ ${command}</div>`;

    // Send command to server
    fetch('/api/terminal/execute', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ command: command })
    })
    .then(response => response.json())
    .then(data => {
        // Add output to terminal
        terminalOutput.innerHTML += `<div class="terminal-output">${data.output}</div>`;
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    })
    .catch(error => {
        console.error('Error executing command:', error);
        terminalOutput.innerHTML += `<div class="text-red-400">Error: ${error.message}</div>`;
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    });
}

// Render File Tree
function renderFileTree(container, treeData) {
    container.innerHTML = '';

    for (const [name, data] of Object.entries(treeData)) {
        const item = document.createElement('div');
        item.className = 'file-tree-item';

        if (data.type === 'folder') {
            const folderIcon = document.createElement('i');
            folderIcon.className = 'fas fa-folder text-yellow-400 ml-2';
            item.appendChild(folderIcon);

            const folderName = document.createElement('span');
            folderName.textContent = name;
            item.appendChild(folderName);

            const folderContents = document.createElement('div');
            folderContents.className = 'file-tree-folder';

            item.addEventListener('click', function() {
                folderContents.classList.toggle('open');
                folderIcon.classList.toggle('fa-folder-open');
            });

            container.appendChild(item);
            container.appendChild(folderContents);

            renderFileTree(folderContents, data.contents);
        } else {
            const fileIcon = document.createElement('i');
            fileIcon.className = getFileIcon(data.extension);
            item.appendChild(fileIcon);

            const fileName = document.createElement('span');
            fileName.textContent = name;
            item.appendChild(fileName);

            item.addEventListener('click', function() {
                openFile(name, data);
            });

            container.appendChild(item);
        }
    }
}

// Get File Icon
function getFileIcon(extension) {
    const icons = {
        '.py': 'fas fa-file-code text-blue-400',
        '.js': 'fab fa-js text-yellow-400',
        '.html': 'fab fa-html5 text-orange-400',
        '.css': 'fab fa-css3-alt text-blue-500',
        '.json': 'fas fa-file-code text-green-400',
        '.md': 'fab fa-markdown text-gray-400',
        '.txt': 'fas fa-file-alt text-gray-300',
        '.zip': 'fas fa-file-archive text-yellow-600',
        '.pdf': 'fas fa-file-pdf text-red-500',
        '.jpg': 'fas fa-file-image text-purple-400',
        '.png': 'fas fa-file-image text-purple-400',
        '.gif': 'fas fa-file-image text-purple-400'
    };

    return icons[extension] || 'fas fa-file text-gray-300';
}

// Open File
function openFile(filename, fileData) {
    currentFile = filename;

    // Update file tree selection
    const fileItems = document.querySelectorAll('.file-tree-item');
    fileItems.forEach(item => {
        item.classList.remove('selected');
    });

    event.currentTarget.classList.add('selected');

    // Load file content
    fetch(`/api/files/${filename}`)
        .then(response => response.json())
        .then(data => {
            if (codeEditor) {
                codeEditor.setValue(data.content);
            }
        })
        .catch(error => {
            console.error('Error opening file:', error);
            showToast('حدث خطأ أثناء فتح الملف', 'error');
        });
}

// Save File
function saveFile(filename, content) {
    if (!filename || !content) return;

    fetch(`/api/files/${filename}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: content })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('تم حفظ الملف بنجاح', 'success');
        } else {
            showToast(data.message || 'فشل حفظ الملف', 'error');
        }
    })
    .catch(error => {
        console.error('Error saving file:', error);
        showToast('حدث خطأ أثناء حفظ الملف', 'error');
    });
}

// Upload Files
function uploadFiles(files) {
    const formData = new FormData();

    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    fetch('/api/files/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('تم رفع الملفات بنجاح', 'success');
            refreshFileTree();
        } else {
            showToast(data.message || 'فشل رفع الملفات', 'error');
        }
    })
    .catch(error => {
        console.error('Error uploading files:', error);
        showToast('حدث خطأ أثناء رفع الملفات', 'error');
    });
}

// Refresh File Tree
function refreshFileTree() {
    fetch('/api/files/tree')
        .then(response => response.json())
        .then(data => {
            fileTree = data;
            const fileTreeElement = document.getElementById('fileTree');
            if (fileTreeElement) {
                renderFileTree(fileTreeElement, fileTree);
            }
        })
        .catch(error => {
            console.error('Error refreshing file tree:', error);
        });
}

// Run Bot
function runBot(botId) {
    fetch(`/api/bots/${botId}/run`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('تم تشغيل البوت بنجاح', 'success');
            updateBotStatus(botId, 'online');
        } else {
            showToast(data.message || 'فشل تشغيل البوت', 'error');
        }
    })
    .catch(error => {
        console.error('Error running bot:', error);
        showToast('حدث خطأ أثناء تشغيل البوت', 'error');
    });
}

// Stop Bot
function stopBot(botId) {
    fetch(`/api/bots/${botId}/stop`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('تم إيقاف البوت بنجاح', 'success');
            updateBotStatus(botId, 'offline');
        } else {
            showToast(data.message || 'فشل إيقاف البوت', 'error');
        }
    })
    .catch(error => {
        console.error('Error stopping bot:', error);
        showToast('حدث خطأ أثناء إيقاف البوت', 'error');
    });
}

// Restart Bot
function restartBot(botId) {
    fetch(`/api/bots/${botId}/restart`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('تم إعادة تشغيل البوت بنجاح', 'success');
            updateBotStatus(botId, 'online');
        } else {
            showToast(data.message || 'فشل إعادة تشغيل البوت', 'error');
        }
    })
    .catch(error => {
        console.error('Error restarting bot:', error);
        showToast('حدث خطأ أثناء إعادة تشغيل البوت', 'error');
    });
}

// Update Bot Status
function updateBotStatus(botId, status) {
    const card = document.querySelector(`[data-bot-id="${botId}"]`);
    if (!card) return;

    const statusBadge = card.querySelector('.bot-status-badge');
    if (statusBadge) {
        statusBadge.textContent = status === 'online' ? 'متصل' : 'غير متصل';
        statusBadge.className = 'bot-status-badge px-2 py-1 rounded-full text-xs ' + 
            (status === 'online' ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400');
    }

    const runBtn = card.querySelector('.bot-run-btn');
    const stopBtn = card.querySelector('.bot-stop-btn');

    if (runBtn && stopBtn) {
        if (status === 'online') {
            runBtn.style.display = 'none';
            stopBtn.style.display = 'inline-block';
        } else {
            runBtn.style.display = 'inline-block';
            stopBtn.style.display = 'none';
        }
    }
}

// Show Toast Notification
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;

    toast.textContent = message;
    toast.className = 'toast ' + type;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Logout
function logout() {
    fetch('/api/auth/logout', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('تم تسجيل الخروج بنجاح', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        }
    })
    .catch(error => {
        console.error('Error logging out:', error);
        showToast('حدث خطأ أثناء تسجيل الخروج', 'error');
    });
}

// Auto-save files
let autoSaveInterval;
function startAutoSave() {
    if (autoSaveInterval) clearInterval(autoSaveInterval);

    autoSaveInterval = setInterval(() => {
        if (currentFile && codeEditor) {
            saveFile(currentFile, codeEditor.getValue());
        }
    }, 30000); // Auto-save every 30 seconds
}

function stopAutoSave() {
    if (autoSaveInterval) {
        clearInterval(autoSaveInterval);
        autoSaveInterval = null;
    }
}

// Initialize auto-save
const autoSaveToggle = document.getElementById('autoSaveToggle');
if (autoSaveToggle) {
    autoSaveToggle.addEventListener('change', function() {
        if (this.checked) {
            startAutoSave();
        } else {
            stopAutoSave();
        }
    });
}
