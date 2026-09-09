/* ==========================================================================
   KICKS AI SNEAKER BOUTIQUE - STOREFRONT & AI CHAT JAVASCRIPT CONTROLLER
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // State
    let currentBrand = 'All';
    let searchQuery = '';
    let selectedProductForOrder = null;
    let selectedSize = null;
    let currentUser = null;

    // Elements
    const productGrid = document.getElementById('productGrid');
    const searchInput = document.getElementById('searchInput');
    const brandChips = document.querySelectorAll('.chip[data-brand]');
    const aiWidgetTrigger = document.getElementById('aiWidgetTrigger');
    const chatDrawer = document.getElementById('chatDrawer');
    const closeChatBtn = document.getElementById('closeChatBtn');
    const drawerOverlay = document.getElementById('drawerOverlay');
    const chatInput = document.getElementById('chatInput');
    const sendChatBtn = document.getElementById('sendChatBtn');
    const chatMessages = document.getElementById('chatMessages');
    const navAuthActions = document.getElementById('navAuthActions');
    
    // Order Modal Elements
    const orderModal = document.getElementById('orderModal');
    const closeOrderModalBtn = document.getElementById('closeOrderModalBtn');
    const orderForm = document.getElementById('orderForm');

    // My Orders Modal Elements
    const myOrdersModal = document.getElementById('myOrdersModal');
    const closeMyOrdersModalBtn = document.getElementById('closeMyOrdersModalBtn');
    const myOrdersList = document.getElementById('myOrdersList');

    // 1. Check Current User Session
    async function checkAuthSession() {
        try {
            const res = await fetch('/api/auth/me');
            const data = await res.json();
            if (data.authenticated && data.user) {
                currentUser = data.user;
                renderUserNavbar(currentUser);
            }
        } catch (err) {
            console.error('Session check error:', err);
        }
    }

    function renderUserNavbar(user) {
        if (!navAuthActions) return;

        navAuthActions.innerHTML = `
            <div style="display:flex; align-items:center; gap:0.8rem;">
                <button class="btn-secondary" id="myOrdersBtn" style="font-size:0.85rem; padding:0.5rem 1rem;">
                    <i class="fa-solid fa-box-archive"></i> My Orders
                </button>
                ${user.role === 'admin' ? `
                    <a href="/admin" class="btn-outline-orange" style="font-size:0.85rem; padding:0.4rem 0.9rem;">
                        <i class="fa-solid fa-shield-halved"></i> Admin Portal
                    </a>
                ` : ''}
                <div style="display:flex; align-items:center; gap:0.5rem; background:rgba(255,255,255,0.06); padding:0.4rem 0.9rem; border-radius:999px; border:1px solid var(--border-glass);">
                    <i class="fa-solid fa-circle-user" style="color:var(--accent-orange);"></i>
                    <span style="font-size:0.88rem; font-weight:600; color:#FFF;">${escapeHtml(user.name.split(' ')[0])}</span>
                    <button id="logoutBtn" style="background:none; border:none; color:var(--text-dim); margin-left:0.4rem; cursor:pointer; font-size:0.8rem;" title="Logout">
                        <i class="fa-solid fa-right-from-bracket"></i>
                    </button>
                </div>
            </div>
            <button class="btn-primary" onclick="document.getElementById('aiWidgetTrigger').click()">
                <i class="fa-solid fa-wand-magic-sparkles"></i> AI Assistant
            </button>
        `;

        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', async () => {
                await fetch('/api/auth/logout', { method: 'POST' });
                window.location.reload();
            });
        }

        const myOrdersBtn = document.getElementById('myOrdersBtn');
        if (myOrdersBtn) {
            myOrdersBtn.addEventListener('click', openMyOrdersModal);
        }
    }

    // 2. Fetch & Render Catalog
    async function loadProducts() {
        if (!productGrid) return;

        productGrid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: var(--text-muted);">
                <div class="pulse-dot" style="margin: 0 auto 1rem; width: 16px; height: 16px;"></div>
                Loading premium sneaker inventory...
            </div>
        `;

        try {
            let url = `/api/products?brand=${encodeURIComponent(currentBrand)}`;
            if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;

            const res = await fetch(url);
            const data = await res.json();
            const products = data.products || [];

            if (products.length === 0) {
                productGrid.innerHTML = `
                    <div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: var(--text-muted);" class="glass-panel">
                        <h3>No sneakers found</h3>
                        <p style="margin-top: 0.5rem;">Try adjusting your search query or brand filter.</p>
                    </div>
                `;
                return;
            }

            productGrid.innerHTML = products.map(product => {
                const sizesList = Array.isArray(product.sizes) ? product.sizes : JSON.parse(product.sizes || '[]');
                return `
                    <div class="product-card">
                        <div class="card-img-wrap">
                            <span class="card-brand-badge">${escapeHtml(product.brand)}</span>
                            <img src="${escapeHtml(product.image_url)}" alt="${escapeHtml(product.name)}" class="card-img" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=800&q=80'">
                        </div>
                        <div class="card-body">
                            <h3 class="card-title">${escapeHtml(product.name)}</h3>
                            <p class="card-desc">${escapeHtml(product.description || '')}</p>
                            <div class="sizes-row">
                                ${sizesList.slice(0, 5).map(sz => `<span class="size-pill">${escapeHtml(sz)}</span>`).join('')}
                                ${sizesList.length > 5 ? `<span class="size-pill">+${sizesList.length - 5}</span>` : ''}
                            </div>
                            <div class="card-footer">
                                <div class="card-price">$${product.price.toFixed(2)}</div>
                                <button class="btn-primary buy-btn" data-product-id="${product.id}">
                                    Buy Now
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');

            // Attach Click handlers to Buy buttons
            document.querySelectorAll('.buy-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const productId = e.currentTarget.dataset.productId;
                    const prod = products.find(p => p.id == productId);
                    if (prod) openOrderModal(prod);
                });
            });

        } catch (err) {
            console.error('Error fetching products:', err);
            productGrid.innerHTML = `<div style="grid-column:1/-1; color: red; text-align:center;">Failed to load catalog.</div>`;
        }
    }

    // Brand Chips Event Listeners
    brandChips.forEach(chip => {
        chip.addEventListener('click', () => {
            brandChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            currentBrand = chip.dataset.brand;
            loadProducts();
        });
    });

    // Search input handler with debounce
    let searchTimeout;
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchQuery = e.target.value.trim();
                loadProducts();
            }, 300);
        });
    }

    // Helper: Toast Notification
    function showToastNotification(msg) {
        let toast = document.getElementById('kicksToast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'kicksToast';
            toast.style.position = 'fixed';
            toast.style.top = '20px';
            toast.style.right = '20px';
            toast.style.zIndex = '999999';
            toast.style.background = 'linear-gradient(135deg, #FF5500, #FF3300)';
            toast.style.color = '#FFF';
            toast.style.padding = '1rem 1.5rem';
            toast.style.borderRadius = '12px';
            toast.style.boxShadow = '0 10px 30px rgba(255,85,0,0.4)';
            toast.style.fontWeight = '700';
            toast.style.fontSize = '0.92rem';
            toast.style.transition = 'all 0.3s ease';
            document.body.appendChild(toast);
        }
        toast.innerHTML = msg;
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-20px)';
        }, 4500);
    }

    // 3. Order Modal Handlers
    function openOrderModal(product) {
        selectedProductForOrder = product;
        selectedSize = null;

        const sizesList = Array.isArray(product.sizes) ? product.sizes : JSON.parse(product.sizes || '[]');

        const modalTitle = document.getElementById('modalProductTitle');
        if (modalTitle) modalTitle.innerText = `Book ${product.name}`;
        
        const modalSubTitle = document.getElementById('modalProductTitleSub');
        if (modalSubTitle) modalSubTitle.innerText = product.name;

        document.getElementById('modalProductPrice').innerText = `$${product.price.toFixed(2)}`;
        document.getElementById('modalProductImg').src = product.image_url;

        // Auto-fill customer details from user session or localStorage for instant 1-click booking
        if (currentUser) {
            document.getElementById('custName').value = currentUser.name;
        } else if (localStorage.getItem('kicks_cust_name')) {
            document.getElementById('custName').value = localStorage.getItem('kicks_cust_name');
        }

        if (localStorage.getItem('kicks_cust_phone')) {
            document.getElementById('custPhone').value = localStorage.getItem('kicks_cust_phone');
        }

        if (localStorage.getItem('kicks_cust_address')) {
            document.getElementById('custAddress').value = localStorage.getItem('kicks_cust_address');
        }

        const sizeContainer = document.getElementById('modalSizeSelector');
        sizeContainer.innerHTML = sizesList.map(sz => `
            <button type="button" class="chip modal-size-btn" data-size="${escapeHtml(sz)}">${escapeHtml(sz)}</button>
        `).join('');

        document.querySelectorAll('.modal-size-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.modal-size-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                selectedSize = btn.dataset.size;
            });
        });

        // Pre-select first size
        if (sizesList.length > 0) {
            const firstBtn = sizeContainer.querySelector('.modal-size-btn');
            if (firstBtn) firstBtn.click();
        }

        orderModal.classList.add('active');
        drawerOverlay.classList.add('active');
    }

    if (closeOrderModalBtn) {
        closeOrderModalBtn.addEventListener('click', () => {
            orderModal.classList.remove('active');
            drawerOverlay.classList.remove('active');
        });
    }

    if (orderForm) {
        orderForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!selectedProductForOrder || !selectedSize) {
                alert('Please select a sneaker size.');
                return;
            }

            const nameVal = document.getElementById('custName').value.trim();
            const phoneVal = document.getElementById('custPhone').value.trim();
            const addressVal = document.getElementById('custAddress').value.trim();

            if (!nameVal || !phoneVal || !addressVal) {
                alert('Please enter your name, phone number, and address.');
                return;
            }

            // Save details locally so subsequent sneaker bookings are instant 1-click
            localStorage.setItem('kicks_cust_name', nameVal);
            localStorage.setItem('kicks_cust_phone', phoneVal);
            localStorage.setItem('kicks_cust_address', addressVal);

            const payload = {
                product_id: selectedProductForOrder.id,
                size: selectedSize,
                quantity: 1,
                customer_name: nameVal,
                customer_phone: phoneVal,
                shipping_address: addressVal,
                source: 'Web Store'
            };

            const submitBtn = orderForm.querySelector('button[type="submit"]');
            const origBtnHtml = submitBtn ? submitBtn.innerHTML : '';

            try {
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Booking Order...`;
                }

                const res = await fetch('/api/orders', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();

                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = origBtnHtml;
                }

                if (res.ok) {
                    orderModal.classList.remove('active');
                    drawerOverlay.classList.remove('active');
                    
                    showToastNotification(`🎉 <strong>ORDER BOOKED!</strong> Order #${data.order.id} for ${escapeHtml(data.order.product_name)} ($${data.order.total_price.toFixed(2)}) is confirmed.`);

                    loadProducts();

                    // Instantly open My Orders modal to show the booked order
                    setTimeout(() => {
                        openMyOrdersModal(phoneVal);
                    }, 400);
                } else {
                    alert(data.error || 'Failed to place order.');
                }
            } catch (err) {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = origBtnHtml;
                }
                console.error('Order submission error:', err);
                alert('An error occurred while booking order.');
            }
        });
    }

    // 4. My Orders Modal Logic
    async function openMyOrdersModal(phoneSearch = '') {
        if (!myOrdersModal) return;
        myOrdersList.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--text-muted);">Loading your orders...</div>`;
        myOrdersModal.classList.add('active');
        drawerOverlay.classList.add('active');

        try {
            let url = '/api/orders';
            if (phoneSearch) {
                url += `?phone=${encodeURIComponent(phoneSearch)}`;
            }

            const res = await fetch(url);
            const data = await res.json();
            const orders = data.orders || [];

            if (orders.length === 0) {
                myOrdersList.innerHTML = `
                    <div style="text-align:center; padding:2rem; color:var(--text-muted);">
                        <i class="fa-solid fa-box-open" style="font-size:2rem; margin-bottom:0.5rem;"></i>
                        <p>${phoneSearch ? `No orders found for phone number: <strong>${escapeHtml(phoneSearch)}</strong>` : "You haven't placed any sneaker orders yet."}</p>
                    </div>
                `;
                return;
            }

            myOrdersList.innerHTML = orders.map(o => `
                <div style="background:rgba(255,255,255,0.04); border:1px solid var(--border-glass); border-radius:10px; padding:1rem; margin-bottom:0.8rem; display:flex; gap:1rem; align-items:center;">
                    <img src="${escapeHtml(o.product_image)}" style="width:60px; height:60px; object-fit:cover; border-radius:8px;">
                    <div style="flex-grow:1;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <strong style="color:#FFF;">${escapeHtml(o.product_name)}</strong>
                            <span class="chip" style="font-size:0.75rem; background:rgba(255,85,0,0.15); color:var(--accent-orange); border-color:var(--accent-orange);">Status: ${escapeHtml(o.status)}</span>
                        </div>
                        <div style="font-size:0.82rem; color:var(--text-muted); margin-top:0.2rem;">
                            Size: ${escapeHtml(o.size)} | Price: <span style="color:var(--accent-orange); font-weight:700;">$${o.total_price.toFixed(2)}</span>
                        </div>
                        <div style="font-size:0.75rem; color:var(--text-dim); margin-top:0.2rem;">
                            Channel: <span style="color:#FFF;">${escapeHtml(o.source || 'Web')}</span> | Phone: ${escapeHtml(o.customer_phone || '')}
                        </div>
                    </div>
                </div>
            `).join('');

        } catch (err) {
            myOrdersList.innerHTML = `<div style="color:red; text-align:center;">Failed to load order history.</div>`;
        }
    }

    const searchOrdersByPhoneBtn = document.getElementById('searchOrdersByPhoneBtn');
    const orderSearchPhoneInput = document.getElementById('orderSearchPhoneInput');
    if (searchOrdersByPhoneBtn && orderSearchPhoneInput) {
        searchOrdersByPhoneBtn.addEventListener('click', () => {
            const phoneVal = orderSearchPhoneInput.value.trim();
            if (phoneVal) openMyOrdersModal(phoneVal);
        });
        orderSearchPhoneInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const phoneVal = orderSearchPhoneInput.value.trim();
                if (phoneVal) openMyOrdersModal(phoneVal);
            }
        });
    }

    if (closeMyOrdersModalBtn) {
        closeMyOrdersModalBtn.addEventListener('click', () => {
            myOrdersModal.classList.remove('active');
            drawerOverlay.classList.remove('active');
        });
    }

    // 5. AI Chat Drawer Logic
    function toggleChatDrawer(open) {
        if (open) {
            chatDrawer.classList.add('active');
            drawerOverlay.classList.add('active');
            if (chatMessages.children.length <= 1) {
                sendChatMessage('hi');
            }
        } else {
            chatDrawer.classList.remove('active');
            if (!orderModal.classList.contains('active') && !myOrdersModal.classList.contains('active')) {
                drawerOverlay.classList.remove('active');
            }
        }
    }

    if (aiWidgetTrigger) aiWidgetTrigger.addEventListener('click', () => toggleChatDrawer(true));
    if (closeChatBtn) closeChatBtn.addEventListener('click', () => toggleChatDrawer(false));
    if (drawerOverlay) drawerOverlay.addEventListener('click', () => {
        toggleChatDrawer(false);
        if (orderModal) orderModal.classList.remove('active');
        if (myOrdersModal) myOrdersModal.classList.remove('active');
    });

    async function sendChatMessage(customMsg) {
        const text = customMsg || chatInput.value.trim();
        if (!text) return;

        if (!customMsg) {
            appendMessage(text, 'user');
            chatInput.value = '';
        }

        const typingId = appendTypingIndicator();

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            const data = await res.json();
            removeTypingIndicator(typingId);
            appendMessage(data.response, 'bot', data.products, data.quick_replies);

        } catch (err) {
            removeTypingIndicator(typingId);
            appendMessage("Sorry, I am having trouble reaching the store server right now.", 'bot');
        }
    }

    function appendMessage(text, sender, products = [], quickReplies = []) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message-bubble ${sender}`;
        
        let html = parseMarkdown(text);

        if (products && products.length > 0) {
            html += `<div style="margin-top: 0.8rem; display: flex; flex-direction: column; gap: 0.6rem;">`;
            products.forEach(p => {
                html += `
                    <div style="background: rgba(0,0,0,0.3); border: 1px solid var(--border-glass); border-radius: 8px; padding: 0.6rem; display: flex; align-items: center; gap: 0.8rem;">
                        <img src="${escapeHtml(p.image_url)}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px;">
                        <div style="flex-grow:1; font-size: 0.82rem;">
                            <strong style="color:#FFF;">${escapeHtml(p.name)}</strong>
                            <div style="color:var(--accent-orange); font-weight:700;">$${p.price.toFixed(2)}</div>
                        </div>
                        <button class="btn-outline-orange chat-buy-btn" data-id="${p.id}" style="font-size:0.75rem; padding: 0.3rem 0.7rem;">Buy</button>
                    </div>
                `;
            });
            html += `</div>`;
        }

        if (quickReplies && quickReplies.length > 0) {
            html += `<div class="chat-quick-chips">`;
            quickReplies.forEach(qr => {
                html += `<span class="chat-quick-chip" data-qr="${escapeHtml(qr)}">${escapeHtml(qr)}</span>`;
            });
            html += `</div>`;
        }

        msgDiv.innerHTML = html;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        msgDiv.querySelectorAll('.chat-quick-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const qrText = chip.dataset.qr;
                if (qrText.includes('Telegram')) {
                    window.open('https://t.me/Eg_chatbot', '_blank');
                } else {
                    sendChatMessage(qrText);
                }
            });
        });

        msgDiv.querySelectorAll('.chat-buy-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const res = await fetch(`/api/products/${btn.dataset.id}`);
                if (res.ok) {
                    const prod = await res.json();
                    openOrderModal(prod);
                }
            });
        });
    }

    function appendTypingIndicator() {
        const id = 'typing_' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'message-bubble bot';
        div.innerHTML = `<div class="pulse-dot" style="display:inline-block;"></div> KICKS AI is thinking...`;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }

    function removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    if (sendChatBtn) sendChatBtn.addEventListener('click', () => sendChatMessage());
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendChatMessage();
        });
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    function parseMarkdown(text) {
        if (!text) return '';
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    // Initial Load
    checkAuthSession();
    loadProducts();
});
