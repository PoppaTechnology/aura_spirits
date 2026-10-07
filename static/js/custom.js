// CSRF Cookie Helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    if (!cookieValue) {
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        if (input) cookieValue = input.value;
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

/* Age Verification Modal */
const modal = document.getElementById('age-modal');
const deniedMsg = document.getElementById('denied-message');

document.addEventListener('DOMContentLoaded', () => {
    if (modal) {
        if (!sessionStorage.getItem('ageVerified')) {
            document.body.classList.add('modal-open-custom');
            setTimeout(() => modal.classList.remove('opacity-0'), 100);
        } else {
            modal.style.display = 'none';
        }
    }
    initScrollReveal();
});

function closeModal() {
    if (!modal) return;
    sessionStorage.setItem('ageVerified', 'true');
    modal.classList.add('opacity-0');
    setTimeout(() => {
        modal.style.display = 'none';
        document.body.classList.remove('modal-open-custom');
    }, 500);
}

function denyAccess() {
    if (!deniedMsg || !modal) return;
    deniedMsg.classList.remove('d-none');
    const box = modal.querySelector('.age-modal-box');
    if (box) {
        box.style.animation = 'none';
        box.offsetHeight; // reflow
        box.style.animation = 'pulse 0.5s';
    }
}

/* Mobile Menu */
const mobileMenuBtn = document.getElementById('mobile-menu-btn');
if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', () => {
        const m = document.getElementById('mobile-menu');
        if (m) m.classList.toggle('d-none');
    });
}

document.querySelectorAll('#mobile-menu .mobile-nav-link').forEach(link => {
    link.addEventListener('click', () => {
        const m = document.getElementById('mobile-menu');
        if (m) m.classList.add('d-none');
    });
});

/* Navbar Scroll */
const navbar = document.getElementById('navbar');
if (navbar) {
    window.addEventListener('scroll', () => {
        navbar.classList.toggle('scrolled', window.scrollY > 40);
    });
    // Check initial
    if (window.scrollY > 40) navbar.classList.add('scrolled');
}

/* Scroll Reveal */
function initScrollReveal() {
    function reveal() {
        document.querySelectorAll('.reveal').forEach(el => {
            if (el.getBoundingClientRect().top < window.innerHeight - 80) {
                el.classList.add('active');
            }
        });
    }
    window.addEventListener('scroll', reveal);
    setTimeout(reveal, 200);
    setTimeout(reveal, 800);
}

/* Toast Notifications */
let toastTimer;
function showToast(msg) {
    let t = document.getElementById('toast');
    let toastText = document.getElementById('toast-text');
    if (!t) {
        t = document.getElementById('toast-msg');
        toastText = document.getElementById('toast-text');
    }
    if (!t) return;
    if (toastText) toastText.textContent = msg;
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('show'), 3000);
}

function showMessage(msg) {
    showToast(msg);
}

/* Cart Drawer & Backend State Sync */
function openCartDrawer() {
    const drawer = document.getElementById('cart-drawer');
    const backdrop = document.getElementById('cart-drawer-backdrop');
    if (drawer && backdrop) {
        drawer.classList.add('open');
        backdrop.classList.add('open');
        document.body.style.overflow = 'hidden';
        fetchCartData();
    } else {
        // Fallback to cart page
        window.location.href = '/cart/';
    }
}

function closeCartDrawer() {
    const drawer = document.getElementById('cart-drawer');
    const backdrop = document.getElementById('cart-drawer-backdrop');
    if (drawer && backdrop) {
        drawer.classList.remove('open');
        backdrop.classList.remove('open');
        document.body.style.overflow = '';
    }
}

function updateCartCounters(count) {
    document.querySelectorAll('.cart-count, #cart-count').forEach(el => {
        el.textContent = count;
    });
}

function fetchCartData() {
    fetch('/api/cart/data/')
        .then(res => res.json())
        .then(data => renderCartDrawer(data))
        .catch(err => console.error('Error fetching cart:', err));
}

