/**
 * BlueGhost Bluetooth Scanner & Device UI Manager
 */
const BlueGhostBluetooth = (function() {
    let currentDevices = [];
    let selectedDevice = null;
    let onConnectCallback = null;

    function renderDeviceList(containerId, countBadgeId, devices, bleError = null) {
        currentDevices = devices;
        const container = document.getElementById(containerId);
        const countBadge = document.getElementById(countBadgeId);

        if (!container) return;

        if (countBadge) {
            countBadge.innerText = `${devices.length} Found`;
        }

        let warningBannerHtml = '';
        if (bleError && bleError.includes('POWERED_OFF')) {
            warningBannerHtml = `
                <div class="alert alert-warning border border-warning bg-dark text-warning p-2 mb-3 rounded small" style="font-size: 0.75rem;">
                    <i class="fa-solid fa-triangle-exclamation me-1"></i>
                    <strong>Bluetooth Radio is OFF on PC</strong><br>
                    Turn on Bluetooth in Windows Settings to scan real phones. (Simulated nodes active below)
                </div>
            `;
        }

        if (devices.length === 0) {
            container.innerHTML = warningBannerHtml + `
                <div class="text-center text-muted my-5">
                    <i class="fa-solid fa-satellite-dish fa-2x mb-2 text-secondary"></i>
                    <p class="small">No nearby Bluetooth ghosts found.<br>Scanning continues...</p>
                </div>
            `;
            return;
        }

        container.innerHTML = warningBannerHtml;
        devices.forEach(dev => {
            const isSelected = selectedDevice && selectedDevice.address === dev.address;
            const card = document.createElement('div');
            card.className = `device-card ${isSelected ? 'active' : ''}`;
            
            // Normalize signal strength percentage (RSSI -100 to -40)
            const rssiVal = dev.rssi || -70;
            const signalPercent = Math.max(10, Math.min(100, (rssiVal + 100) * 1.66));

            card.innerHTML = `
                <div class="d-flex align-items-center justify-content-between">
                    <div class="d-flex align-items-center gap-3">
                        <div class="device-avatar">${dev.avatar || '👻'}</div>
                        <div>
                            <div class="fw-bold text-white small d-flex align-items-center gap-2">
                                ${dev.ghost_name}
                                <span class="badge bg-secondary bg-opacity-50 text-info font-monospace" style="font-size: 0.65rem;">
                                    ${dev.distance}m
                                </span>
                            </div>
                            <div class="text-muted" style="font-size: 0.75rem;">
                                ${dev.ble_name || 'Bluetooth Device'} • ${dev.rssi} dBm
                            </div>
                            <div class="signal-bar" style="width: 120px;">
                                <div class="signal-fill" style="width: ${signalPercent}%;"></div>
                            </div>
                        </div>
                    </div>
                    <div>
                        <button class="btn ${isSelected ? 'btn-neon-purple' : 'btn-neon-cyan'} btn-sm py-1 px-3 btn-connect" style="font-size: 0.8rem;">
                            ${isSelected ? 'Connected' : 'Connect'}
                        </button>
                    </div>
                </div>
            `;

            card.querySelector('.btn-connect').addEventListener('click', (e) => {
                e.stopPropagation();
                setSelectedDevice(dev);
                if (onConnectCallback) {
                    onConnectCallback(dev);
                }
            });

            container.appendChild(card);
        });
    }

    function setSelectedDevice(dev) {
        selectedDevice = dev;
    }

    function getSelectedDevice() {
        return selectedDevice;
    }

    function setConnectCallback(cb) {
        onConnectCallback = cb;
    }

    return {
        renderDevices: renderDeviceList,
        setSelectedDevice: setSelectedDevice,
        getSelectedDevice: getSelectedDevice,
        onConnect: setConnectCallback
    };
})();
