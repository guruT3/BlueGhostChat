import os
import wave
import math
import struct

SOUNDS_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_RATE = 44100

def generate_tone(filename, duration, start_freq, end_freq, volume=0.5, type_='sine'):
    filepath = os.path.join(SOUNDS_DIR, filename)
    num_samples = int(SAMPLE_RATE * duration)
    with wave.open(filepath, 'w') as wav_file:
        wav_file.setnchannels(1) # mono
        wav_file.setsampwidth(2) # 16-bit
        wav_file.setframerate(SAMPLE_RATE)

        for i in range(num_samples):
            t = i / SAMPLE_RATE
            progress = t / duration
            freq = start_freq + (end_freq - start_freq) * progress
            
            # Envelope (fade in / out)
            fade = min(i / (SAMPLE_RATE * 0.02), 1.0) * min((num_samples - i) / (SAMPLE_RATE * 0.05), 1.0)

            if type_ == 'sine':
                sample = math.sin(2 * math.pi * freq * t)
            elif type_ == 'spooky':
                sample = math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(2 * math.pi * (freq * 0.5) * t)
            else:
                sample = math.sin(2 * math.pi * freq * t)

            val = int(sample * volume * fade * 32767)
            wav_file.writeframes(struct.pack('<h', max(-32768, min(32767, val))))

if __name__ == '__main__':
    generate_tone('connected.wav', 0.4, 440, 880, 0.4, 'sine')
    generate_tone('disconnected.wav', 0.5, 600, 250, 0.4, 'sine')
    generate_tone('message_received.wav', 0.25, 523, 784, 0.4, 'sine')
    generate_tone('message_sent.wav', 0.15, 600, 1000, 0.3, 'sine')
    generate_tone('ghost_vanished.wav', 0.7, 450, 120, 0.4, 'spooky')
    print("All sound files generated successfully in static/sounds/!")