function renderCartDrawer(cart) {
    const container = document.getElementById('drawer-items-container');
    const subtotalEl = document.getElementById('drawer-subtotal');
    const totalEl = document.getElementById('drawer-total');
    const shippingEl = document.getElementById('drawer-shipping');
    const shippingBar = document.getElementById('drawer-shipping-bar');
    const shippingMsg = document.getElementById('drawer-shipping-msg');

    updateCartCounters(cart.count);

    if (subtotalEl) subtotalEl.textContent = cart.formatted_subtotal;
    if (totalEl) totalEl.textContent = cart.formatted_total;
    if (shippingEl) shippingEl.textContent = cart.formatted_shipping;

    if (shippingBar && shippingMsg) {
        shippingBar.style.width = `${cart.free_shipping_progress}%`;
        if (cart.free_shipping_needed > 0) {
            shippingMsg.innerHTML = `Add <span style="color:var(--amber-400);font-weight:600;">₦${cart.free_shipping_needed.toFixed(2)}</span> more for <strong>FREE Courier Delivery</strong>`;
        } else {
            shippingMsg.innerHTML = `<i class="ph-fill ph-check-circle" style="color:var(--amber-400);"></i> <strong>Unlocked FREE White Glove Courier</strong>`;
        }
    }

    if (!container) return;

    if (!cart.items || cart.items.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="ph ph-shopping-bag text-muted mb-3" style="font-size:3rem;display:block;"></i>
                <h4 class="font-serif text-white mb-2 fs-5">Your Cellar Cart is Empty</h4>
                <p class="text-muted small mb-4">Explore our curated collection of artisanal whiskies and fine spirits.</p>
                <a href="/catalog/" class="btn-amber-pill py-2 px-4" style="font-size:0.8rem;" onclick="closeCartDrawer()">Explore Catalog</a>
            </div>
        `;
        return;
    }

    let html = '';
    cart.items.forEach(item => {
        html += `
            <div class="cart-item-card">
                <img src="${item.image_url}" alt="${item.name}" class="cart-item-img">
                <div class="cart-item-info">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <span class="cart-item-cat">${item.category} • ${item.volume}</span>
                            <a href="/spirit/${item.slug}/" class="cart-item-title d-block">${item.name}</a>
                        </div>
                        <button class="cart-item-del" onclick="apiRemoveFromCart(${item.id})" title="Remove item">
                            <i class="ph ph-trash"></i>
                        </button>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mt-2">
                        <div class="cart-qty-ctrl">
                            <button class="cart-qty-btn" onclick="apiUpdateCart(${item.id}, ${item.quantity - 1})"><i class="ph ph-minus"></i></button>
                            <span class="cart-qty-num">${item.quantity}</span>
                            <button class="cart-qty-btn" onclick="apiUpdateCart(${item.id}, ${item.quantity + 1})"><i class="ph ph-plus"></i></button>
                        </div>
                        <span class="cart-item-price">${item.formatted_total}</span>
                    </div>
                </div>
            </div>
        `;
    });
    container.innerHTML = html;
}

/* Cart API AJAX Actions */
function addToCart(btn, productId, name, qty = 1) {
    if (btn) {
        btn.classList.add('added');
        btn.innerHTML = '<i class="ph ph-check"></i> Added';
    }

    fetch('/api/cart/add/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken || getCookie('csrftoken'),
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: qty
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            updateCartCounters(data.cart.count);
            showToast(data.message || `"${name}" added to cart`);
            renderCartDrawer(data.cart);
        } else {
            showToast(data.message || "Error adding to cart");
        }
    })
    .catch(err => {
        console.error('Add to cart error:', err);
        showToast("Error updating cart");
    })
    .finally(() => {
        if (btn) {
            setTimeout(() => {
                btn.classList.remove('added');
                btn.innerHTML = '<i class="ph ph-shopping-cart"></i> Add to Cart';
            }, 2200);
        }
    });
}

function quickAdd(btn, productId, name) {
    addToCart(btn, productId, name, 1);
}

function apiUpdateCart(productId, newQty) {
    fetch('/api/cart/update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken || getCookie('csrftoken'),
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: newQty
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            renderCartDrawer(data.cart);
            // If on cart page, reload or refresh
            if (window.location.pathname === '/cart/') {
                window.location.reload();
            }
        }
    });
}

function apiRemoveFromCart(productId) {
    fetch('/api/cart/remove/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken || getCookie('csrftoken'),
        },
        body: JSON.stringify({
            product_id: productId
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast(data.message);
            renderCartDrawer(data.cart);
            if (window.location.pathname === '/cart/') {
                window.location.reload();
            }
        }
    });
}

function applyCartCoupon() {
    const input = document.getElementById('cart-coupon-input') || document.getElementById('coupon-input');
    if (!input) return;
    const code = input.value.trim();
    if (!code) {
        showToast('Please enter a voucher code.');
        return;
    }
    apiApplyCoupon(code);
}

function applyCheckoutCoupon() {
    const input = document.getElementById('checkout-coupon-input');
    if (!input) return;
    const code = input.value.trim();
    if (!code) {
        showToast('Please enter a voucher code.');
        return;
    }
    apiApplyCoupon(code);
}

function removeCartCoupon() {
    fetch('/api/cart/coupon/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken || getCookie('csrftoken'),
        },
        body: JSON.stringify({ code: '' })
    })
    .then(res => res.json())
    .then(data => {
        showToast(data.message || 'Voucher removed');
        if (data.cart) renderCartDrawer(data.cart);
        if (window.location.pathname === '/cart/' || window.location.pathname === '/checkout/') {
            window.location.reload();
        }
    })
    .catch(err => {
        console.error('Error removing coupon:', err);
        showToast('Error removing voucher');
    });
}

function apiApplyCoupon(code) {
    if (!code) {
        showToast('Please enter a voucher code.');
        return;
    }
    fetch('/api/cart/coupon/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken || getCookie('csrftoken'),
        },
        body: JSON.stringify({ code: code.trim() })
    })
    .then(res => res.json())
    .then(data => {
        showToast(data.message);
        if (data.success) {
            if (data.cart) renderCartDrawer(data.cart);
            if (window.location.pathname === '/cart/' || window.location.pathname === '/checkout/') {
                setTimeout(() => window.location.reload(), 400);
            }
        }
    })
    .catch(err => {
        console.error('Error applying coupon:', err);
        showToast('Error communicating with server.');
    });
}

/* Wishlist Toggle */
function toggleWish(btn, productId) {
    if (!productId) return;
    fetch('/api/wishlist/toggle/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken || getCookie('csrftoken'),
        },
        body: JSON.stringify({ product_id: productId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            if (data.in_wishlist) {
                btn.classList.add('active');
                btn.innerHTML = '<i class="ph-fill ph-heart"></i>';
            } else {
                btn.classList.remove('active');
                btn.innerHTML = '<i class="ph ph-heart"></i>';
            }
            showToast(data.message);
            document.querySelectorAll('.wishlist-count').forEach(el => {
                el.textContent = data.count;
            });
            if (window.location.pathname === '/wishlist/' && !data.in_wishlist) {
                window.location.reload();
            }
        }
    })
    .catch(err => console.error('Wishlist error:', err));
}

/* Newsletter Subscription */
function handleNewsletterSubmit(e, form) {
    e.preventDefault();
    const emailInput = form.querySelector('input[type="email"]');
    if (!emailInput || !emailInput.value) return;

    fetch('/api/newsletter/subscribe/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken || getCookie('csrftoken'),
        },
        body: JSON.stringify({ email: emailInput.value })
    })
    .then(res => res.json())
    .then(data => {
        showToast(data.message);
        if (data.success) {
            emailInput.value = '';
        }
    })
    .catch(err => {
        showToast("Unable to subscribe right now. Please try again.");
    });
}

/* Catalog Live Filter Engine */
let searchDebounceTimer;

function handleCatalogSearch(input) {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
        applyCatalogFilters();
    }, 350);
}

function handleCategoryTabClick(tab) {
    document.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    applyCatalogFilters();
}

function handleSortChange() {
    applyCatalogFilters();
}

function applyCatalogFilters() {
    const activeTab = document.querySelector('.category-tab.active');
    const category = activeTab ? activeTab.dataset.cat : 'all';
    const searchInput = document.getElementById('search-input');
    const query = searchInput ? searchInput.value.trim() : '';
    const sortSelect = document.getElementById('sort-select');
    const sortBy = sortSelect ? sortSelect.value : 'featured';

    const params = new URLSearchParams();
    if (category && category !== 'all') params.set('category', category);
    if (query) params.set('q', query);
    if (sortBy) params.set('sort', sortBy);
    params.set('ajax', '1');

    const grid = document.getElementById('product-grid');
    if (!grid) return;

    grid.style.opacity = '0.5';

    fetch(`/catalog/?${params.toString()}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(res => res.text())
    .then(html => {
        grid.innerHTML = html;
        grid.style.opacity = '1';
        initScrollReveal();
    })
    .catch(err => {
        console.error('Filter error:', err);
        grid.style.opacity = '1';
    });
}

function clearFilters() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) searchInput.value = '';
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) sortSelect.value = 'featured';
    
    document.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
    const allTab = document.querySelector('.category-tab[data-cat="all"]');
    if (allTab) allTab.classList.add('active');

    applyCatalogFilters();
}
