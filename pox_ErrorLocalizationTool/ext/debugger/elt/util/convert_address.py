import struct

from pox.lib.addresses import EthAddr, IPAddr


def eth_to_int(addr):
    if not isinstance(addr, EthAddr):
        return None
    value = 0
    raw = addr.toRaw()
    for i in range(len(raw)):
        byte_shift = 5 - i
        byte = raw[i]
        byte_value = struct.unpack("B", byte)[0]
        value += (byte_value << (8 * byte_shift))
    return value


def int_to_eth(addr):
    addr = long(addr)
    val = []
    for _ in range(6):
        val.insert(0, struct.pack("B", (addr & 0xFF)))
        addr >>= 8
    return EthAddr(''.join(val))


def ip_to_uint(addr):
    if isinstance(addr, tuple):
        addr = addr[0]
    if not isinstance(addr, IPAddr):
        return None
    return addr.toUnsigned()


def uint_to_ip(addr):
    return IPAddr(addr)
