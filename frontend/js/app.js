// le o login do localStorage, monta o menu certo e troca as telas

const MENUS = {
  TI: [
    { id: 'dashboard', label: 'Dashboard', icon: 'speedometer2' },
    { id: 'usuarios', label: 'Usuários', icon: 'people' },
    { id: 'pessoas', label: 'Pessoas', icon: 'person-vcard' },
    { id: 'processos', label: 'Processos', icon: 'folder' },
    { id: 'sorteio', label: 'Sorteio', icon: 'shuffle' },
    { id: 'conflitos', label: 'Conflitos', icon: 'exclamation-triangle' },
  ],
  JUIZ: [
    { id: 'meus-processos', label: 'Meus Processos', icon: 'folder' },
    { id: 'processos', label: 'Todos os Processos', icon: 'collection' },
    { id: 'reg-conflito', label: 'Registrar Conflito', icon: 'exclamation-triangle' },
    { id: 'logs', label: 'Logs de Sorteio', icon: 'list-ul' },
  ],
  ASSESSOR: [
    { id: 'assessor-processos', label: 'Processos do Meu Juiz', icon: 'folder' },
    { id: 'pessoas', label: 'Pessoas', icon: 'person-vcard' },
  ],
  ASSISTENTE: [
    { id: 'cad-pessoa', label: 'Cadastrar Pessoa', icon: 'person-plus' },
    { id: 'cad-processo', label: 'Cadastrar Processo', icon: 'plus-square' },
    { id: 'meus-cadastros', label: 'Meus Cadastros', icon: 'list-check' },
  ],
  JUIZ_EXTERNO: [
    { id: 'juiz-externo', label: 'Meu Processo', icon: 'folder' },
  ],
};

let auth = null;

function alerta(tipo, msg) {
  const area = document.getElementById('alerta-area');
  const div = document.createElement('div');
  div.className = `alert alert-${tipo} alert-dismissible fade show`;
  div.innerHTML = `${msg}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
  area.appendChild(div);
  setTimeout(() => div.remove(), 5000);
}

function mostrarTela(id) {
  document.querySelectorAll('section.tela').forEach(s => s.classList.remove('ativa'));
  const el = document.getElementById('tela-' + id);
  if (el) el.classList.add('ativa');
  document.querySelectorAll('#sidebar-menu .nav-link').forEach(l => l.classList.remove('active'));
  const link = document.querySelector(`#sidebar-menu [data-tela="${id}"]`);
  if (link) link.classList.add('active');
  carregarTela(id);
}

function badgeNivel(n) { return `<span class="badge badge-nivel-${n}">Nível ${n}</span>`; }
function badgeStatus(s) { return `<span class="badge badge-status-${s}">${s}</span>`; }
function badgeMotivo(m) { return `<span class="badge badge-motivo-${m}">${m}</span>`; }
function fmtDate(s) { return s ? new Date(s).toLocaleString('pt-BR') : '—'; }

async function carregarTela(id) {
  try {
    if (id === 'dashboard') await renderDashboard();
    else if (id === 'usuarios') await renderUsuarios();
    else if (id === 'pessoas') await renderPessoas();
    else if (id === 'processos') await recarregarProcessos();
    else if (id === 'sorteio') await renderLogs('tabela-logs');
    else if (id === 'logs') await renderLogs('tabela-logs2');
    else if (id === 'conflitos') await renderConflitos();
    else if (id === 'reg-conflito') await renderRegConflito();
    else if (id === 'meus-processos') await renderMeusProcessos();
    else if (id === 'assessor-processos') await renderAssessorProcessos();
    else if (id === 'meus-cadastros') await renderMeusCadastros();
    else if (id === 'cad-processo') await carregarPessoasSelect();
    else if (id === 'juiz-externo') await renderJuizExterno();
  } catch (err) { alerta('danger', err.message); }
}

async function renderDashboard() {
  const procs = await api('/processos/');
  const cont = { PENDENTE: 0, SORTEADO: 0, AGUARDANDO_JUIZ_EXTERNO: 0, ENCERRADO: 0 };
  procs.forEach(p => { cont[p.status] = (cont[p.status] || 0) + 1; });
  const users = await api('/usuarios/').catch(() => []);
  const logs = await api('/sorteio/logs').catch(() => []);
  const ultLog = logs[0] ? fmtDate(logs[0].criado_em) : '—';
  document.getElementById('dash-cards').innerHTML = `
    <div class="col-md-3"><div class="card"><div class="card-body"><h6>Pendentes</h6><h3>${cont.PENDENTE}</h3></div></div></div>
    <div class="col-md-3"><div class="card"><div class="card-body"><h6>Sorteados</h6><h3>${cont.SORTEADO}</h3></div></div></div>
    <div class="col-md-3"><div class="card"><div class="card-body"><h6>Aguardando Externo</h6><h3>${cont.AGUARDANDO_JUIZ_EXTERNO}</h3></div></div></div>
    <div class="col-md-3"><div class="card"><div class="card-body"><h6>Usuários</h6><h3>${users.length}</h3></div></div></div>
    <div class="col-md-6"><div class="card"><div class="card-body"><h6>Último sorteio</h6><p>${ultLog}</p></div></div></div>
  `;
}

