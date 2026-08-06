/**
 * BlueGhost Audio Manager - Handles UI Sound Effects
 */
const BlueGhostAudio = (function() {
    let soundEnabled = true;
    const sounds = {
        connected: new Audio('/static/sounds/connected.wav'),
        disconnected: new Audio('/static/sounds/disconnected.wav'),
        message_received: new Audio('/static/sounds/message_received.wav'),
        message_sent: new Audio('/static/sounds/message_sent.wav'),
        ghost_vanished: new Audio('/static/sounds/ghost_vanished.wav')
    };

    // Preload audio files
    Object.values(sounds).forEach(audio => {
        audio.preload = 'auto';
    });

    function play(soundKey) {
        if (!soundEnabled) return;
        const audio = sounds[soundKey];
        if (audio) {
            audio.currentTime = 0;
            audio.play().catch(e => {
                // Ignore autoplay policies
            });
        }
    }

    function toggleSound() {
        soundEnabled = !soundEnabled;
        return soundEnabled;
    }

    function isEnabled() {
        return soundEnabled;
    }

    return {
        play: play,
        toggleSound: toggleSound,
        isEnabled: isEnabled
    };
})();
