/**
 * Chart utility functions for CoinEx Trading Bot
 * This file provides reusable chart functionality for different pages
 */

// Global chart configurations and color schemes
const chartColors = {
    primary: 'rgba(75, 192, 192, 1)',
    primaryLight: 'rgba(75, 192, 192, 0.2)',
    secondary: 'rgba(54, 162, 235, 1)',
    secondaryLight: 'rgba(54, 162, 235, 0.2)', 
    danger: 'rgba(255, 99, 132, 1)',
    dangerLight: 'rgba(255, 99, 132, 0.2)',
    warning: 'rgba(255, 159, 64, 1)',
    warningLight: 'rgba(255, 159, 64, 0.2)',
    success: 'rgba(40, 167, 69, 1)',
    successLight: 'rgba(40, 167, 69, 0.2)',
    purple: 'rgba(153, 102, 255, 1)',
    purpleLight: 'rgba(153, 102, 255, 0.2)',
    gray: 'rgba(201, 203, 207, 1)',
    grayLight: 'rgba(201, 203, 207, 0.2)'
};

// Common chart options
const commonChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
        mode: 'index',
        intersect: false,
    },
    plugins: {
        legend: {
            position: 'top',
        },
        tooltip: {
            usePointStyle: true,
            callbacks: {
                label: function(context) {
                    let label = context.dataset.label || '';
                    if (label) {
                        label += ': ';
                    }
                    if (context.parsed.y !== null) {
                        // Format the number to have up to 8 decimal places for crypto prices
                        if (context.parsed.y < 0.01) {
                            label += context.parsed.y.toFixed(8);
                        } else if (context.parsed.y < 1) {
                            label += context.parsed.y.toFixed(6);
                        } else if (context.parsed.y < 1000) {
                            label += context.parsed.y.toFixed(2);
                        } else {
                            label += new Intl.NumberFormat().format(context.parsed.y.toFixed(2));
                        }
                    }
                    return label;
                }
            }
        }
    }
};

/**
 * Create a price chart with optional indicators
 * @param {string} canvasId - The HTML canvas element id
 * @param {Array} priceData - Array of price data points
 * @param {Array} labels - Array of labels for the x-axis
 * @param {Object} indicators - Optional indicators to display (MA, RSI, etc.)
 * @param {Object} options - Additional options for the chart
 * @returns {Chart} The created Chart.js instance
 */
