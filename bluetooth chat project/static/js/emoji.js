/**
 * BlueGhost Emoji Picker Module
 */
const BlueGhostEmoji = (function() {
    const EMOJIS = [
        "👻", "🌑", "🐧", "🦊", "👾", "🌀", "💀", "👁️", "⚡", "🛰️", "🤖", "🎭",
        "🔥", "✨", "💥", "🌌", "🌙", "⚔️", "🛡️", "🔮", "🧿", "📡", "🛸", "💬",
        "😀", "😎", "😏", "😈", "🧐", "🤔", "🤫", "🥳", "🎃", "👽", "🤖", "🙈"
    ];

    function initEmojiPicker(pickerElementId, inputElementId) {
        const pickerEl = document.getElementById(pickerElementId);
        const inputEl = document.getElementById(inputElementId);

        if (!pickerEl || !inputEl) return;

        pickerEl.innerHTML = '';
        EMOJIS.forEach(emoji => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'emoji-btn';
            btn.innerText = emoji;
            btn.addEventListener('click', () => {
                inputEl.value += emoji;
                inputEl.focus();
                pickerEl.classList.add('d-none');
            });
            pickerEl.appendChild(btn);
        });
    }

    function togglePicker(pickerElementId) {
        const pickerEl = document.getElementById(pickerElementId);
        if (pickerEl) {
            pickerEl.classList.toggle('d-none');
        }
    }

    return {
        init: initEmojiPicker,
        toggle: togglePicker
    };
})();
