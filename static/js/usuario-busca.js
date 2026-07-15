(function () {
    function debounce(fn, wait) {
        let timer;
        return function (...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), wait);
        };
    }

    function initUsuarioBusca(container) {
        if (container.dataset.usuarioBuscaInit) return;
        const input = container.querySelector('.usuario-busca-input');
        const hidden = container.querySelector('.usuario-busca-hidden');
        const resultados = container.querySelector('.usuario-busca-resultados');
        const url = container.dataset.searchUrl;
        if (!input || !hidden || !resultados || !url) return;
        container.dataset.usuarioBuscaInit = '1';

        function esconderResultados() {
            resultados.innerHTML = '';
            resultados.classList.add('d-none');
        }

        function buscar(termo) {
            fetch(`${url}?q=${encodeURIComponent(termo)}`)
                .then((r) => r.json())
                .then((data) => {
                    resultados.innerHTML = '';
                    if (!data.resultados || !data.resultados.length) {
                        esconderResultados();
                        return;
                    }
                    data.resultados.forEach((pessoa) => {
                        const item = document.createElement('button');
                        item.type = 'button';
                        item.className = 'list-group-item list-group-item-action';
                        const detalhe = pessoa.identificador
                            ? `${pessoa.tipo} · ${pessoa.identificador} · ${pessoa.email}`
                            : `${pessoa.tipo} · ${pessoa.email}`;
                        item.innerHTML = `${pessoa.nome} <span class="text-muted small">(${detalhe})</span>`;
                        item.addEventListener('mousedown', (e) => {
                            e.preventDefault();
                            hidden.value = pessoa.id;
                            input.value = pessoa.nome;
                            esconderResultados();
                        });
                        resultados.appendChild(item);
                    });
                    resultados.classList.remove('d-none');
                })
                .catch(() => esconderResultados());
        }

        const buscarDebounced = debounce(buscar, 250);

        input.addEventListener('input', () => {
            hidden.value = '';
            buscarDebounced(input.value.trim());
        });
        input.addEventListener('focus', () => buscar(input.value.trim()));
        input.addEventListener('blur', () => setTimeout(esconderResultados, 150));
    }

    window.initUsuarioBusca = initUsuarioBusca;

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.usuario-busca').forEach(initUsuarioBusca);
    });
})();