function createPriceChart(canvasId, priceData, labels, indicators = {}, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Create datasets array starting with price data
    const datasets = [{
        label: options.priceLabel || 'قیمت',
        data: priceData,
        borderColor: chartColors.primary,
        backgroundColor: chartColors.primaryLight,
        borderWidth: 2,
        tension: 0.4,
        fill: options.fillPrice === false ? false : true,
        yAxisID: 'y'
    }];
    
    // Add indicators if provided
    if (indicators.sma20 && indicators.sma20.length) {
        datasets.push({
            label: 'SMA 20',
            data: indicators.sma20,
            borderColor: chartColors.success,
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.4,
            fill: false,
            yAxisID: 'y'
        });
    }
    
    if (indicators.sma50 && indicators.sma50.length) {
        datasets.push({
            label: 'SMA 50',
            data: indicators.sma50,
            borderColor: chartColors.secondary,
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.4,
            fill: false,
            yAxisID: 'y'
        });
    }
    
    if (indicators.ema12 && indicators.ema12.length) {
        datasets.push({
            label: 'EMA 12',
            data: indicators.ema12,
            borderColor: chartColors.warning,
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.4,
            fill: false,
            yAxisID: 'y'
        });
    }
    
    if (indicators.ema26 && indicators.ema26.length) {
        datasets.push({
            label: 'EMA 26',
            data: indicators.ema26,
            borderColor: chartColors.danger,
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.4,
            fill: false,
            yAxisID: 'y'
        });
    }
    
    // Create a separate y-axis for RSI if it exists
    let scales = {
        x: {
            title: {
                display: true,
                text: options.xLabel || 'زمان'
            }
        },
        y: {
            position: 'left',
            title: {
                display: true,
                text: options.yLabel || 'قیمت'
            },
            beginAtZero: options.beginAtZero === true ? true : false
        }
    };
    
    // Add RSI on a secondary y-axis if provided
    if (indicators.rsi && indicators.rsi.length) {
        scales.y1 = {
            type: 'linear',
            display: true,
            position: 'right',
            min: 0,
            max: 100,
            title: {
                display: true,
                text: 'RSI'
            },
            grid: {
                drawOnChartArea: false,
            }
        };
        
        datasets.push({
            label: 'RSI',
            data: indicators.rsi,
            borderColor: chartColors.purple,
            backgroundColor: chartColors.purpleLight,
            borderWidth: 2,
            tension: 0.4,
            fill: false,
            yAxisID: 'y1'
        });
        
        // Add overbought/oversold lines
        datasets.push({
            label: 'Overbought (70)',
            data: Array(labels.length).fill(70),
            borderColor: 'rgba(255, 99, 132, 0.5)',
            borderDash: [5, 5],
            borderWidth: 1,
            pointRadius: 0,
            fill: false,
            yAxisID: 'y1'
        });
        
        datasets.push({
            label: 'Oversold (30)',
            data: Array(labels.length).fill(30),
            borderColor: 'rgba(75, 192, 192, 0.5)',
            borderDash: [5, 5],
            borderWidth: 1,
            pointRadius: 0,
            fill: false,
            yAxisID: 'y1'
        });
    }
    
    // Add Bollinger Bands if provided
    if (indicators.bollinger) {
        if (indicators.bollinger.upper && indicators.bollinger.upper.length) {
            datasets.push({
                label: 'BB Upper',
                data: indicators.bollinger.upper,
                borderColor: chartColors.danger,
                borderWidth: 1,
                pointRadius: 0,
                borderDash: options.dashBands ? [5, 5] : [],
                tension: 0.4,
                fill: false,
                yAxisID: 'y'
            });
        }
        
        if (indicators.bollinger.middle && indicators.bollinger.middle.length) {
            datasets.push({
                label: 'BB Middle',
                data: indicators.bollinger.middle,
                borderColor: chartColors.gray,
                borderWidth: 1,
                pointRadius: 0,
                tension: 0.4,
                fill: false,
                yAxisID: 'y'
            });
        }
        
        if (indicators.bollinger.lower && indicators.bollinger.lower.length) {
            datasets.push({
                label: 'BB Lower',
                data: indicators.bollinger.lower,
                borderColor: chartColors.success,
                borderWidth: 1,
                pointRadius: 0,
                borderDash: options.dashBands ? [5, 5] : [],
                tension: 0.4,
                fill: false,
                yAxisID: 'y'
            });
        }
        
        // Fill between upper and lower bands
        if (options.fillBands && indicators.bollinger.upper && indicators.bollinger.lower) {
            datasets.push({
                label: 'BB Range',
                data: indicators.bollinger.upper,
                borderColor: 'transparent',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                fill: '+1',  // Fill to next dataset
                tension: 0.4,
                pointRadius: 0,
                yAxisID: 'y'
            });
        }
    }
    
    // Create the chart with merged options
    const chartOptions = {
        ...commonChartOptions,
        scales: scales
    };
    
    // Override with custom options if provided
    if (options.customOptions) {
        Object.assign(chartOptions, options.customOptions);
    }
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: chartOptions
    });
}

/**
 * Create a MACD chart
 * @param {string} canvasId - The HTML canvas element id
 * @param {Object} macdData - MACD data object with macd, signal, and histogram arrays
 * @param {Array} labels - Array of labels for the x-axis
 * @param {Object} options - Additional options for the chart
 * @returns {Chart} The created Chart.js instance
 */
