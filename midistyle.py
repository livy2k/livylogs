import time
import mido

# 1. Define standard guitar tuning MIDI note bases
STRING_BASES = {
    'e': 64,  # High E
    'B': 59,
    'G': 55,
    'D': 50,
    'A': 45,
    'E': 40  # Low E
}

# 2. Raw guitar tab snippet
TAB_DATA = """
e|-------0-3-0---|
B|-----1-------1-|
G|---0-----------|
D|---------------|
A|-3-------------|
E|---------------|
"""


def parse_tab_to_midi_steps(tab_str):
    """Parses text tab into a sequence of MIDI note lists."""
    lines = [line.strip() for line in tab_str.strip().split('\n') if '|' in line]

    parsed_strings = {}
    for line in lines:
        string_letter, frets = line.split('|', 1)
        string_letter = string_letter.strip()
        if string_letter in STRING_BASES:
            parsed_strings[string_letter] = frets

    if not parsed_strings:
        return []

    track_length = min(len(frets) for frets in parsed_strings.values())

    steps = []
    for i in range(track_length):
        notes_at_step = []
        for string_letter, frets in parsed_strings.items():
            char = frets[i]
            if char.isdigit():
                fret = int(char)
                midi_note = STRING_BASES[string_letter] + fret
                notes_at_step.append(midi_note)
        steps.append(notes_at_step)

    return steps


def play_16bit_distorted_tab(steps, tempo_bpm=120):
    """Plays extracted steps using a 16-bit arcade distortion patch."""
    try:
        import mido
    except ImportError:
        print("Mido not found. MIDI playback unavailable.")
        return

    step_duration = 60 / tempo_bpm / 2

    try:
        with mido.open_output() as output:
            DISTORTION_GUITAR_PATCH = 29
            output.send(mido.Message('program_change', program=DISTORTION_GUITAR_PATCH, channel=0))

            print("Playing with 16-bit heavy distortion distortion... Press Ctrl+C to stop.")

            for notes in steps:
                for note in notes:
                    output.send(mido.Message('note_on', note=note, velocity=127, channel=0))

                time.sleep(step_duration)

                for note in notes:
                    output.send(mido.Message('note_off', note=note, velocity=0, channel=0))
    except Exception as e:
        print(f"MIDI Playback Error: {e}")


if __name__ == "__main__":
    midi_timeline = parse_tab_to_midi_steps(TAB_DATA)
    play_16bit_distorted_tab(midi_timeline, tempo_bpm=110)