async function renderUsuarios() {
  const users = await api('/usuarios/');
  document.getElementById('tabela-usuarios').innerHTML = users.map(u => `
    <tr>
      <td>${u.id}</td><td>${u.login}</td><td>${u.nome}</td><td>${u.perfil}</td>
      <td>${u.ativo ? '<span class="text-success">Sim</span>' : '<span class="text-danger">Não</span>'}</td>
      <td>${u.ativo ? `<button class="btn btn-sm btn-outline-danger" onclick="desativarUsuario(${u.id})">Desativar</button>` : ''}</td>
    </tr>`).join('');
}

async function desativarUsuario(id) {
  if (!confirm('Desativar este usuário?')) return;
  await api('/usuarios/' + id, { method: 'DELETE' });
  alerta('success', 'Usuário desativado');
  renderUsuarios();
}

function abrirModalUsuario() {
  document.getElementById('form-usuario').reset();
  new bootstrap.Modal('#modal-usuario').show();
}

async function renderPessoas() {
  const ps = await api('/pessoas/');
  document.getElementById('tabela-pessoas').innerHTML = ps.map(p => `
    <tr><td>${p.id}</td><td>${p.tipo}</td><td>${p.documento}</td><td>${p.nome}</td></tr>`).join('');
}

function abrirModalPessoa() { mostrarTela('cad-pessoa'); }

async function recarregarProcessos() {
  const procs = await api('/processos/');
  const fs = document.getElementById('filtro-status')?.value || '';
  const fn = document.getElementById('filtro-nivel')?.value || '';
  const filtrados = procs.filter(p => (!fs || p.status === fs) && (!fn || String(p.nivel) === fn));
  document.getElementById('tabela-processos').innerHTML = filtrados.map(p => {
    const acoes = [];
    if (auth.perfil === 'TI' && p.status === 'AGUARDANDO_JUIZ_EXTERNO') {
      acoes.push(`<button class="btn btn-sm btn-warning" onclick="abrirDesignarExterno(${p.id})">Designar externo</button>`);
    }
    return `<tr>
      <td>${p.numero}</td><td>${p.descricao}</td><td>${badgeNivel(p.nivel)}</td>
      <td>${p.pessoa_id}</td><td>${badgeStatus(p.status)}</td>
      <td>${p.juiz_id || '—'}</td><td>${acoes.join(' ')}</td>
    </tr>`;
  }).join('');
}

async function renderLogs(tbodyId) {
  const logs = await api('/sorteio/logs');
  document.getElementById(tbodyId).innerHTML = logs.map(l => `
    <tr><td>${fmtDate(l.criado_em)}</td><td>${l.processo_id}</td><td>${l.juiz_id}</td>
        <td>${badgeMotivo(l.motivo)}</td><td>${l.detalhes || ''}</td></tr>`).join('');
}

async function renderConflitos() {
  const cs = await api('/conflitos/');
  document.getElementById('tabela-conflitos').innerHTML = cs.map(c => `
    <tr><td>${c.id}</td><td>${c.processo_id}</td><td>${c.juiz_id}</td>
        <td>${c.justificativa}</td><td>${fmtDate(c.registrado_em)}</td></tr>`).join('');
}

async function renderRegConflito() {
  const procs = await api('/processos/');
  const meus = procs.filter(p => p.juiz_id === auth.juiz_id && p.status === 'SORTEADO');
  document.getElementById('conf-processo').innerHTML = meus.map(p =>
    `<option value="${p.id}">${p.numero} - ${p.descricao}</option>`).join('');
}

async function renderMeusProcessos() {
  const procs = await api('/processos/');
  const meus = procs.filter(p => p.juiz_id === auth.juiz_id);
  document.getElementById('tabela-meus-processos').innerHTML = meus.map(p => {
    const acoes = [];
    if (p.status === 'SORTEADO') {
      acoes.push(`<button class="btn btn-sm btn-outline-primary" onclick="abrirAutorizar(${p.id})">Autorizar edição</button>`);
      acoes.push(`<button class="btn btn-sm btn-outline-secondary" onclick="marcarReabertura(${p.id})">Marcar reabertura</button>`);
    }
    return `<tr><td>${p.numero}</td><td>${p.descricao}</td><td>${badgeNivel(p.nivel)}</td>
      <td>${badgeStatus(p.status)}</td><td>${acoes.join(' ')}</td></tr>`;
  }).join('');
}

