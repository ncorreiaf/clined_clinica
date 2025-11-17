/**
 * JavaScript principal do Sistema Spa Terapêutico Clined
 * Contém funcionalidades comuns e interações do frontend
 */

// Aguarda o carregamento completo do DOM
document.addEventListener('DOMContentLoaded', function() {
    
    // Inicialização das funcionalidades
    initCurrentTime();
    initTooltips();
    initFormValidation();
    initAutoRefresh();
    initKeyboardShortcuts();
    initLocalStorage();
    
    console.log('Sistema Spa Terapêutico Clined inicializado com sucesso!');
});

/**
 * Atualiza o relógio em tempo real na navbar
 */
function initCurrentTime() {
    const timeElement = document.getElementById('current-time');
    
    if (timeElement) {
        function updateTime() {
            const now = new Date();
            const timeString = now.toLocaleTimeString('pt-BR', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            const dateString = now.toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
            
            timeElement.innerHTML = `${dateString} - ${timeString}`;
        }
        
        // Atualiza imediatamente e depois a cada segundo
        updateTime();
        setInterval(updateTime, 1000);
    }
}

/**
 * Inicializa tooltips do Bootstrap em toda a aplicação
 */
function initTooltips() {
    // Inicializa tooltips do Bootstrap 5
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Configurações gerais de validação de formulários
 */
function initFormValidation() {
    // Validação de CPF em tempo real
    const cpfInputs = document.querySelectorAll('input[name*="cpf"]');
    cpfInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            const cpf = e.target.value.replace(/\D/g, '');
            
            // Formatar CPF: 000.000.000-00
            if (cpf.length <= 11) {
                const formatted = cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
                e.target.value = formatted;
            }
            
            // Validar CPF
            if (cpf.length === 11) {
                const isValid = validateCPF(cpf);
                e.target.classList.toggle('is-invalid', !isValid);
                e.target.classList.toggle('is-valid', isValid);
                
                // Exibir mensagem de erro
                let feedback = e.target.parentNode.querySelector('.invalid-feedback');
                if (!feedback && !isValid) {
                    feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = 'CPF inválido';
                    e.target.parentNode.appendChild(feedback);
                } else if (feedback && isValid) {
                    feedback.remove();
                }
            }
        });
    });
    
    // Validação de telefone em tempo real
    const telefoneInputs = document.querySelectorAll('input[name*="telefone"], input[type="tel"]');
    telefoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            const telefone = e.target.value.replace(/\D/g, '');
            
            // Formatar telefone: (00) 00000-0000
            if (telefone.length <= 11) {
                const formatted = telefone.length <= 10 
                    ? telefone.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3')
                    : telefone.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
                e.target.value = formatted;
            }
        });
    });
    
    // Validação de campos obrigatórios
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                    
                    // Adicionar feedback se não existir
                    if (!field.parentNode.querySelector('.invalid-feedback')) {
                        const feedback = document.createElement('div');
                        feedback.className = 'invalid-feedback';
                        feedback.textContent = 'Este campo é obrigatório';
                        field.parentNode.appendChild(feedback);
                    }
                } else {
                    field.classList.remove('is-invalid');
                    field.classList.add('is-valid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showNotification('Por favor, preencha todos os campos obrigatórios', 'error');
            }
        });
    });
}

/**
 * Valida CPF usando algoritmo oficial
 * @param {string} cpf - CPF apenas números
 * @returns {boolean} - true se válido
 */
function validateCPF(cpf) {
    // Remover caracteres especiais
    cpf = cpf.replace(/[^\d]/g, '');
    
    // Verificar se tem 11 dígitos
    if (cpf.length !== 11) return false;
    
    // Verificar se não são todos iguais
    if (/^(\d)\1+$/.test(cpf)) return false;
    
    // Validar dígitos verificadores
    let soma = 0;
    for (let i = 0; i < 9; i++) {
        soma += parseInt(cpf.charAt(i)) * (10 - i);
    }
    let resto = soma % 11;
    let dv1 = resto < 2 ? 0 : 11 - resto;
    
    if (parseInt(cpf.charAt(9)) !== dv1) return false;
    
    soma = 0;
    for (let i = 0; i < 10; i++) {
        soma += parseInt(cpf.charAt(i)) * (11 - i);
    }
    resto = soma % 11;
    let dv2 = resto < 2 ? 0 : 11 - resto;
    
    return parseInt(cpf.charAt(10)) === dv2;
}

/**
 * Auto-refresh para páginas específicas
 */
function initAutoRefresh() {
    const currentPath = window.location.pathname;
    
    // Auto-refresh para fila de espera (a cada 30 segundos)
    if (currentPath.includes('/fila-espera')) {
        setInterval(() => {
            // Só atualiza se não há modais abertos ou campos sendo editados
            if (!document.querySelector('.modal.show') && 
                document.activeElement.tagName !== 'INPUT' &&
                document.activeElement.tagName !== 'TEXTAREA') {
                window.location.reload();
            }
        }, 30000);
    }
    
    // Auto-refresh para lista de agendamentos (a cada 2 minutos)
    if (currentPath.includes('/lista') && currentPath.includes('agendamento')) {
        setInterval(() => {
            if (!document.querySelector('.modal.show')) {
                window.location.reload();
            }
        }, 120000);
    }
}

/**
 * Atalhos de teclado para navegação rápida
 */
function initKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + combinações
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'n': // Ctrl+N - Novo agendamento
                    e.preventDefault();
                    const novoAgendamentoBtn = document.querySelector('a[href*="agendar"]');
                    if (novoAgendamentoBtn) novoAgendamentoBtn.click();
                    break;
                    
                case 'f': // Ctrl+F - Fila de espera
                    e.preventDefault();
                    const filaBtn = document.querySelector('a[href*="fila-espera"]');
                    if (filaBtn) filaBtn.click();
                    break;
                    
                case 'p': // Ctrl+P - Lista de pacientes
                    e.preventDefault();
                    const pacientesBtn = document.querySelector('a[href*="pacientes"]');
                    if (pacientesBtn) pacientesBtn.click();
                    break;
                    
                case 'h': // Ctrl+H - Home
                    e.preventDefault();
                    window.location.href = '/';
                    break;
            }
        }
        
        // Esc - Fechar modais ou voltar
        if (e.key === 'Escape') {
            const modal = document.querySelector('.modal.show');
            if (modal) {
                bootstrap.Modal.getInstance(modal).hide();
            } else {
                const voltarBtn = document.querySelector('a[href*="voltar"], .btn-secondary[onclick*="history"]');
                if (voltarBtn) voltarBtn.click();
            }
        }
    });
}

/**
 * Gerenciamento de dados no localStorage
 */
function initLocalStorage() {
    // Salvar dados do formulário automaticamente
    const forms = document.querySelectorAll('form[id]');
    forms.forEach(form => {
        const formId = form.id;
        
        // Carregar dados salvos
        const savedData = localStorage.getItem(`form_${formId}`);
        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                Object.keys(data).forEach(key => {
                    const field = form.querySelector(`[name="${key}"]`);
                    if (field && field.type !== 'password') {
                        field.value = data[key];
                    }
                });
            } catch (e) {
                console.warn('Erro ao carregar dados do formulário:', e);
            }
        }
        
        // Salvar dados automaticamente
        form.addEventListener('input', debounce(() => {
            const formData = new FormData(form);
            const data = {};
            
            for (let [key, value] of formData.entries()) {
                // Não salvar senhas ou dados sensíveis
                if (!key.includes('password') && !key.includes('senha')) {
                    data[key] = value;
                }
            }
            
            localStorage.setItem(`form_${formId}`, JSON.stringify(data));
        }, 1000));
        
        // Limpar dados ao submeter com sucesso
        form.addEventListener('submit', () => {
            // Aguardar um pouco para confirmar se o submit foi bem-sucedido
            setTimeout(() => {
                if (!document.querySelector('.alert-danger')) {
                    localStorage.removeItem(`form_${formId}`);
                }
            }, 2000);
        });
    });
}

/**
 * Função debounce para limitar chamadas de função
 * @param {Function} func - Função a ser executada
 * @param {number} wait - Tempo de espera em ms
 * @returns {Function} - Função com debounce aplicado
 */
function debounce(func, wait) {
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

/**
 * Exibe notificações toast
 * @param {string} message - Mensagem a exibir
 * @param {string} type - Tipo: success, error, warning, info
 */
function showNotification(message, type = 'info') {
    // Criar elemento de toast se não existir
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'error' ? 'bg-danger' : 
                   type === 'success' ? 'bg-success' :
                   type === 'warning' ? 'bg-warning' : 'bg-info';
    
    const toastHtml = `
        <div id="${toastId}" class="toast ${bgClass} text-white" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header ${bgClass} text-white border-0">
                <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : 
                                   type === 'success' ? 'check-circle' :
                                   type === 'warning' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
                <strong class="me-auto">Sistema Clined Spa</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Remover elemento após ocultar
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

/**
 * Confirma ações importantes
 * @param {string} message - Mensagem de confirmação
 * @param {Function} callback - Função a executar se confirmado
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Formatação de dados para exibição
 */
const formatters = {
    /**
     * Formatar CPF
     * @param {string} cpf - CPF sem formatação
     * @returns {string} - CPF formatado
     */
    cpf: function(cpf) {
        return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    },
    
    /**
     * Formatar telefone
     * @param {string} telefone - Telefone sem formatação
     * @returns {string} - Telefone formatado
     */
    telefone: function(telefone) {
        const numbers = telefone.replace(/\D/g, '');
        return numbers.length === 11 
            ? numbers.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3')
            : numbers.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
    },
    
    /**
     * Formatar data
     * @param {string} date - Data em formato ISO
     * @returns {string} - Data formatada pt-BR
     */
    date: function(date) {
        return new Date(date).toLocaleDateString('pt-BR');
    },
    
    /**
     * Formatar data e hora
     * @param {string} datetime - Data/hora em formato ISO
     * @returns {string} - Data/hora formatada pt-BR
     */
    datetime: function(datetime) {
        return new Date(datetime).toLocaleString('pt-BR');
    }
};

/**
 * Utilitários para trabalhar com datas
 */
const dateUtils = {
    /**
     * Verificar se uma data é hoje
     * @param {string|Date} date - Data a verificar
     * @returns {boolean} - true se for hoje
     */
    isToday: function(date) {
        const today = new Date();
        const checkDate = new Date(date);
        return checkDate.toDateString() === today.toDateString();
    },
    
    /**
     * Calcular idade
     * @param {string|Date} birthDate - Data de nascimento
     * @returns {number} - Idade em anos
     */
    calculateAge: function(birthDate) {
        const today = new Date();
        const birth = new Date(birthDate);
        let age = today.getFullYear() - birth.getFullYear();
        const monthDiff = today.getMonth() - birth.getMonth();
        
        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
            age--;
        }
        
        return age;
    }
};

/**
 * Exportar funcionalidades para uso global
 */
window.clinedSpa = {
    showNotification,
    confirmAction,
    formatters,
    dateUtils,
    validateCPF
};