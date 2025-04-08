// Function to handle strategy type selection
function updateStrategyParameters(strategyId, availableStrategies) {
    const parametersContainer = document.getElementById('strategy_parameters');
    parametersContainer.innerHTML = '';
    
    if (!strategyId) return;
    
    const strategy = availableStrategies.find(s => s.id === strategyId);
    if (!strategy) return;
    
    // Create input fields for each parameter
    for (const [paramName, paramInfo] of Object.entries(strategy.parameters)) {
        const inputId = `param_${paramName}`;
        
        let inputHtml = `
            <div class="mb-3">
                <label for="${inputId}" class="form-label">${paramInfo.description}</label>
        `;
        
        if (paramInfo.type === 'bool') {
            inputHtml += `
                <div class="form-check">
                    <input type="checkbox" class="form-check-input" id="${inputId}" name="${paramName}" ${paramInfo.default ? 'checked' : ''}>
                    <label class="form-check-label" for="${inputId}">فعال</label>
                </div>
            `;
        } else {
            const min = paramInfo.min !== undefined ? `min="${paramInfo.min}"` : '';
            const max = paramInfo.max !== undefined ? `max="${paramInfo.max}"` : '';
            const step = paramInfo.type === 'float' ? 'step="0.1"' : '';
            
            inputHtml += `
                <input type="${paramInfo.type === 'int' || paramInfo.type === 'float' ? 'number' : 'text'}" 
                       class="form-control" 
                       id="${inputId}" 
                       name="${paramName}" 
                       value="${paramInfo.default}" 
                       ${min} ${max} ${step}
                       required>
            `;
        }
        
        inputHtml += `</div>`;
        parametersContainer.innerHTML += inputHtml;
    }
}

// Function to toggle strategy active status
function toggleStrategy(id, checkbox) {
    fetch(`/strategy/${id}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            // Reset checkbox to previous state
            checkbox.checked = !checkbox.checked;
            alert('خطا در تغییر وضعیت استراتژی');
        }
    })
    .catch(error => {
        // Reset checkbox to previous state
        checkbox.checked = !checkbox.checked;
        alert('خطا در تغییر وضعیت استراتژی');
        console.error('Error:', error);
    });
}

// Function to delete a strategy with confirmation
function deleteStrategy(id, name) {
    if (confirm(`آیا از حذف استراتژی "${name}" اطمینان دارید؟`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/strategy/${id}/delete`;
        document.body.appendChild(form);
        form.submit();
    }
}

// Function to view strategy analysis
function viewStrategyAnalysis(id) {
    // Show loading state
    document.getElementById('strategy-analysis').style.display = 'block';
    document.getElementById('strategy-name').textContent = 'در حال بارگذاری...';
    document.getElementById('current-signal').textContent = 'در حال تحلیل...';
    document.getElementById('current-signal').className = 'badge bg-secondary fs-5';
    document.getElementById('strategy-parameters').innerHTML = '';
    
    // Fetch strategy analysis
    fetch(`/api/analyze_strategy/${id}?timeframe=1h&limit=100`)
        .then(response => response.json())
        .then(response => {
            if (response.success) {
                const data = response.data;
                
                // Update strategy name
                document.getElementById('strategy-name').textContent = data.strategy_name + ' (' + data.trading_pair + ')';
                
                // Update signal
                const signalEl = document.getElementById('current-signal');
                signalEl.textContent = data.signal;
                
                if (data.signal === 'BUY') {
                    signalEl.className = 'badge bg-success fs-5';
                } else if (data.signal === 'SELL') {
                    signalEl.className = 'badge bg-danger fs-5';
                } else {
                    signalEl.className = 'badge bg-secondary fs-5';
                }
                
                // Update parameters
                const paramsEl = document.getElementById('strategy-parameters');
                paramsEl.innerHTML = '';
                
                for (const [key, value] of Object.entries(data)) {
                    // Filter out non-parameter fields and arrays
                    if (!['signal', 'strategy_name', 'trading_pair', 'timeframe', 'error'].includes(key) && 
                        !Array.isArray(value) && typeof value !== 'object') {
                        const paramDiv = document.createElement('div');
                        paramDiv.className = 'mb-1';
                        paramDiv.innerHTML = `<strong>${key}:</strong> ${value}`;
                        paramsEl.appendChild(paramDiv);
                    }
                }
                
                // Update chart
                updateStrategyChart(data);
                
            } else {
                document.getElementById('strategy-name').textContent = 'خطا در تحلیل';
                document.getElementById('current-signal').textContent = 'خطا';
                document.getElementById('current-signal').className = 'badge bg-danger fs-5';
                alert('خطا در تحلیل استراتژی: ' + response.error);
            }
        })
        .catch(error => {
            document.getElementById('strategy-name').textContent = 'خطا در تحلیل';
            document.getElementById('current-signal').textContent = 'خطا';
            document.getElementById('current-signal').className = 'badge bg-danger fs-5';
            alert('خطا در تحلیل استراتژی');
            console.error('Error:', error);
        });
}

// Initialize event listeners when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Strategy type selection
    const strategyTypeSelect = document.getElementById('strategy_type');
    if (strategyTypeSelect) {
        strategyTypeSelect.addEventListener('change', function() {
            // This function will be implemented in the template with availableStrategies data
            // from server, so we're not implementing it here
        });
    }
    
    // Toggle strategy active status
    const strategyToggles = document.querySelectorAll('.strategy-toggle');
    strategyToggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            toggleStrategy(this.dataset.id, this);
        });
    });
    
    // Delete strategy buttons
    const deleteButtons = document.querySelectorAll('.delete-strategy');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            deleteStrategy(this.dataset.id, this.dataset.name);
        });
    });
    
    // View strategy analysis
    const viewButtons = document.querySelectorAll('.view-strategy');
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            viewStrategyAnalysis(this.dataset.id);
        });
    });
    
    // Close analysis panel
    const closeButton = document.getElementById('close-analysis');
    if (closeButton) {
        closeButton.addEventListener('click', function() {
            document.getElementById('strategy-analysis').style.display = 'none';
            if (window.strategyChart) {
                window.strategyChart.destroy();
            }
        });
    }
});
