// ── API CLIENT ──
const API = {
  base: '/api/v1',
  token: () => localStorage.getItem('token'),
  headers: () => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${API.token()}`
  }),
  get:    (path)       => fetch(API.base+path, {headers:API.headers()}).then(r=>r.json()),
  post:   (path, body) => fetch(API.base+path, {method:'POST', headers:API.headers(), body:JSON.stringify(body)}).then(r=>r.json()),
  delete: (path)       => fetch(API.base+path, {method:'DELETE', headers:API.headers()}).then(r=>r.json()),
}

// ── AUTH HELPERS ──
function requireAuth() { 
  if (!localStorage.getItem('token') && window.location.pathname !== '/login' && window.location.pathname !== '/signup') {
    window.location.href='/login'; 
  }
}

function logout() { 
  localStorage.clear(); 
  window.location.href='/login'; 
}

// ── FORMAT HELPERS ──
const fmt = {
  money:    n => '$'+Number(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}),
  pct:      n => (n>=0?'+':'')+Number(n).toFixed(2)+'%',
  score:    n => (Number(n)*100).toFixed(1)+'%',
  datetime: s => new Date(s).toLocaleString('en-US',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}),
}

function buildAvatarDataUri(user) {
  const label = user?.name || user?.username || user?.email || 'U';
  const initials = label
    .split(' ')
    .map(w => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || 'U';
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect width="100" height="100" fill="#1a1f26" rx="50"/><text x="50" y="56" text-anchor="middle" fill="#00daf3" font-size="36" font-family="sans-serif">${initials}</text></svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

// ── TOAST SYSTEM ──
function toast(title, msg, type='info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none';
    document.body.appendChild(container);
  }

  const el = document.createElement('div');
  const borderColor = type === 'error' ? 'border-error' : (type === 'success' ? 'border-secondary' : 'border-primary');
  const textColor = type === 'error' ? 'text-error' : (type === 'success' ? 'text-secondary' : 'text-primary');
  
  el.className = `bg-surface-container border-l-4 ${borderColor} p-4 rounded shadow-lg animate-[fadeUp_0.3s_ease-out] w-80 pointer-events-auto flex items-start gap-3 backdrop-blur-md bg-opacity-90`;
  
  let icon = 'info';
  if(type === 'error') icon = 'error';
  if(type === 'success') icon = 'check_circle';

  el.innerHTML = `
    <span class="material-symbols-outlined ${textColor}">${icon}</span>
    <div>
      <h4 class="text-sm font-bold text-on-surface">${title}</h4>
      <p class="text-xs text-on-surface-variant mt-1">${msg}</p>
    </div>
  `;

  container.appendChild(el);
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(-10px)';
    el.style.transition = 'all 0.3s ease';
    setTimeout(() => el.remove(), 300);
  }, 4000);
}

// ── SIDEBAR ACTIVE STATE & RESPONSIVENESS ──
document.addEventListener('DOMContentLoaded', () => {
  requireAuth(); // Ensure auth on load
  
  const path = window.location.pathname;
  document.querySelectorAll('aside nav a').forEach(a => {
    const href = a.getAttribute('href');
    if (href === path) {
      a.classList.add('bg-[#272A2E]', 'border-[#00E5FF]', 'text-[#00E5FF]');
      a.classList.remove('text-[#E1E2E7]/60', 'hover:text-[#E1E2E7]', 'border-transparent');
    } else {
      a.classList.remove('bg-[#272A2E]', 'border-[#00E5FF]', 'text-[#00E5FF]');
      a.classList.add('text-[#E1E2E7]/60', 'hover:text-[#E1E2E7]', 'border-transparent');
    }
  });

  // Attach logout handlers reliably across pages
  document.querySelectorAll('button').forEach(btn => {
    const text = (btn.textContent || '').trim();
    const icon = btn.querySelector('.material-symbols-outlined')?.textContent?.trim();
    if (text.includes('Logout') || icon === 'logout' || btn.dataset.action === 'logout') {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        logout();
      });
    }
  });

  // Mobile menu handlers
  const mobileMenuBtn = document.getElementById('mobile-menu-btn');
  const closeSidebarBtn = document.getElementById('close-sidebar-btn');
  const sidebar = document.getElementById('sidebar');

  if (mobileMenuBtn && sidebar) {
    mobileMenuBtn.addEventListener('click', () => {
      sidebar.classList.remove('-translate-x-full');
    });
  }
  if (closeSidebarBtn && sidebar) {
    closeSidebarBtn.addEventListener('click', () => {
      sidebar.classList.add('-translate-x-full');
    });
  }

  // Profile modal and data fetching
  if (window.location.pathname !== '/login' && window.location.pathname !== '/signup') {
    initProfile();
  }
});

async function initProfile() {
  try {
    const user = await API.get('/auth/me');
    if (user) {
      const avatarSrc = !user.avatar_url || user.avatar_url.includes('default-avatar.png')
        ? buildAvatarDataUri(user)
        : user.avatar_url;
      document.querySelectorAll('.rounded-full.overflow-hidden').forEach(el => {
        el.innerHTML = `<img src="${avatarSrc}" class="w-full h-full object-cover">`;
      });
    }
    
    // Attach settings button handler
    const settingsBtns = document.querySelectorAll('.material-symbols-outlined');
    settingsBtns.forEach(btn => {
      if (btn.textContent.trim() === 'settings') {
        const parentBtn = btn.closest('button');
        if (parentBtn) {
          parentBtn.addEventListener('click', () => openProfileModal(user));
        }
      }
    });
  } catch (err) {
    console.warn("Could not fetch user profile details.");
  }
}

function openProfileModal(user) {
  let modal = document.getElementById('profile-modal');
  if (!modal) {
    const modalAvatarSrc = !user.avatar_url || user.avatar_url.includes('default-avatar.png')
      ? buildAvatarDataUri(user)
      : user.avatar_url;
    modal = document.createElement('div');
    modal.id = 'profile-modal';
    modal.className = 'fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm';
    modal.innerHTML = `
      <div class="bg-surface-container-high rounded-2xl p-8 w-full max-w-md border border-outline-variant/20 shadow-2xl relative">
        <button id="close-profile" class="absolute top-4 right-4 text-on-surface-variant hover:text-on-surface"><span class="material-symbols-outlined">close</span></button>
        <h2 class="text-2xl font-bold font-headline mb-6">Profile Settings</h2>
        
        <div class="flex items-center gap-6 mb-6">
          <div class="w-20 h-20 rounded-full bg-surface-container overflow-hidden border border-outline-variant/30 relative group cursor-pointer" id="avatar-container">
            <img id="modal-avatar" src="${modalAvatarSrc}" class="w-full h-full object-cover">
            <div class="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <span class="material-symbols-outlined text-white">upload</span>
            </div>
            <input type="file" id="avatar-upload" class="hidden" accept="image/*">
          </div>
          <div>
            <p class="text-sm font-bold text-on-surface-variant uppercase tracking-widest">Avatar</p>
            <p class="text-xs text-on-surface-variant/60">Click image to update.</p>
          </div>
        </div>

        <div class="space-y-4">
          <div>
            <label class="block text-xs uppercase tracking-widest text-on-surface-variant font-bold mb-1">Username</label>
            <input id="profile-username" type="text" value="${user.username || ''}" class="w-full bg-surface-container-highest border border-outline-variant/30 rounded-xl px-4 py-3 text-sm focus:ring-1 focus:ring-primary text-on-surface">
          </div>
          <div>
            <label class="block text-xs uppercase tracking-widest text-on-surface-variant font-bold mb-1">Email</label>
            <input id="profile-email" type="email" value="${user.email || ''}" class="w-full bg-surface-container-highest border border-outline-variant/30 rounded-xl px-4 py-3 text-sm focus:ring-1 focus:ring-primary text-on-surface">
          </div>
        </div>
        
        <div class="mt-8 flex justify-end gap-3">
          <button id="cancel-profile" class="px-4 py-2 rounded-xl text-sm font-bold text-on-surface-variant hover:bg-surface-container">Cancel</button>
          <button id="save-profile" class="px-6 py-2 bg-primary-container text-on-primary-container rounded-xl text-sm font-bold shadow hover:opacity-90">Save Changes</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    document.getElementById('close-profile').addEventListener('click', () => modal.remove());
    document.getElementById('cancel-profile').addEventListener('click', () => modal.remove());
    
    // Upload logic
    const fileInput = document.getElementById('avatar-upload');
    document.getElementById('avatar-container').addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const formData = new FormData();
      formData.append('file', file);
      try {
        const res = await fetch(API.base + '/profile/image', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${API.token()}` },
          body: formData
        }).then(r => r.json());
        
        if (res.avatar_url) {
          document.getElementById('modal-avatar').src = res.avatar_url;
          document.getElementById('modal-avatar').classList.remove('hidden');
          toast('Success', 'Avatar updated', 'success');
          initProfile(); // Refresh avatars elsewhere
        }
      } catch (err) {
        toast('Error', 'Failed to upload image', 'error');
      }
    });

    // Save profile logic
    document.getElementById('save-profile').addEventListener('click', async () => {
      const username = document.getElementById('profile-username').value;
      const email = document.getElementById('profile-email').value;
      try {
        const res = await fetch(API.base + '/profile', {
            method: 'PUT',
            headers: API.headers(),
            body: JSON.stringify({ username, email })
        });
        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Update failed');
        }
        toast('Success', 'Profile updated', 'success');
        modal.remove();
      } catch (err) {
        toast('Error', err.message || 'Failed to update profile', 'error');
      }
    });
  }
}
