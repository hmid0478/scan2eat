/**
 * Scan2Eat - Main JavaScript File
 * Handles all client-side functionality
 */

// ==================== UTILITY FUNCTIONS ====================

const Utils = {
    // Format currency
    formatCurrency: (amount) => {
        return `Rs. ${parseFloat(amount).toFixed(2)}`;
    },

    // Format date
    formatDate: (dateString) => {
        const options = { day: '2-digit', month: 'short', year: 'numeric' };
        return new Date(dateString).toLocaleDateString('en-IN', options);
    },

    // Format time
    formatTime: (dateString) => {
        const options = { hour: '2-digit', minute: '2-digit', hour12: true };
        return new Date(dateString).toLocaleTimeString('en-IN', options).toLowerCase();
    },

    // Debounce function for search
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Show loading spinner
    showLoading: (element) => {
        element.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
    },

    // API call wrapper
    async apiCall(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            Toast.show('Network error. Please try again.', 'error');
            throw error;
        }
    }
};

// ==================== TOAST NOTIFICATION SYSTEM ====================

const Toast = {
    container: null,

    init() {
        // Create toast container if not exists
        if (!document.getElementById('toast-container')) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'toast-container position-fixed top-0 end-0 p-3';
            this.container.style.zIndex = '9999';
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('toast-container');
        }
    },

    show(message, type = 'info', duration = 4000) {
        if (!this.container) this.init();

        const toastId = 'toast-' + Date.now();
        const bgClass = {
            'success': 'bg-success',
            'error': 'bg-danger',
            'warning': 'bg-warning',
            'info': 'bg-info'
        }[type] || 'bg-info';

        const iconClass = {
            'success': 'bi-check-circle-fill',
            'error': 'bi-x-circle-fill',
            'warning': 'bi-exclamation-triangle-fill',
            'info': 'bi-info-circle-fill'
        }[type] || 'bi-info-circle-fill';

        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi ${iconClass} me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        this.container.insertAdjacentHTML('beforeend', toastHTML);
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: duration });
        toast.show();

        // Remove from DOM after hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
};

// ==================== FORM VALIDATION ====================

const FormValidator = {
    init() {
        // Add validation to all forms with 'needs-validation' class
        document.querySelectorAll('form.needs-validation').forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });

        // Real-time validation for specific fields
        this.setupRealTimeValidation();
    },

    setupRealTimeValidation() {
        // Roll number validation
        const rollNumberInput = document.getElementById('roll_number');
        if (rollNumberInput) {
            rollNumberInput.addEventListener('input', (e) => {
                const value = e.target.value.trim();
                const feedback = e.target.nextElementSibling?.nextElementSibling;

                if (value.length < 3) {
                    e.target.classList.add('is-invalid');
                    e.target.classList.remove('is-valid');
                } else {
                    e.target.classList.remove('is-invalid');
                    e.target.classList.add('is-valid');

                    // Check if roll number exists (debounced)
                    this.checkRollNumberExists(value);
                }
            });
        }

        // Password strength indicator
        const passwordInput = document.getElementById('password');
        if (passwordInput) {
            passwordInput.addEventListener('input', (e) => {
                this.updatePasswordStrength(e.target.value);
            });
        }

        // Amount validation
        const amountInput = document.getElementById('amount');
        if (amountInput) {
            amountInput.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                if (value <= 0 || isNaN(value)) {
                    e.target.classList.add('is-invalid');
                    e.target.classList.remove('is-valid');
                } else {
                    e.target.classList.remove('is-invalid');
                    e.target.classList.add('is-valid');
                }
            });
        }
    },

    checkRollNumberExists: Utils.debounce(async (rollNumber) => {
        try {
            const response = await fetch(`/api/check-roll-number?roll=${rollNumber}`);
            const data = await response.json();

            const input = document.getElementById('roll_number');
            const feedback = document.createElement('div');

            // Remove existing feedback
            const existingFeedback = input.parentElement.querySelector('.roll-feedback');
            if (existingFeedback) existingFeedback.remove();

            feedback.className = 'roll-feedback small mt-1';

            if (data.exists) {
                feedback.className += ' text-danger';
                feedback.innerHTML = '<i class="bi bi-x-circle me-1"></i>Roll number already registered';
                input.classList.add('is-invalid');
                input.classList.remove('is-valid');
            } else {
                feedback.className += ' text-success';
                feedback.innerHTML = '<i class="bi bi-check-circle me-1"></i>Roll number available';
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            }

            input.parentElement.appendChild(feedback);
        } catch (error) {
            console.error('Error checking roll number:', error);
        }
    }, 500),

    updatePasswordStrength(password) {
        let strength = 0;
        let feedback = [];

        if (password.length >= 8) strength++;
        else feedback.push('At least 8 characters');

        if (/[a-z]/.test(password)) strength++;
        else feedback.push('lowercase letter');

        if (/[A-Z]/.test(password)) strength++;
        else feedback.push('uppercase letter');

        if (/[0-9]/.test(password)) strength++;
        else feedback.push('number');

        if (/[^a-zA-Z0-9]/.test(password)) strength++;
        else feedback.push('special character');

        const strengthBar = document.getElementById('password-strength');
        if (strengthBar) {
            const percentage = (strength / 5) * 100;
            const colors = ['bg-danger', 'bg-danger', 'bg-warning', 'bg-info', 'bg-success'];
            const labels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];

            strengthBar.style.width = percentage + '%';
            strengthBar.className = 'progress-bar ' + colors[strength - 1];
            strengthBar.textContent = labels[strength - 1] || '';
        }
    }
};

