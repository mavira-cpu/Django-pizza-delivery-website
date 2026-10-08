// ===== DOM READY =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOM loaded');
    initAddToCart();
});

// ===== ADD TO CART =====
function addToCart(itemId, quantity = 1) {
    console.log('🛒 Adding item:', itemId);
    
    fetch(`/add-to-cart/?item_id=${itemId}&quantity=${quantity}`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
        }
    })
    .then(response => {
        console.log('📡 Status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('📦 Response:', data);
        if (data.status === 'success') {
            // Update cart badge
            updateCartBadge(data.cart_count);
            
            // Button feedback
            const button = document.querySelector(`.add-to-cart[data-item-id="${itemId}"]`);
            if (button) {
                const originalText = button.textContent;
                button.textContent = ' Added!';
                button.style.background = '#28a745';
                setTimeout(() => {
                    button.textContent = originalText;
                    button.style.background = '';
                }, 1500);
            }
            
            showToast(data.message);
        }
    })
    .catch(error => {
        console.error(' Error:', error);
        showToast('Error adding item to cart', 'error');
    });
}

// ===== UPDATE CART BADGE =====
function updateCartBadge(count) {
    document.querySelectorAll('.cart-badge').forEach(badge => {
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'block' : 'none';
        }
    });
}

// ===== INIT ADD TO CART BUTTONS =====
function initAddToCart() {
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const itemId = this.dataset.itemId;
            if (itemId) {
                addToCart(itemId, 1);
            }
        });
    });
}

// ===== TOAST NOTIFICATION =====
function showToast(message, type = 'success') {
    const existing = document.querySelector('.toast-notification');
    if (existing) existing.remove();
    
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.textContent = message;
    
    const colors = {
        success: '#28a745',
        error: '#dc3545',
        warning: '#ffc107'
    };
    
    Object.assign(toast.style, {
        position: 'fixed',
        bottom: '30px',
        right: '30px',
        background: colors[type] || colors.success,
        color: '#fff',
        padding: '16px 28px',
        borderRadius: '12px',
        boxShadow: '0 8px 30px rgba(0,0,0,0.15)',
        zIndex: '9999',
        animation: 'slideIn 0.4s ease',
        fontWeight: '600',
        maxWidth: '400px'
    });
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(30px)';
        toast.style.transition = '0.3s';
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}

// ===== ADD ANIMATION STYLE =====
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
`;
document.head.appendChild(style);

console.log('✅ JavaScript loaded');