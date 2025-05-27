
def SevenSegmentDecode(segments):
    if segments.value == 0b0000000: return 0
    if segments.value == 0b0111111: return 0
    if segments.value == 0b0000110: return 1
    if segments.value == 0b1011011: return 2
    if segments.value == 0b1001111: return 3
    if segments.value == 0b1100110: return 4
    if segments.value == 0b1101101: return 5
    if segments.value == 0b1111101: return 6
    if segments.value == 0b0000111: return 7
    if segments.value == 0b1111111: return 8
    if segments.value == 0b1101111: return 9
    return -1

