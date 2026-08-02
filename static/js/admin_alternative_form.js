(function() {
    const productInput = document.getElementById('productSearch');
    const dropdown = document.getElementById('productDropdown');
    const productPk = document.getElementById('productPk');

    if (!productInput || !dropdown || !productPk) return;

    const products = window._productsData || [];

    function renderDropdown(filterText) {
        const q = (filterText || '').toLowerCase();
        const filtered = q ? products.filter(p => p.text.toLowerCase().includes(q)) : products;

        dropdown.innerHTML = '';

        if (filtered.length === 0) {
            dropdown.classList.add('hidden');
            return;
        }

        filtered.forEach(p => {
            const item = document.createElement('div');
            item.className = 'px-4 py-2.5 cursor-pointer transition hover:bg-white/10 text-sm';
            item.style.color = 'var(--text-primary)';
            item.textContent = p.text;
            item.addEventListener('click', function() {
                productInput.value = p.text;
                productPk.value = p.pk;
                dropdown.classList.add('hidden');
            });
            dropdown.appendChild(item);
        });

        dropdown.classList.remove('hidden');
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
        if (e.key === 'Escape') dropdown.classList.add('hidden');
    });
})();
