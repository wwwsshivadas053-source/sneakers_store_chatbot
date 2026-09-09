/* ==========================================================================
   KICKS AI SNEAKER BOUTIQUE - ADMIN DASHBOARD CONTROLLER
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // Check if on admin page
    const adminStatsRow = document.getElementById('adminStatsRow');
    if (!adminStatsRow) return;

    // Elements
    const totalRevenueEl = document.getElementById('statTotalRevenue');
    const totalOrdersEl = document.getElementById('statTotalOrders');
    const totalProductsEl = document.getElementById('statTotalProducts');
    const lowStockCountEl = document.getElementById('statLowStockCount');

    const productsTableBody = document.getElementById('adminProductsTableBody');
    const ordersTableBody = document.getElementById('adminOrdersTableBody');

    const addProductBtn = document.getElementById('addProductBtn');
    const productModal = document.getElementById('productModal');
    const closeProductModalBtn = document.getElementById('closeProductModalBtn');
    const productForm = document.getElementById('productForm');
    const modalTitle = document.getElementById('productModalTitle');

    let currentEditingProductId = null;

    // 1. Fetch & Render Stats
    async function loadAdminStats() {
        try {
            const res = await fetch('/api/admin/stats');
            if (res.status === 401 || res.status === 403) {
                window.location.href = '/login?next=/admin';
                return;
            }
            const stats = await res.json();

            totalRevenueEl.innerText = `$${stats.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
            totalOrdersEl.innerText = stats.total_orders;
            totalProductsEl.innerText = stats.total_products;
            lowStockCountEl.innerText = stats.low_stock_count;

            if (stats.low_stock_count > 0) {
                lowStockCountEl.parentElement.style.borderColor = 'var(--accent-orange)';
            }
        } catch (err) {
            console.error('Error fetching admin stats:', err);
        }
    }

    // 2. Fetch & Render Products Table
    async function loadAdminProducts() {
        try {
            const res = await fetch('/api/products');
            const data = await res.json();
            const products = data.products || [];

            productsTableBody.innerHTML = products.map(p => `
                <tr>
                    <td style="display:flex; align-items:center; gap:0.8rem; padding: 0.8rem 1rem;">
                        <img src="${escapeHtml(p.image_url)}" style="width:45px; height:45px; object-fit:cover; border-radius:6px;">
                        <div>
                            <strong style="color:#FFF;">${escapeHtml(p.name)}</strong>
                            <div style="font-size:0.75rem; color:var(--text-dim);">${escapeHtml(p.category)}</div>
                        </div>
                    </td>
                    <td><span class="chip" style="font-size:0.75rem;">${escapeHtml(p.brand)}</span></td>
                    <td style="font-weight:700; color:var(--accent-orange);">$${p.price.toFixed(2)}</td>
                    <td>
                        <span style="font-weight:700; color: ${p.stock <= 5 ? '#EF4444' : '#10B981'};">
                            ${p.stock} units ${p.stock <= 5 ? '⚠️' : ''}
                        </span>
                    </td>
                    <td>
                        <div style="display:flex; gap:0.4rem;">
                            <button class="btn-outline-orange edit-prod-btn" data-id="${p.id}" style="font-size:0.75rem; padding:0.3rem 0.6rem;">Edit</button>
                            <button class="btn-secondary delete-prod-btn" data-id="${p.id}" style="font-size:0.75rem; padding:0.3rem 0.6rem; color:#EF4444; border-color:rgba(239,68,68,0.3);">Delete</button>
                        </div>
                    </td>
                </tr>
            `).join('');

            // Attach edit/delete listeners
            document.querySelectorAll('.edit-prod-btn').forEach(btn => {
                btn.addEventListener('click', () => openEditProductModal(btn.dataset.id, products));
            });

            document.querySelectorAll('.delete-prod-btn').forEach(btn => {
                btn.addEventListener('click', () => deleteProduct(btn.dataset.id));
            });

        } catch (err) {
            console.error('Error fetching admin products:', err);
        }
    }

    // 3. Fetch & Render Orders Table
    async function loadAdminOrders() {
        try {
            const res = await fetch('/api/orders');
            if (res.status === 401 || res.status === 403) return;

            const data = await res.json();
            const orders = data.orders || [];

            ordersTableBody.innerHTML = orders.map(o => `
                <tr>
                    <td style="padding: 0.8rem 1rem; font-weight:700; color:var(--accent-orange);">#${o.id}</td>
                    <td>
                        <strong style="color:#FFF;">${escapeHtml(o.customer_name)}</strong>
                        <div style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(o.customer_phone)}</div>
                    </td>
                    <td>
                        <div>${escapeHtml(o.product_name)}</div>
                        <div style="font-size:0.75rem; color:var(--text-dim);">Size: ${escapeHtml(o.size)} | Qty: ${o.quantity}</div>
                    </td>
                    <td style="font-weight:700;">$${o.total_price.toFixed(2)}</td>
                    <td>
                        <span class="chip" style="font-size:0.75rem; background:rgba(255,255,255,0.06);">${escapeHtml(o.source || 'Web')}</span>
                    </td>
                    <td>
                        <select class="form-control status-select" data-order-id="${o.id}" style="font-size:0.8rem; padding:0.3rem 0.6rem; width:130px;">
                            <option value="Pending" ${o.status === 'Pending' ? 'selected' : ''}>Pending</option>
                            <option value="Processing" ${o.status === 'Processing' ? 'selected' : ''}>Processing</option>
                            <option value="Shipped" ${o.status === 'Shipped' ? 'selected' : ''}>Shipped</option>
                            <option value="Delivered" ${o.status === 'Delivered' ? 'selected' : ''}>Delivered</option>
                            <option value="Cancelled" ${o.status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
                        </select>
                    </td>
                </tr>
            `).join('');

            document.querySelectorAll('.status-select').forEach(select => {
                select.addEventListener('change', async (e) => {
                    const orderId = e.target.dataset.orderId;
                    const newStatus = e.target.value;
                    await updateOrderStatus(orderId, newStatus);
                });
            });

        } catch (err) {
            console.error('Error fetching admin orders:', err);
        }
    }

    async function updateOrderStatus(orderId, newStatus) {
        try {
            const res = await fetch(`/api/orders/${orderId}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus })
            });

            if (res.ok) {
                loadAdminStats();
            } else {
                alert('Failed to update status.');
            }
        } catch (err) {
            console.error('Order status update error:', err);
        }
    }

    // 4. Add/Edit Product Modal Handlers
    function openAddProductModal() {
        currentEditingProductId = null;
        modalTitle.innerText = "Add New Sneaker";
        productForm.reset();
        document.getElementById('prodSizes').value = '["US 7", "US 8", "US 9", "US 10", "US 11"]';
        productModal.classList.add('active');
    }

    function openEditProductModal(productId, productsList) {
        const prod = productsList.find(p => p.id == productId);
        if (!prod) return;

        currentEditingProductId = productId;
        modalTitle.innerText = "Edit Sneaker Details";
        
        document.getElementById('prodName').value = prod.name;
        document.getElementById('prodBrand').value = prod.brand;
        document.getElementById('prodCategory').value = prod.category;
        document.getElementById('prodPrice').value = prod.price;
        document.getElementById('prodStock').value = prod.stock;
        document.getElementById('prodImg').value = prod.image_url;
        document.getElementById('prodSizes').value = JSON.stringify(prod.sizes);
        document.getElementById('prodDesc').value = prod.description || '';
        document.getElementById('prodFeatured').checked = prod.featured;

        productModal.classList.add('active');
    }

    if (addProductBtn) addProductBtn.addEventListener('click', openAddProductModal);
    if (closeProductModalBtn) closeProductModalBtn.addEventListener('click', () => productModal.classList.remove('active'));

    if (productForm) {
        productForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            let sizesArr = ["US 7", "US 8", "US 9", "US 10", "US 11"];
            try {
                sizesArr = JSON.parse(document.getElementById('prodSizes').value);
            } catch (err) {
                sizesArr = document.getElementById('prodSizes').value.split(',').map(s => s.trim());
            }

            const payload = {
                name: document.getElementById('prodName').value.trim(),
                brand: document.getElementById('prodBrand').value,
                category: document.getElementById('prodCategory').value,
                price: parseFloat(document.getElementById('prodPrice').value),
                stock: parseInt(document.getElementById('prodStock').value),
                image_url: document.getElementById('prodImg').value.trim(),
                sizes: sizesArr,
                description: document.getElementById('prodDesc').value.trim(),
                featured: document.getElementById('prodFeatured').checked
            };

            const url = currentEditingProductId ? `/api/products/${currentEditingProductId}` : '/api/products';
            const method = currentEditingProductId ? 'PUT' : 'POST';

            try {
                const res = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (res.ok) {
                    productModal.classList.remove('active');
                    loadAdminProducts();
                    loadAdminStats();
                } else {
                    const data = await res.json();
                    alert(data.error || 'Operation failed.');
                }
            } catch (err) {
                console.error('Save product error:', err);
            }
        });
    }

    async function deleteProduct(productId) {
        if (!confirm("Are you sure you want to delete this sneaker from inventory?")) return;

        try {
            const res = await fetch(`/api/products/${productId}`, { method: 'DELETE' });
            if (res.ok) {
                loadAdminProducts();
                loadAdminStats();
            } else {
                alert('Failed to delete product.');
            }
        } catch (err) {
            console.error('Delete error:', err);
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    // Initial Load & Auto Refresh every 10s
    loadAdminStats();
    loadAdminProducts();
    loadAdminOrders();

    setInterval(() => {
        loadAdminStats();
        loadAdminOrders();
    }, 10000);
});
