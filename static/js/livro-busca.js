(function () {
    function debounce(fn, wait) {
        let timer;
        return function (...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), wait);
        };
    }

    function initLivroBusca(container) {
        if (container.dataset.livroBuscaInit) return;
        const input = container.querySelector('.livro-busca-input');
        const hidden = container.querySelector('.livro-busca-hidden');
        const resultados = container.querySelector('.livro-busca-resultados');
        const url = container.dataset.searchUrl;
        if (!input || !hidden || !resultados || !url) return;
        container.dataset.livroBuscaInit = '1';

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
                    data.resultados.forEach((livro) => {
                        const item = document.createElement('button');
                        item.type = 'button';
                        item.className = 'list-group-item list-group-item-action';
                        item.innerHTML = `${livro.titulo} <span class="text-muted small">(${livro.disponiveis} disponível${livro.disponiveis === 1 ? '' : 'eis'})</span>`;
                        item.addEventListener('mousedown', (e) => {
                            e.preventDefault();
                            hidden.value = livro.id;
                            input.value = livro.titulo;
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

    window.initLivroBusca = initLivroBusca;

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.livro-busca').forEach(initLivroBusca);
    });
})();
