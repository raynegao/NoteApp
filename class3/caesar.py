alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encrypt(text, key):
    result = ""
    for letter in text:
        if letter in alphabet:
            position = alphabet.index(letter)
            result += alphabet[(position + key) % 26]
        else:
            result += letter
    return result


def decrypt(text, key):
    return encrypt(text, -key)


def crack(text):
    counts = [0] * 26
    for letter in text:
        if letter in alphabet:
            position = alphabet.index(letter)
            counts[position] += 1
    if sum(counts) == 0:
        raise ValueError("Capital letters are required")
    most_common = counts.index(max(counts))
    guessed_key = (most_common - alphabet.index("E")) % 26
    return guessed_key


if __name__ == "__main__":
    message = "THE SECRET MESSAGE IS HERE. WE NEED TO KEEP THE MESSAGE SAFE."
    key = 7

    encrypted = encrypt(message, key)
    guessed_key = crack(encrypted)

    print("Original:", message)
    print("Encrypted:", encrypted)
    print("Guessed key:", guessed_key)
    print("Decrypted:", decrypt(encrypted, guessed_key))
