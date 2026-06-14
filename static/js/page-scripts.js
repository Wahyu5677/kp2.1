(function () {
    function updateCountAndFilter(inputId, tableId, countBadgeId) {
        const table = document.getElementById(tableId);
        const input = document.getElementById(inputId);
        const tbody = table ? table.querySelector('tbody') : null;
        const countBadge = document.getElementById(countBadgeId);
        if (!tbody || !input || !countBadge) return;

        const rows = Array.from(tbody.querySelectorAll('tr'));
        const q = (input.value || '').toLowerCase().trim();

        let visible = 0;
        rows.forEach(row => {
            const text = row.innerText.toLowerCase();
            const show = !q || text.includes(q);
            row.style.display = show ? '' : 'none';
            if (show) visible++;
        });

        countBadge.textContent = visible + ' data';
    }

    function initSearch(tableId, inputId, countBadgeId) {
        const input = document.getElementById(inputId);
        if (!input) return;

        input.addEventListener('input', function () {
            updateCountAndFilter(inputId, tableId, countBadgeId);
        });

        updateCountAndFilter(inputId, tableId, countBadgeId);
    }

    function setupDeleteModal(options) {
        const modal = document.getElementById(options.modalId);
        const form = document.getElementById(options.formId);
        if (!modal || !form) return;

        document.querySelectorAll(options.buttonSelector).forEach(btn => {
            btn.addEventListener('click', function () {
                const url = btn.getAttribute(options.urlAttribute) || '';
                const label = btn.getAttribute(options.labelAttribute) || 'data ini';
                if (options.labelId) {
                    const labelItem = document.getElementById(options.labelId);
                    if (labelItem) labelItem.textContent = label;
                }
                if (url) {
                    form.setAttribute('action', url);
                } else {
                    form.setAttribute('action', '');
                }
            });
        });

        modal.addEventListener('show.bs.modal', function (event) {
            const btn = event.relatedTarget;
            if (!btn) return;

            const url = btn.getAttribute(options.urlAttribute) || '';
            const label = btn.getAttribute(options.labelAttribute) || 'data ini';
            if (options.labelId) {
                const labelItem = document.getElementById(options.labelId);
                if (labelItem) labelItem.textContent = label;
            }

            if (url) {
                form.setAttribute('action', url);
            } else {
                form.setAttribute('action', '');
            }
        });

        modal.addEventListener('hidden.bs.modal', function () {
            form.setAttribute('action', '');
        });
    }

    function initBarangPage() {
        initSearch('tableBarang', 'searchBarang', 'rowCountBarang');
        setupDeleteModal({
            modalId: 'modalHapusBarang',
            formId: 'formHapusBarangModal',
            buttonSelector: '.btn-hapus[data-hapus-url]',
            urlAttribute: 'data-hapus-url',
            labelAttribute: 'data-hapus-label',
            labelId: 'modalHapusBarangLabelItem'
        });
    }

    function initBarangKosongPage() {
        initSearch('tableBarangKosong', 'searchBarangKosong', 'rowCountBarangKosong');
        setupDeleteModal({
            modalId: 'modalHapusBarangKosong',
            formId: 'formHapusBarangKosong',
            buttonSelector: '.btn-hapus[data-hapus-url]',
            urlAttribute: 'data-hapus-url',
            labelAttribute: 'data-hapus-label',
            labelId: 'modalHapusBarangKosongLabelItem'
        });
    }

    function initKeuanganPage() {
        initSearch('tableKeuangan', 'searchKeuangan', 'rowCountKeuangan');
        initKeuanganFilter();
        setupDeleteModal({
            modalId: 'modalHapusKeuangan',
            formId: 'formHapusKeuangan',
            buttonSelector: '.btn-hapus[data-hapus-url]',
            urlAttribute: 'data-hapus-url',
            labelAttribute: 'data-hapus-label',
            labelId: 'modalHapusKeuanganLabelItem'
        });
    }

    function initKeuanganFilter() {
        const periode = document.getElementById('periode');
        const weeklyField = document.getElementById('weeklyField');
        const monthlyField = document.getElementById('monthlyField');
        if (!periode || !weeklyField || !monthlyField) return;

        const updateVisibility = () => {
            const value = periode.value;
            weeklyField.classList.toggle('d-none', value !== 'weekly');
            monthlyField.classList.toggle('d-none', value !== 'monthly');
        };

        periode.addEventListener('change', updateVisibility);
        updateVisibility();
    }

    function initStockOpnamePage() {
        initSearch('tableStockOpname', 'searchStockOpname', 'rowCountStockOpname');
        setupDeleteModal({
            modalId: 'modalHapusStockOpname',
            formId: 'formHapusStockOpname',
            buttonSelector: '.btn-hapus[data-hapus-url]',
            urlAttribute: 'data-hapus-url',
            labelAttribute: 'data-hapus-label',
            labelId: 'modalHapusStockOpnameLabelItem'
        });
    }

    function autoDismissAlerts(timeoutMs) {
        const alerts = document.querySelectorAll('.alert.alert-dismissible.fade.show');
        if (!alerts.length) return;

        setTimeout(() => {
            alerts.forEach(alert => {
                try {
                    const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                    bsAlert.close();
                } catch (e) {
                    alert.classList.remove('show');
                    alert.classList.add('hide');
                }
            });
        }, timeoutMs);
    }

    document.addEventListener('DOMContentLoaded', function () {
        initBarangPage();
        initBarangKosongPage();
        initKeuanganPage();
        initStockOpnamePage();
        autoDismissAlerts(5000);
    });
})();