function createMACDChart(canvasId, macdData, labels, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Create datasets
    const datasets = [];
    
    // Add MACD line
    if (macdData.macd) {
        datasets.push({
            label: 'MACD Line',
            data: macdData.macd,
            borderColor: chartColors.primary,
            backgroundColor: chartColors.primaryLight,
            borderWidth: 2,
            tension: 0.4,
            fill: false,
            type: 'line'
        });
    }
    
    // Add signal line
    if (macdData.signal) {
        datasets.push({
            label: 'Signal Line',
            data: macdData.signal,
            borderColor: chartColors.danger,
            backgroundColor: chartColors.dangerLight,
            borderWidth: 2,
            tension: 0.4,
            fill: false,
            type: 'line'
        });
    }
    
    // Add histogram
    if (macdData.histogram) {
        datasets.push({
            label: 'Histogram',
            data: macdData.histogram,
            backgroundColor: context => {
                const value = context.raw;
                return value >= 0 ? chartColors.successLight : chartColors.dangerLight;
            },
            borderColor: context => {
                const value = context.raw;
                return value >= 0 ? chartColors.success : chartColors.danger;
            },
            borderWidth: 1,
            type: 'bar'
        });
    }
    
    // Create chart options
    const chartOptions = {
        ...commonChartOptions,
        scales: {
            x: {
                title: {
                    display: true,
                    text: options.xLabel || 'زمان'
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'MACD'
                }
            }
        }
    };
    
    // Override with custom options if provided
    if (options.customOptions) {
        Object.assign(chartOptions, options.customOptions);
    }
    
    return new Chart(ctx, {
        type: 'line',  // Default type, some datasets override this
        data: {
            labels: labels,
            datasets: datasets
        },
        options: chartOptions
    });
}

/**
 * Create a multi-type chart for displaying trade history
 * @param {string} canvasId - The HTML canvas element id
 * @param {Object} tradeData - Object with buys and sells arrays
 * @param {Array} labels - Array of labels for the x-axis (dates)
 * @param {Object} options - Additional options for the chart
 * @returns {Chart} The created Chart.js instance
 */
function createTradeHistoryChart(canvasId, tradeData, labels, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    const datasets = [];
    
    // Add buy trades
    if (tradeData.buys) {
        datasets.push({
            label: options.buyLabel || 'خرید',
            data: tradeData.buys,
            backgroundColor: chartColors.successLight,
            borderColor: chartColors.success,
            borderWidth: 1,
            barPercentage: 0.8,
            categoryPercentage: 0.9
        });
    }
    
    // Add sell trades
    if (tradeData.sells) {
        datasets.push({
            label: options.sellLabel || 'فروش',
            data: tradeData.sells,
            backgroundColor: chartColors.dangerLight,
            borderColor: chartColors.danger,
            borderWidth: 1,
            barPercentage: 0.8,
            categoryPercentage: 0.9
        });
    }
    
    // Add profit/loss line if available
    if (tradeData.profit) {
        datasets.push({
            label: 'سود/زیان',
            data: tradeData.profit,
            borderColor: chartColors.purple,
            backgroundColor: chartColors.purpleLight,
            borderWidth: 2,
            tension: 0.4,
            type: 'line',
            fill: false,
            yAxisID: 'y1'
        });
    }
    
    // Create chart options
    const chartOptions = {
        ...commonChartOptions,
        scales: {
            x: {
                stacked: true,
                title: {
                    display: true,
                    text: options.xLabel || 'تاریخ'
                }
            },
            y: {
                stacked: options.stacked !== false,
                title: {
                    display: true,
                    text: options.yLabel || 'تعداد معاملات'
                },
                beginAtZero: true,
                ticks: {
                    precision: 0
                }
            }
        }
    };
    
    // Add second y-axis for profit if profit data is available
    if (tradeData.profit) {
        chartOptions.scales.y1 = {
            type: 'linear',
            display: true,
            position: 'right',
            title: {
                display: true,
                text: 'سود/زیان (%)'
            },
            grid: {
                drawOnChartArea: false,
            }
        };
    }
    
    // Override with custom options if provided
    if (options.customOptions) {
        Object.assign(chartOptions, options.customOptions);
    }
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: chartOptions
    });
}

/**
 * Create a strategy performance comparison chart
 * @param {string} canvasId - The HTML canvas element id
 * @param {Array} strategies - Array of strategy names
 * @param {Array} performanceData - Array of performance values
 * @param {Object} options - Additional options for the chart
 * @returns {Chart} The created Chart.js instance
 */
