(function() {
    const productInput = document.getElementById('productSearch');
    const dropdown = document.getElementById('productDropdown');
    const productPk = document.getElementById('productPk');

    if (!productInput || !dropdown || !productPk) return;

    let products = [];
    try {
        products = JSON.parse(productInput.dataset.products || '[]');
    } catch (e) {
        products = [];
    }

    function renderDropdown(filterText) {
        const q = (filterText || productInput.value).toLowerCase();
        const filtered = q ? products.filter(p => p.text.toLowerCase().includes(q)) : products;

        if (filtered.length === 0) {
            dropdown.classList.add('hidden');
            return;
        }

        dropdown.innerHTML = filtered.map(p =>
            `<div class="px-4 py-2.5 cursor-pointer transition hover:bg-white/10 text-sm" style="color:var(--text-primary)" data-pk="${p.pk}" data-text="${p.text.replace(/"/g, '"')}">${p.text}</div>`
        ).join('');
        dropdown.classList.remove('hidden');

        dropdown.querySelectorAll('div[data-pk]').forEach(item => {
            item.addEventListener('click', function() {
                productInput.value = this.dataset.text;
                productPk.value = this.dataset.pk;
                dropdown.classList.add('hidden');
            });
        });
    }

    productInput.addEventListener('input', function() {
        renderDropdown(this.value);
    });

    productInput.addEventListener('focus', function() {
        renderDropdown(this.value);
    });

    document.addEventListener('click', function(e) {
        if (!productInput.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.add('hidden');
        }
    });

    productInput.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            dropdown.classList.add('hidden');
        }
    });
})();
