// Health Monitor Pro - Custom JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });

    // Form validation enhancement
    enhanceForms();

    // Real-time health calculations
    setupHealthCalculators();

    // Auto-dismiss alerts after 5 seconds
    autoDismissAlerts();

    // Smooth scrolling for anchor links
    smoothScroll();

    // Password strength checker
    setupPasswordStrength();

    // Metric filtering
    setupMetricFilters();
});

// Form Enhancement
function enhanceForms() {
    const forms = document.querySelectorAll('form');

    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            }
        });
    });
}

// Health Calculators
function setupHealthCalculators() {
    // BMI Calculator
    const weightInput = document.getElementById('weight');
    const heightInput = document.getElementById('height');
    const bmiResult = document.getElementById('bmiResult');

    if (weightInput && heightInput && bmiResult) {
        function calculateBMI() {
            const weight = parseFloat(weightInput.value);
            const height = parseFloat(heightInput.value);

            if (weight && height) {
                const heightM = height / 100;
                const bmi = weight / (heightM * heightM);
                let category = '';
                let color = 'success';

                if (bmi < 18.5) {
                    category = 'Underweight';
                    color = 'warning';
                } else if (bmi < 25) {
                    category = 'Normal';
                    color = 'success';
                } else if (bmi < 30) {
                    category = 'Overweight';
                    color = 'warning';
                } else {
                    category = 'Obese';
                    color = 'danger';
                }

                bmiResult.innerHTML = `<strong>BMI: ${bmi.toFixed(1)}</strong> - <span class="text-${color}">${category}</span>`;
                bmiResult.classList.remove('d-none');
            } else {
                bmiResult.classList.add('d-none');
            }
        }

        weightInput.addEventListener('input', calculateBMI);
        heightInput.addEventListener('input', calculateBMI);
    }

    // Blood Pressure Calculator
    const systolicInput = document.getElementById('systolic');
    const diastolicInput = document.getElementById('diastolic');
    const bpResult = document.getElementById('bpResult');

    if (systolicInput && diastolicInput && bpResult) {
        function calculateBP() {
            const systolic = parseInt(systolicInput.value);
            const diastolic = parseInt(diastolicInput.value);

            if (systolic && diastolic) {
                let category = '';
                let color = 'success';

                if (systolic < 90 || diastolic < 60) {
                    category = 'Low Blood Pressure';
                    color = 'warning';
                } else if (systolic <= 120 && diastolic <= 80) {
                    category = 'Normal';
                    color = 'success';
                } else if (systolic <= 129 && diastolic <= 80) {
                    category = 'Elevated';
                    color = 'warning';
                } else if (systolic <= 139 || diastolic <= 89) {
                    category = 'Stage 1 Hypertension';
                    color = 'danger';
                } else {
                    category = 'Stage 2 Hypertension';
                    color = 'danger';
                }

                bpResult.innerHTML = `<span class="text-${color}">${category}</span>`;
                bpResult.classList.remove('d-none');
            } else {
                bpResult.classList.add('d-none');
            }
        }

        systolicInput.addEventListener('input', calculateBP);
        diastolicInput.addEventListener('input', calculateBP);
    }
}

// Auto-dismiss alerts
function autoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');

    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

// Smooth scrolling
function smoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Password strength checker
function setupPasswordStrength() {
    const passwordInput = document.getElementById('password');
    const strengthBar = document.getElementById('password-strength-bar');
    const strengthText = document.getElementById('password-strength-text');

    if (passwordInput && strengthBar && strengthText) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            let strength = 0;
            let color = 'danger';
            let text = 'Very Weak';

            // Length check
            if (password.length >= 8) strength += 25;
            if (password.length >= 12) strength += 25;

            // Complexity checks
            if (/[A-Z]/.test(password)) strength += 25;
            if (/[0-9]/.test(password)) strength += 25;
            if (/[^A-Za-z0-9]/.test(password)) strength += 25;

            // Cap at 100
            strength = Math.min(strength, 100);

            // Determine color and text
            if (strength >= 75) {
                color = 'success';
                text = 'Strong';
            } else if (strength >= 50) {
                color = 'warning';
                text = 'Medium';
            } else if (strength >= 25) {
                color = 'info';
                text = 'Weak';
            }

            // Update UI
            strengthBar.style.width = `${strength}%`;
            strengthBar.className = `progress-bar bg-${color}`;
            strengthText.textContent = `Strength: ${text}`;
            strengthText.className = `text-${color}`;
        });
    }
}

// Metric filtering
function setupMetricFilters() {
    const filterButtons = document.querySelectorAll('.metric-filter');
    const metricCards = document.querySelectorAll('.metric-card');

    if (filterButtons.length && metricCards.length) {
        filterButtons.forEach(button => {
            button.addEventListener('click', function() {
                const filterType = this.dataset.filter;

                // Update active button
                filterButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');

                // Filter cards
                metricCards.forEach(card => {
                    if (filterType === 'all' || card.dataset.type === filterType) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        });
    }
}

// Chart utilities
function createHealthChart(ctx, type, data, options = {}) {
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom'
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                }
            },
            x: {
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                }
            }
        }
    };

    const mergedOptions = { ...defaultOptions, ...options };

    return new Chart(ctx, {
        type: type,
        data: data,
        options: mergedOptions
    });
}

// Export data function
function exportData(format) {
    const data = {
        user: document.querySelector('.user-name')?.textContent || 'User',
        exportDate: new Date().toISOString(),
        metrics: []
    };

    // Collect metric data
    document.querySelectorAll('.metric-row').forEach(row => {
        const metric = {
            type: row.dataset.type,
            value: row.dataset.value,
            date: row.dataset.date,
            status: row.dataset.status
        };
        data.metrics.push(metric);
    });

    let content, mimeType, filename;

    switch(format) {
        case 'csv':
            content = convertToCSV(data);
            mimeType = 'text/csv';
            filename = `health-data-${new Date().toISOString().split('T')[0]}.csv`;
            break;
        case 'json':
            content = JSON.stringify(data, null, 2);
            mimeType = 'application/json';
            filename = `health-data-${new Date().toISOString().split('T')[0]}.json`;
            break;
        default:
            console.error('Unsupported format');
            return;
    }

    downloadFile(content, filename, mimeType);
}

function convertToCSV(data) {
    const headers = ['Type', 'Value', 'Date', 'Status'];
    const rows = data.metrics.map(metric => [
        metric.type,
        metric.value,
        metric.date,
        metric.status
    ]);

    return [
        headers.join(','),
        ...rows.map(row => row.join(','))
    ].join('\n');
}

function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Real-time data updates
function startRealTimeUpdates() {
    // This would typically connect to a WebSocket for real-time updates
    // For now, we'll simulate with periodic AJAX calls
    if (window.location.pathname === '/dashboard' || window.location.pathname === '/metrics') {
        setInterval(fetchLatestMetrics, 30000); // Every 30 seconds
    }
}

function fetchLatestMetrics() {
    fetch('/api/metrics?limit=1')
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                const latestMetric = data[0];
                updateMetricDisplay(latestMetric);
            }
        })
        .catch(error => console.error('Error fetching metrics:', error));
}

function updateMetricDisplay(metric) {
    // Update UI with latest metric
    const metricElement = document.querySelector(`[data-metric-id="${metric.id}"]`);
    if (metricElement) {
        metricElement.querySelector('.metric-value').textContent = metric.value;
        metricElement.querySelector('.metric-time').textContent =
            new Date(metric.date).toLocaleTimeString();
    }
}

// Initialize real-time updates
startRealTimeUpdates();