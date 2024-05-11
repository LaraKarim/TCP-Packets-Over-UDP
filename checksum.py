def detect(message, checksum):
    message_bits = message.encode('utf-8')
    actual_checksum = sum(message_bits)
    print(actual_checksum)

    if actual_checksum == checksum:
        return False
    else:
        return True


# message = "Hello, World!"
# checksum = 1129
# error_detected = detect(message, checksum)
# print(error_detected)