async function marcarReabertura(pid) {
  if (!confirm('Marcar como reabertura? O processo volta para PENDENTE.')) return;
  await api(`/processos/${pid}/marcar-reabertura`, { method: 'POST' });
  alerta('success', 'Marcado como reabertura.');
  renderMeusProcessos();
}

async function abrirAutorizar(pid) {
  document.getElementById('aut-pid').value = pid;
  const users = await api('/usuarios/').catch(() => []);
  // O endpoint /usuarios/ só funciona para TI. Para juízes, listar genericamente o assessor:
  // Como o juiz só tem assessores vinculados a ele, fazemos um fallback simples.
  let opts = '';
  if (users.length) {
    opts = users.filter(u => u.perfil === 'ASSESSOR' && u.ativo).map(u =>
      `<option value="${u.id}">${u.nome}</option>`).join('');
  } else {
    // Fallback: assessor_id desconhecido, pede ID manualmente.
    opts = '<option value="">Digite o ID do assessor</option>';
  }
  document.getElementById('aut-assessor').innerHTML = opts;
  new bootstrap.Modal('#modal-autorizar').show();
}

async function renderAssessorProcessos() {
  const procs = await api('/processos/');
  document.getElementById('tabela-assessor-processos').innerHTML = procs.map(p => {
    const acaoEdit = p.status === 'SORTEADO'
      ? `<button class="btn btn-sm btn-outline-primary" onclick="tentarEditar(${p.id})">Editar</button>`
      : '<i class="bi bi-lock"></i> <small class="text-muted">Aguardando autorização</small>';
    return `<tr><td>${p.numero}</td><td>${p.descricao}</td><td>${badgeNivel(p.nivel)}</td>
      <td>${badgeStatus(p.status)}</td><td>${acaoEdit}</td></tr>`;
  }).join('');
}

async function tentarEditar(pid) {
  const nova = prompt('Nova descrição (em branco cancela):');
  if (!nova) return;
  try {
    await api('/processos/' + pid, { method: 'PATCH', body: { descricao: nova } });
    alerta('success', 'Processo editado.');
    renderAssessorProcessos();
  } catch (e) { alerta('danger', e.message); }
}

async function renderMeusCadastros() {
  const procs = await api('/processos/');
  document.getElementById('tabela-meus-cadastros').innerHTML = procs.map(p => {
    const editar = p.status === 'cadastrado'
      ? `<button class="btn btn-sm btn-outline-primary" onclick="editarMeuCadastro(${p.id})">Editar</button>`
      : '';
    return `<tr><td>${p.numero}</td><td>${p.descricao}</td><td>${badgeNivel(p.nivel)}</td>
      <td>${p.pessoa_id}</td><td>${p.status}</td><td>${editar}</td></tr>`;
  }).join('');
}

async function editarMeuCadastro(pid) {
  const nova = prompt('Nova descrição:');
  if (!nova) return;
  try {
    await api('/processos/' + pid, { method: 'PATCH', body: { descricao: nova } });
    alerta('success', 'Atualizado.');
    renderMeusCadastros();
  } catch (e) { alerta('danger', e.message); }
}

async function carregarPessoasSelect() {
  const ps = await api('/pessoas/');
  document.getElementById('proc-pessoa').innerHTML = ps.map(p =>
    `<option value="${p.id}">${p.nome} (${p.documento})</option>`).join('');
}

async function renderJuizExterno() {
  const procs = await api('/processos/');
  if (!procs.length) {
    document.getElementById('card-juiz-externo').innerHTML =
      '<p class="text-muted">Nenhum processo designado.</p>';
    return;
  }
  const p = procs[0];
  document.getElementById('card-juiz-externo').innerHTML = `
    <div class="card"><div class="card-body">
      <h5>Processo ${p.numero}</h5>
      <p>${p.descricao}</p>
      <p>${badgeNivel(p.nivel)} ${badgeStatus(p.status)}</p>
    </div></div>`;
}

function abrirDesignarExterno(pid) {
  document.getElementById('ext-pid').value = pid;
  document.getElementById('ext-login').value = '';
  document.getElementById('ext-senha').value = '';
  document.getElementById('ext-nome').value = '';
  new bootstrap.Modal('#modal-externo').show();
}

