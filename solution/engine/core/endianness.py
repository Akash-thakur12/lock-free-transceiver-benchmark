"""Byte-Order Serialization & Endianness Conversion Framework."""
import struct

class BigEndianCodec:
    """Strict Network Byte Order (Big-Endian) Serialization Primitives."""
    @staticmethod
    def pack_uint8(val: int) -> bytes:
        return struct.pack(">B", val & 0xFF)

    @staticmethod
    def unpack_uint8(data: bytes, offset: int = 0) -> int:
        return struct.unpack_from(">B", data, offset)[0]

    @staticmethod
    def pack_uint16(val: int) -> bytes:
        return struct.pack(">H", val & 0xFFFF)

    @staticmethod
    def unpack_uint16(data: bytes, offset: int = 0) -> int:
        return struct.unpack_from(">H", data, offset)[0]

    @staticmethod
    def pack_uint32(val: int) -> bytes:
        return struct.pack(">I", val & 0xFFFFFFFF)

    @staticmethod
    def unpack_uint32(data: bytes, offset: int = 0) -> int:
        return struct.unpack_from(">I", data, offset)[0]

    @staticmethod
    def pack_uint64(val: int) -> bytes:
        return struct.pack(">Q", val & 0xFFFFFFFFFFFFFFFF)

    @staticmethod
    def unpack_uint64(data: bytes, offset: int = 0) -> int:
        return struct.unpack_from(">Q", data, offset)[0]
