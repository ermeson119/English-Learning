// JavaScript principal da plataforma

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips do Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicializar popovers do Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts após 5 segundos
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Smooth scroll para links internos
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Confirmar ações destrutivas
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Loading state para formulários
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Carregando...';
            }
        });
    });
});

// Funções utilitárias
const Utils = {
    // Formatar tempo em segundos para MM:SS
    formatTime: function(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    },

    // Mostrar notificação toast
    showToast: function(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remover toast após ser ocultado
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    },

    // Criar container para toasts
    createToastContainer: function() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
        return container;
    },

    // Copiar texto para clipboard
    copyToClipboard: function(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showToast('Texto copiado para a área de transferência!', 'success');
        }).catch(() => {
            this.showToast('Erro ao copiar texto', 'danger');
        });
    },

    // Validar email
    isValidEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Funcionalidades específicas para atividades
const AtividadeManager = {
    // Responder atividade via AJAX
    responderAtividade: function(atividadeId, resposta) {
        const formData = new FormData();
        formData.append('resposta', resposta);

        fetch(`/aluno/atividades/${atividadeId}/responder`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            this.processarRespostaAtividade(data, atividadeId);
        })
        .catch(error => {
            console.error('Erro ao responder atividade:', error);
            Utils.showToast('Erro ao enviar resposta. Tente novamente.', 'danger');
        });
    },

    // Processar resposta da atividade
    processarRespostaAtividade: function(data, atividadeId) {
        const atividadeCard = document.querySelector(`[data-atividade-id="${atividadeId}"]`);
        
        if (data.sucesso) {
            atividadeCard.classList.add('correta');
            atividadeCard.classList.remove('incorreta');
            Utils.showToast(data.mensagem, 'success');
            
            // Atualizar pontuação se existir elemento
            const pontuacaoElement = document.querySelector('.pontuacao-total');
            if (pontuacaoElement) {
                const pontuacaoAtual = parseInt(pontuacaoElement.textContent) || 0;
                pontuacaoElement.textContent = pontuacaoAtual + data.pontuacao;
            }
        } else {
            atividadeCard.classList.add('incorreta');
            atividadeCard.classList.remove('correta');
            Utils.showToast(data.mensagem, 'warning');
        }

        // Atualizar contador de tentativas
        const tentativasElement = atividadeCard.querySelector('.tentativas');
        if (tentativasElement) {
            tentativasElement.textContent = `Tentativas: ${data.tentativas}`;
        }
    }
};

// Funcionalidades para vídeos
const VideoManager = {
    // Marcar vídeo como assistido
    marcarComoAssistido: function(videoId) {
        // Implementar lógica para marcar vídeo como assistido
        console.log(`Vídeo ${videoId} marcado como assistido`);
    },

    // Controlar progresso do vídeo
    atualizarProgresso: function(videoId, tempoAtual, duracao) {
        const progresso = (tempoAtual / duracao) * 100;
        
        // Atualizar barra de progresso se existir
        const progressBar = document.querySelector(`[data-video-id="${videoId}"] .progress-bar`);
        if (progressBar) {
            progressBar.style.width = `${progresso}%`;
            progressBar.setAttribute('aria-valuenow', progresso);
        }

        // Marcar como assistido se chegou a 90%
        if (progresso >= 90) {
            this.marcarComoAssistido(videoId);
        }
    }
};

// Funcionalidades para ranking
const RankingManager = {
    // Atualizar ranking em tempo real
    atualizarRanking: function(turmaId) {
        fetch(`/api/ranking/${turmaId}`)
        .then(response => response.json())
        .then(data => {
            this.renderizarRanking(data);
        })
        .catch(error => {
            console.error('Erro ao atualizar ranking:', error);
        });
    },

    // Renderizar ranking na página
    renderizarRanking: function(rankingData) {
        const rankingContainer = document.querySelector('#ranking-container');
        if (!rankingContainer) return;

        let html = '';
        rankingData.forEach((item, index) => {
            const posicao = index + 1;
            const classePosition = posicao === 1 ? 'first' : posicao === 2 ? 'second' : posicao === 3 ? 'third' : '';
            
            html += `
                <div class="ranking-item d-flex align-items-center p-3 border-bottom">
                    <div class="ranking-position ${classePosition} me-3">
                        ${posicao}
                    </div>
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${item.aluno.nome}</h6>
                        <small class="text-muted">Pontuação: ${item.pontuacao}</small>
                    </div>
                    <div class="text-end">
                        <span class="badge bg-primary">${item.pontuacao} pts</span>
                    </div>
                </div>
            `;
        });

        rankingContainer.innerHTML = html;
    }
};

// Exportar para uso global
window.Utils = Utils;
window.AtividadeManager = AtividadeManager;
window.VideoManager = VideoManager;
window.RankingManager = RankingManager;