function init() {
  auth = getAuth();
  if (!auth) { window.location.href = '/'; return; }
  document.getElementById('nav-user').textContent = `${auth.nome} (${auth.perfil})`;
  document.getElementById('btn-sair').addEventListener('click', () => {
    clearAuth(); window.location.href = '/';
  });

  const menu = MENUS[auth.perfil] || [];
  const ul = document.getElementById('sidebar-menu');
  ul.innerHTML = menu.map(m => `
    <li class="nav-item"><a class="nav-link" data-tela="${m.id}">
      <i class="bi bi-${m.icon}"></i> ${m.label}</a></li>`).join('');
  ul.querySelectorAll('.nav-link').forEach(l =>
    l.addEventListener('click', () => mostrarTela(l.dataset.tela)));
  if (menu[0]) mostrarTela(menu[0].id);

  // Handlers de formulário
  document.getElementById('btn-salvar-usuario')?.addEventListener('click', async () => {
    try {
      await api('/usuarios/', { method: 'POST', body: {
        login: document.getElementById('u-login').value,
        senha: document.getElementById('u-senha').value,
        nome: document.getElementById('u-nome').value,
        perfil: document.getElementById('u-perfil').value,
      }});
      bootstrap.Modal.getInstance('#modal-usuario').hide();
      alerta('success', 'Usuário criado'); renderUsuarios();
    } catch (e) { alerta('danger', e.message); }
  });

  document.getElementById('form-processo')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      await api('/processos/', { method: 'POST', body: {
        numero: document.getElementById('proc-numero').value,
        descricao: document.getElementById('proc-descricao').value,
        nivel: parseInt(document.getElementById('proc-nivel').value),
        pessoa_id: parseInt(document.getElementById('proc-pessoa').value),
      }});
      alerta('success', 'Processo cadastrado'); e.target.reset();
    } catch (err) { alerta('danger', err.message); }
  });

  document.getElementById('form-pessoa')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const tipo = document.querySelector('input[name="pessoa-tipo"]:checked').value;
    const doc = document.getElementById('pessoa-doc').value.replace(/\D/g, '');
    if (tipo === 'PF' && doc.length !== 11) return alerta('danger', 'CPF deve ter 11 dígitos');
    if (tipo === 'PJ' && doc.length !== 14) return alerta('danger', 'CNPJ deve ter 14 dígitos');
    try {
      await api('/pessoas/', { method: 'POST', body: {
        tipo, documento: doc, nome: document.getElementById('pessoa-nome').value,
      }});
      alerta('success', 'Pessoa cadastrada'); e.target.reset();
    } catch (err) { alerta('danger', err.message); }
  });

  document.getElementById('btn-executar-sorteio')?.addEventListener('click', async () => {
    if (!confirm('Executar sorteio agora?')) return;
    try {
      const r = await api('/sorteio/executar', { method: 'POST' });
      alerta('success', `${r.processos_sorteados} processo(s) sorteado(s).`);
      renderLogs('tabela-logs');
    } catch (e) { alerta('danger', e.message); }
  });

  document.getElementById('form-conflito')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData();
    fd.append('processo_id', document.getElementById('conf-processo').value);
    fd.append('justificativa', document.getElementById('conf-just').value);
    fd.append('documento', document.getElementById('conf-doc').files[0]);
    try {
      await api('/conflitos/', { method: 'POST', body: fd });
      alerta('success', 'Conflito registrado.'); e.target.reset();
    } catch (err) { alerta('danger', err.message); }
  });

  document.getElementById('btn-salvar-externo')?.addEventListener('click', async () => {
    try {
      await api('/conflitos/designar-juiz-externo', { method: 'POST', body: {
        processo_id: parseInt(document.getElementById('ext-pid').value),
        login: document.getElementById('ext-login').value,
        senha: document.getElementById('ext-senha').value,
        nome: document.getElementById('ext-nome').value,
      }});
      bootstrap.Modal.getInstance('#modal-externo').hide();
      alerta('success', 'Juiz externo designado.'); recarregarProcessos();
    } catch (e) { alerta('danger', e.message); }
  });

  document.getElementById('btn-salvar-autorizar')?.addEventListener('click', async () => {
    try {
      const aid = parseInt(document.getElementById('aut-assessor').value);
      const pid = parseInt(document.getElementById('aut-pid').value);
      await api(`/processos/${pid}/autorizar-edicao`, { method: 'POST', body: { assessor_id: aid }});
      bootstrap.Modal.getInstance('#modal-autorizar').hide();
      alerta('success', 'Autorização concedida.');
    } catch (e) { alerta('danger', e.message); }
  });
}

document.addEventListener('DOMContentLoaded', init);
