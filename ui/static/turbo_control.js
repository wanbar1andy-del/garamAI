// ===== TURBO CONTROL FUNCTIONALITY =====
document.addEventListener('DOMContentLoaded', function () {
    const turboToggle = document.getElementById('turbo-mode-toggle');
    const turboSlider = document.getElementById('turbo-slider');
    const turboApplyBtn = document.getElementById('turbo-apply-btn');
    const turboManualSection = document.getElementById('turbo-manual-section');
    const turboAutoSection = document.getElementById('turbo-auto-section');
    const turboValueDisplay = document.getElementById('turbo-value-display');
    const turboCurrentMode = document.getElementById('turbo-current-mode');
    const turboCurrentValue = document.getElementById('turbo-current-value');

    if (!turboToggle) return; // Exit if turbo controls not found

    // Load current settings
    async function loadTurboSettings() {
        try {
            const resp = await fetch('/api/turbo/get');
            const data = await resp.json();

            const isAuto = data.mode === 'auto' || data.auto_enabled;
            turboToggle.checked = isAuto;
            turboSlider.value = data.manual_value * 100;
            turboValueDisplay.textContent = `${Math.round(data.manual_value * 100)}%`;

            turboManualSection.style.display = isAuto ? 'none' : 'block';
            turboAutoSection.style.display = isAuto ? 'block' : 'none';

            turboCurrentMode.textContent = isAuto ? '자동' : '수동';
            turboCurrentValue.textContent = `${Math.round((data.current_multiplier || data.manual_value) * 100)}%`;

        } catch (error) {
            console.error('Failed to load turbo settings:', error);
        }
    }

    // Toggle mode
    turboToggle.addEventListener('change', function () {
        const isAuto = this.checked;
        turboManualSection.style.display = isAuto ? 'none' : 'block';
        turboAutoSection.style.display = isAuto ? 'block' : 'none';
    });

    // Slider update
    turboSlider.addEventListener('input', function () {
        turboValueDisplay.textContent = `${this.value}%`;
    });

    // Apply settings
    turboApplyBtn.addEventListener('click', async function () {
        const isAuto = turboToggle.checked;
        const manualValue = parseInt(turboSlider.value) / 100;

        try {
            const resp = await fetch('/api/turbo/set', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mode: isAuto ? 'auto' : 'manual',
                    manual_value: manualValue,
                    auto_enabled: isAuto
                })
            });

            const result = await resp.json();

            if (result.success) {
                alert('✅ 터보 설정이 적용되었습니다!');
                loadTurboSettings();
            } else {
                alert('❌ 설정 실패: ' + (result.error || '알 수 없는 오류'));
            }
        } catch (error) {
            console.error('Failed to apply turbo settings:', error);
            alert('❌ 네트워크 오류가 발생했습니다.');
        }
    });

    // Initial load
    loadTurboSettings();

    // Refresh every 5 seconds
    setInterval(loadTurboSettings, 5000);
});
