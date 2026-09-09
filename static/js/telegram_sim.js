/* ==========================================================================
   KICKS AI SNEAKER BOUTIQUE - INTERACTIVE TELEGRAM BOT WEB SIMULATOR
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    const tgMessagesContainer = document.getElementById('tgMessagesContainer');
    const tgInput = document.getElementById('tgInput');
    const tgSendBtn = document.getElementById('tgSendBtn');

    if (!tgMessagesContainer) return;

    // Send command/text to bot backend
    async function sendTelegramMessage(text) {
        if (!text) return;

        // Render user message bubble
        appendTgBubble(text, 'user');
        if (tgInput) tgInput.value = '';

        // Show typing status
        const typingEl = appendTgTyping();

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, telegram_id: '999888' })
            });

            const data = await res.json();
            if (typingEl) typingEl.remove();

            appendTgBubble(data.response, 'bot', data.products, data.quick_replies);

        } catch (err) {
            if (typingEl) typingEl.remove();
            appendTgBubble("⚠️ Communication error with store backend.", 'bot');
        }
    }

    function appendTgBubble(text, sender, products = [], quickReplies = []) {
        const wrapDiv = document.createElement('div');
        wrapDiv.style.display = 'flex';
        wrapDiv.style.flexDirection = 'column';
        wrapDiv.style.alignItems = sender === 'user' ? 'flex-end' : 'flex-start';
        wrapDiv.style.marginBottom = '0.8rem';

        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        let html = `
            <div style="max-width: 82%; padding: 0.75rem 1rem; border-radius: 12px; font-size: 0.88rem; line-height: 1.4;
                ${sender === 'user' ? 'background: #2AABEE; color: #FFF; border-bottom-right-radius: 2px;' : 'background: #212D3B; color: #F5F5F5; border-bottom-left-radius: 2px;'}"
            >
                ${parseMarkdown(text)}
                <div style="font-size: 0.68rem; opacity: 0.7; text-align: right; margin-top: 0.3rem;">${timeStr}</div>
            </div>
        `;

        if (products && products.length > 0) {
            html += `<div style="max-width: 82%; margin-top: 0.4rem; display: flex; flex-direction: column; gap: 0.5rem; width: 100%;">`;
            products.forEach(p => {
                html += `
                    <div style="background: #17212B; border: 1px solid #2B394A; border-radius: 8px; padding: 0.6rem; display: flex; gap: 0.6rem; align-items: center;">
                        <img src="${escapeHtml(p.image_url)}" style="width: 45px; height: 45px; object-fit: cover; border-radius: 6px;">
                        <div style="flex-grow: 1; font-size: 0.8rem;">
                            <strong style="color:#FFF;">${escapeHtml(p.name)}</strong>
                            <div style="color:#2AABEE; font-weight:700;">$${p.price.toFixed(2)}</div>
                        </div>
                        <button class="tg-inline-btn" data-buy-id="${p.id}" style="background: #2AABEE; color:#FFF; border:none; padding:0.3rem 0.6rem; border-radius:4px; font-size:0.75rem; cursor:pointer;">
                            🛒 Order
                        </button>
                    </div>
                `;
            });
            html += `</div>`;
        }

        if (quickReplies && quickReplies.length > 0) {
            html += `<div style="display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.4rem; max-width: 82%;">`;
            quickReplies.forEach(qr => {
                html += `<button class="tg-qr-btn" data-qr="${escapeHtml(qr)}" style="background:#212D3B; border: 1px solid #2AABEE; color:#2AABEE; padding:0.3rem 0.7rem; border-radius:14px; font-size:0.75rem; cursor:pointer;">${escapeHtml(qr)}</button>`;
            });
            html += `</div>`;
        }

        wrapDiv.innerHTML = html;
        tgMessagesContainer.appendChild(wrapDiv);
        tgMessagesContainer.scrollTop = tgMessagesContainer.scrollHeight;

        // Attach listeners for inline buttons
        wrapDiv.querySelectorAll('.tg-qr-btn').forEach(btn => {
            btn.addEventListener('click', () => sendTelegramMessage(btn.dataset.qr));
        });

        wrapDiv.querySelectorAll('.tg-inline-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                sendTelegramMessage(`I want to buy product ID #${btn.dataset.buyId}`);
            });
        });
    }

    function appendTgTyping() {
        const div = document.createElement('div');
        div.style.alignSelf = 'flex-start';
        div.style.marginBottom = '0.8rem';
        div.style.background = '#212D3B';
        div.style.color = '#8A99A8';
        div.style.padding = '0.5rem 0.9rem';
        div.style.borderRadius = '12px';
        div.style.fontSize = '0.8rem';
        div.innerHTML = `<em>bot is typing...</em>`;
        tgMessagesContainer.appendChild(div);
        tgMessagesContainer.scrollTop = tgMessagesContainer.scrollHeight;
        return div;
    }

    if (tgSendBtn) tgSendBtn.addEventListener('click', () => sendTelegramMessage(tgInput.value.trim()));
    if (tgInput) {
        tgInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendTelegramMessage(tgInput.value.trim());
        });
    }

    // Command buttons bar inside simulator
    document.querySelectorAll('.tg-cmd-btn').forEach(btn => {
        btn.addEventListener('click', () => sendTelegramMessage(btn.dataset.cmd));
    });

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

    // Trigger start on load
    sendTelegramMessage('/start');
});