// ==================== STUDENT MANAGEMENT ====================

const StudentManager = {
    async search(query) {
        const resultsContainer = document.getElementById('student-results');
        if (!resultsContainer) return;

        if (query.length < 2) {
            resultsContainer.innerHTML = '<p class="text-muted">Type at least 2 characters to search...</p>';
            return;
        }

        Utils.showLoading(resultsContainer);

        try {
            const response = await fetch(`/api/students/search?q=${encodeURIComponent(query)}`);
            const students = await response.json();
            this.renderStudentList(students, resultsContainer);
        } catch (error) {
            resultsContainer.innerHTML = '<p class="text-danger">Error loading students</p>';
        }
    },

    renderStudentList(students, container) {
        if (students.length === 0) {
            container.innerHTML = '<p class="text-muted">No students found</p>';
            return;
        }

        let html = '<div class="list-group">';
        students.forEach(student => {
            const balanceClass = student.wallet_balance > 100 ? 'success' :
                                student.wallet_balance > 0 ? 'warning' : 'danger';
            html += `
                <div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${student.name}</strong>
                        <small class="text-muted d-block">${student.username} | Room: ${student.room_number}</small>
                    </div>
                    <div class="text-end">
                        <span class="badge bg-${balanceClass}">${Utils.formatCurrency(student.wallet_balance)}</span>
                        <button class="btn btn-sm btn-outline-primary ms-2" onclick="StudentManager.showDetails('${student.id}')">
                            <i class="bi bi-eye"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        container.innerHTML = html;
    },

    async showDetails(studentId) {
        try {
            const response = await fetch(`/api/students/${studentId}`);
            const student = await response.json();

            const modalHTML = `
                <div class="modal fade" id="studentModal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title"><i class="bi bi-person me-2"></i>${student.name}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="row mb-3">
                                    <div class="col-6">
                                        <small class="text-muted">Roll Number</small>
                                        <p class="fw-bold mb-0">${student.username}</p>
                                    </div>
                                    <div class="col-6">
                                        <small class="text-muted">Room Number</small>
                                        <p class="fw-bold mb-0">${student.room_number}</p>
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-6">
                                        <small class="text-muted">Wallet Balance</small>
                                        <p class="fw-bold text-success mb-0">${Utils.formatCurrency(student.wallet_balance)}</p>
                                    </div>
                                    <div class="col-6">
                                        <small class="text-muted">Total Meals</small>
                                        <p class="fw-bold mb-0">${student.total_meals || 0}</p>
                                    </div>
                                </div>
                                ${student.qr_code_path ? `
                                    <div class="text-center">
                                        <img src="/static/${student.qr_code_path}" alt="QR Code" class="img-fluid" style="max-width: 150px;">
                                    </div>
                                ` : ''}
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Remove existing modal
            const existingModal = document.getElementById('studentModal');
            if (existingModal) existingModal.remove();

            document.body.insertAdjacentHTML('beforeend', modalHTML);
            const modal = new bootstrap.Modal(document.getElementById('studentModal'));
            modal.show();
        } catch (error) {
            Toast.show('Error loading student details', 'error');
        }
    },

    async addBalance(studentId, amount) {
        try {
            const response = await fetch('/api/students/add-balance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ student_id: studentId, amount: amount })
            });

            const result = await response.json();

            if (result.success) {
                Toast.show(`Added ${Utils.formatCurrency(amount)} to wallet`, 'success');
                // Refresh the page or update UI
                setTimeout(() => location.reload(), 1500);
            } else {
                Toast.show(result.message || 'Failed to add balance', 'error');
            }
        } catch (error) {
            Toast.show('Error adding balance', 'error');
        }
    }
};

