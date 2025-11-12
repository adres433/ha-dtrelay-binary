# errors.py - central place for error codes/messages

ERRORS = {
    1250: "Unable to create UDP/TCP socket.",
    1255: "Network unreachable – invalid IP or port.",
    1258: "Device did not respond in time (1 s).",
    1260: "Invalid response from device.",
    1261: "Serial number must be 5 digits (0–9).",
    1265: "Unknown communication error."
}

def get_error_message(code: int) -> str:
    return ERRORS.get(code, f"Unrecognized error {code}")