function createStrategyComparisonChart(canvasId, strategies, performanceData, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Generate a consistent set of colors
    const backgroundColors = [
        chartColors.primaryLight,
        chartColors.secondaryLight,
        chartColors.purpleLight,
        chartColors.warningLight,
        chartColors.successLight,
        chartColors.dangerLight
    ];
    
    const borderColors = [
        chartColors.primary,
        chartColors.secondary,
        chartColors.purple,
        chartColors.warning,
        chartColors.success,
        chartColors.danger
    ];
    
    const chartOptions = {
        ...commonChartOptions,
        scales: {
            y: {
                beginAtZero: options.beginAtZero !== false,
                title: {
                    display: true,
                    text: options.yLabel || 'عملکرد (%)'
                }
            }
        },
        plugins: {
            ...commonChartOptions.plugins,
            tooltip: {
                ...commonChartOptions.plugins.tooltip,
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed.y !== null) {
                            label += context.parsed.y.toFixed(2) + '%';
                        }
                        return label;
                    }
                }
            }
        }
    };
    
    // Override with custom options if provided
    if (options.customOptions) {
        Object.assign(chartOptions, options.customOptions);
    }
    
    return new Chart(ctx, {
        type: options.chartType || 'bar',
        data: {
            labels: strategies,
            datasets: [{
                label: options.datasetLabel || 'عملکرد استراتژی',
                data: performanceData,
                backgroundColor: backgroundColors.slice(0, strategies.length),
                borderColor: borderColors.slice(0, strategies.length),
                borderWidth: 1
            }]
        },
        options: chartOptions
    });
}

/**
 * Format price data for display
 * @param {number} price - The price to format
 * @param {boolean} includeSymbol - Whether to include the currency symbol
 * @param {string} symbol - The currency symbol
 * @returns {string} Formatted price string
 */
function formatPrice(price, includeSymbol = false, symbol = '$') {
    if (price === undefined || price === null) return 'N/A';
    
    let formattedPrice;
    if (price < 0.00001) {
        formattedPrice = price.toFixed(8);
    } else if (price < 0.001) {
        formattedPrice = price.toFixed(6);
    } else if (price < 1) {
        formattedPrice = price.toFixed(4);
    } else if (price < 1000) {
        formattedPrice = price.toFixed(2);
    } else {
        formattedPrice = new Intl.NumberFormat().format(price.toFixed(2));
    }
    
    return includeSymbol ? symbol + formattedPrice : formattedPrice;
}

/**
 * Format percentage value for display
 * @param {number} value - The percentage value to format
 * @param {boolean} includeSymbol - Whether to include the percentage symbol
 * @returns {string} Formatted percentage string
 */
function formatPercentage(value, includeSymbol = true) {
    if (value === undefined || value === null) return 'N/A';
    
    const formattedValue = value.toFixed(2);
    return includeSymbol ? formattedValue + '%' : formattedValue;
}

/**
 * Update chart with new data
 * @param {Chart} chart - The Chart.js instance to update
 * @param {Array} newData - New data points
 * @param {Array} newLabels - New labels
 */
function updateChart(chart, newData, newLabels = null) {
    if (!chart) return;
    
    // Update datasets
    if (Array.isArray(newData)) {
        // Single dataset
        if (chart.data.datasets.length > 0) {
            chart.data.datasets[0].data = newData;
        }
    } else if (typeof newData === 'object') {
        // Multiple datasets
        Object.keys(newData).forEach((key, index) => {
            if (chart.data.datasets[index]) {
                chart.data.datasets[index].data = newData[key];
            }
        });
    }
    
    // Update labels if provided
    if (newLabels) {
        chart.data.labels = newLabels;
    }
    
    chart.update();
}

// Export the functions for use in other scripts
window.chartUtils = {
    createPriceChart,
    createMACDChart,
    createTradeHistoryChart,
    createStrategyComparisonChart,
    formatPrice,
    formatPercentage,
    updateChart,
    colors: chartColors
};
