const API_BASE = '';

function getAuth() {
  return JSON.parse(localStorage.getItem('auth') || 'null');
}

function setAuth(auth) {
  localStorage.setItem('auth', JSON.stringify(auth));
}

function clearAuth() {
  localStorage.removeItem('auth');
}

async function api(path, opts = {}) {
  const auth = getAuth();
  const headers = opts.headers || {};
  if (auth?.token) headers['Authorization'] = `Bearer ${auth.token}`;
  if (!(opts.body instanceof FormData) && opts.body && typeof opts.body !== 'string') {
    headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(opts.body);
  }
  const r = await fetch(API_BASE + path, { ...opts, headers });
  if (r.status === 401) {
    clearAuth();
    window.location.href = '/';
    return;
  }
  const text = await r.text();
  const data = text ? JSON.parse(text) : null;
  if (!r.ok) throw new Error(data?.detail || 'Erro na requisição');
  return data;
}