// ==================== DASHBOARD CHARTS ====================

const DashboardCharts = {
    mealAttendanceChart: null,
    revenueChart: null,
    weeklyTrendChart: null,

    async init() {
        // Check if Chart.js is loaded
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js not loaded');
            return;
        }

        // Initialize charts based on available elements
        if (document.getElementById('mealAttendanceChart')) {
            await this.loadMealAttendanceChart();
        }

        if (document.getElementById('revenueChart')) {
            await this.loadRevenueChart();
        }

        if (document.getElementById('weeklyTrendChart')) {
            await this.loadWeeklyTrendChart();
        }
    },

    async loadMealAttendanceChart() {
        try {
            const response = await fetch('/api/stats/meal-attendance');
            const data = await response.json();

            const ctx = document.getElementById('mealAttendanceChart').getContext('2d');

            this.mealAttendanceChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Breakfast', 'Lunch', 'Dinner'],
                    datasets: [{
                        data: [data.breakfast || 0, data.lunch || 0, data.dinner || 0],
                        backgroundColor: ['#ffc107', '#28a745', '#007bff'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error loading meal attendance chart:', error);
        }
    },

    async loadRevenueChart() {
        try {
            const response = await fetch('/api/stats/revenue');
            const data = await response.json();

            const ctx = document.getElementById('revenueChart').getContext('2d');

            this.revenueChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: 'Revenue (Rs.)',
                        data: data.values || [],
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: (value) => 'Rs. ' + value
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error loading revenue chart:', error);
        }
    },

    async loadWeeklyTrendChart() {
        try {
            const response = await fetch('/api/stats/weekly-trend');
            const data = await response.json();

            const ctx = document.getElementById('weeklyTrendChart').getContext('2d');

            this.weeklyTrendChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: 'Attendance',
                        data: data.values || [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error loading weekly trend chart:', error);
        }
    }
};

// ==================== MEAL MANAGEMENT ====================

const MealManager = {
    async deleteMeal(mealId) {
        if (!confirm('Are you sure you want to delete this meal?')) return;

        try {
            const response = await fetch(`/api/meals/${mealId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                Toast.show('Meal deleted successfully', 'success');
                // Remove the row from table
                const row = document.querySelector(`tr[data-meal-id="${mealId}"]`);
                if (row) {
                    row.style.transition = 'opacity 0.3s';
                    row.style.opacity = '0';
                    setTimeout(() => row.remove(), 300);
                }
            } else {
                Toast.show(result.message || 'Failed to delete meal', 'error');
            }
        } catch (error) {
            Toast.show('Error deleting meal', 'error');
        }
    },

    async toggleMealStatus(mealId, isActive) {
        try {
            const response = await fetch(`/api/meals/${mealId}/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: !isActive })
            });

            const result = await response.json();

            if (result.success) {
                Toast.show(`Meal ${isActive ? 'deactivated' : 'activated'}`, 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                Toast.show(result.message || 'Failed to update meal', 'error');
            }
        } catch (error) {
            Toast.show('Error updating meal', 'error');
        }
    }
};

// ==================== REPORTS ====================

const Reports = {
    async exportToCSV() {
        try {
            const startDate = document.getElementById('start_date').value;
            const endDate = document.getElementById('end_date').value;

            window.location.href = `/api/reports/export?start_date=${startDate}&end_date=${endDate}&format=csv`;
            Toast.show('Downloading report...', 'info');
        } catch (error) {
            Toast.show('Error exporting report', 'error');
        }
    },

    printReport() {
        window.print();
    }
};

// ==================== REAL-TIME UPDATES ====================

const RealTimeUpdates = {
    socket: null,

    init() {
        // Periodic refresh for dashboard stats
        if (document.getElementById('live-stats')) {
            setInterval(() => this.refreshDashboardStats(), 30000); // Every 30 seconds
        }
    },

    async refreshDashboardStats() {
        try {
            const response = await fetch('/api/stats/dashboard');
            const stats = await response.json();

            // Update stats cards
            const elements = {
                'total-students': stats.total_students,
                'today-attendance': stats.today_attendance,
                'today-revenue': Utils.formatCurrency(stats.today_revenue)
            };

            Object.entries(elements).forEach(([id, value]) => {
                const el = document.getElementById(id);
                if (el) {
                    el.textContent = value;
                    el.classList.add('stat-updated');
                    setTimeout(() => el.classList.remove('stat-updated'), 500);
                }
            });
        } catch (error) {
            console.error('Error refreshing stats:', error);
        }
    }
};

// ==================== CONFIRMATION DIALOGS ====================

const ConfirmDialog = {
    show(message, onConfirm, onCancel = () => {}) {
        const modalHTML = `
            <div class="modal fade" id="confirmModal" tabindex="-1">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title"><i class="bi bi-question-circle me-2"></i>Confirm Action</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p class="mb-0">${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" id="confirmCancel">Cancel</button>
                            <button type="button" class="btn btn-primary" id="confirmOk">Confirm</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal
        const existingModal = document.getElementById('confirmModal');
        if (existingModal) existingModal.remove();

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modalElement = document.getElementById('confirmModal');
        const modal = new bootstrap.Modal(modalElement);

        document.getElementById('confirmOk').addEventListener('click', () => {
            modal.hide();
            onConfirm();
        });

        document.getElementById('confirmCancel').addEventListener('click', () => {
            modal.hide();
            onCancel();
        });

        modal.show();
    }
};

// ==================== DATA TABLES ====================

const DataTables = {
    init() {
        document.querySelectorAll('.sortable-table').forEach(table => {
            this.makeSortable(table);
        });

        document.querySelectorAll('.filterable-table').forEach(table => {
            this.addFilter(table);
        });
    },

    makeSortable(table) {
        const headers = table.querySelectorAll('th[data-sortable]');

        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.innerHTML += ' <i class="bi bi-arrow-down-up text-muted small"></i>';

            header.addEventListener('click', () => {
                const column = header.cellIndex;
                const tbody = table.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));
                const isAsc = header.classList.contains('sort-asc');

                // Remove sort classes from all headers
                headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));

                // Sort rows
                rows.sort((a, b) => {
                    const aVal = a.cells[column].textContent.trim();
                    const bVal = b.cells[column].textContent.trim();

                    // Check if numeric
                    const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
                    const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));

                    if (!isNaN(aNum) && !isNaN(bNum)) {
                        return isAsc ? bNum - aNum : aNum - bNum;
                    }

                    return isAsc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
                });

                // Update header class
                header.classList.add(isAsc ? 'sort-desc' : 'sort-asc');

                // Re-append rows
                rows.forEach(row => tbody.appendChild(row));
            });
        });
    },

    addFilter(table) {
        const filterInput = document.createElement('input');
        filterInput.type = 'text';
        filterInput.className = 'form-control mb-3';
        filterInput.placeholder = 'Search table...';

        table.parentElement.insertBefore(filterInput, table);

        filterInput.addEventListener('input', Utils.debounce((e) => {
            const filter = e.target.value.toLowerCase();
            const rows = table.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            });
        }, 300));
    }
};

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize all modules
    Toast.init();
    FormValidator.init();
    DataTables.init();
    RealTimeUpdates.init();

    // Initialize charts if on dashboard/reports page
    if (document.querySelector('[data-chart]')) {
        DashboardCharts.init();
    }

    // Setup search functionality
    const searchInput = document.getElementById('student-search');
    if (searchInput) {
        searchInput.addEventListener('input', Utils.debounce((e) => {
            StudentManager.search(e.target.value);
        }, 300));
    }

    // Add loading states to forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';

                // Re-enable after 5 seconds (fallback)
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 5000);
            }
        });
    });

    // Add confirmation to delete buttons
    document.querySelectorAll('[data-confirm]').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const message = this.dataset.confirm || 'Are you sure?';
            const href = this.href;

            ConfirmDialog.show(message, () => {
                window.location.href = href;
            });
        });
    });

    // Auto-dismiss alerts after 5 seconds
    document.querySelectorAll('.alert-dismissible').forEach(alert => {
        setTimeout(() => {
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn) closeBtn.click();
        }, 5000);
    });

    console.log('Scan2Eat initialized successfully');
});

// Export for global access
window.Utils = Utils;
window.Toast = Toast;
window.StudentManager = StudentManager;
window.MealManager = MealManager;
window.Reports = Reports;
window.ConfirmDialog = ConfirmDialog;
window.DashboardCharts = DashboardCharts;
