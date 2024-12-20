from __future__ import annotations

from enum import Enum, auto
from typing import List, Dict, Tuple, Any, Optional, Callable, Union
import ipaddress

import asn1


# SNMP Version
class VersionValue(object):
    def __init__(self, name: str, code: int):
        self.name = name
        self.code = code


class VERSION(object):
    V1 = VersionValue(name='v1', code=0x00)
    V2C = VersionValue(name='v2c', code=0x01)


# ASN.1 TAG
class Tag(object):
    def __init__(self, name, code):
        self.name = name
        self.code = code

    def get_class(self) -> int:
        return self.code & 0xc0

    def get_pc(self) -> int:
        return self.code & 0x20

    def get_tag_number(self) -> int:
        return self.code & 0x1f

    def __str__(self):
        return f"name={self.name} code={self.code}"


class ASN1(object):
    BOOLEAN = Tag(name='BOOLEAN', code=0x01)
    INTEGER = Tag(name='INTEGER', code=0x02)
    OCTET_STRING = Tag(name='OCTET_STRING', code=0x04)
    NULL = Tag(name='NULL', code=0x05)
    OBJECT_IDENTIFIER = Tag(name='OBJECT_IDENTIFIER', code=0x06)
    SEQUENCE = Tag(name='SEQUENCE', code=0x30)
    IPADDRESS = Tag(name='IPADDRESS', code=0x40)
    COUNTER32 = Tag(name='COUNTER32', code=0x41)
    GAUGE32 = Tag(name='GAUGE32', code=0x42)
    TIME_TICKS = Tag(name='TIME_TICKS', code=0x43)
    COUNTER64 = Tag(name='COUNTER64', code=0x46)
    NO_SUCH_OBJECT = Tag(name='NO_SUCH_OBJECT', code=0x80)
    NO_SUCH_INSTANCE = Tag(name='NO_SUCH_INSTANCE', code=0x81)
    END_OF_MIB_VIEW = Tag(name='END_OF_MIB_VIEW', code=0x82)

    GET_REQUEST = Tag(name='GET_REQUEST', code=0xA0)
    GET_NEXT_REQUEST = Tag(name='GET_NEXT_REQUEST', code=0xA1)
    GET_RESPONSE = Tag(name='GET_RESPONSE', code=0xA2)
    SET_REQUEST = Tag(name='SET_REQUEST', code=0xA3)
    GET_BULK_REQUEST = Tag(name='GET_BULK_REQUEST', code=0xA5)

    _bind_tuple = {
        (0, 0, 64): IPADDRESS
    }

    @classmethod
    def get_tag(cls, tupl: Tuple[int, int, int]) -> Tag:
        if t := cls._bind_tuple.get(tupl, None):
            print(f"RETORNANDO UM TIPO NAO NULLO IP ADDRESS {t.name}")

            return t
        return cls.NULL


class SNMPValue(object):
    def __init__(self):
        self.tag: Tag = None

    def get_class(self) -> int:
        return self.tag.get_class()

    def get_pc(self) -> int:
        return self.tag.get_pc()

    def get_tag_number(self) -> int:
        return self.tag.get_tag_number()


class SNMPLeafValue(SNMPValue):
    def __init__(self, tag=None, value=None, tag_tuple=None):
        super().__init__()
        self.value: Any = value
        self.tag: Tag = tag
        self.tag_tuple = tag_tuple

    def encode(self) -> bytes:
        raise NotImplementedError


class Integer(SNMPLeafValue):
    def __init__(self, value: int):
        self.value = value
        self.tag = ASN1.INTEGER

    def encode(self) -> bytes:
        if isinstance(self.value, bool):
            self.value = 1 if self.value is True else 0
        return asn1.Encoder._encode_integer(self.value)


class Boolean(SNMPLeafValue):
    def __init__(self, value: bool):
        self.value = value
        self.tag = ASN1.INTEGER

    def encode(self) -> bytes:
        return asn1.Encoder._encode_boolean(self.value)


class OctetString(SNMPLeafValue):
    def __init__(self, value: str):
        self.value = value
        self.tag = ASN1.OCTET_STRING

    def encode(self) -> bytes:
        return asn1.Encoder._encode_octet_string(self.value)


class Null(SNMPLeafValue):
    def __init__(self):
        super().__init__()
        self.value = None
        self.tag = ASN1.NULL

    def encode(self) -> bytes:
        return asn1.Encoder._encode_null()


class ObjectIdentifier(SNMPLeafValue):
    def __init__(self, value: str):
        self.value = value
        self.tag = ASN1.OBJECT_IDENTIFIER

    def encode(self) -> bytes:
        return asn1.Encoder()._encode_object_identifier(self.value)


class IPAddress(SNMPLeafValue):
    def __init__(self, value: str):
        self.value = value
        self.tag = ASN1.IPADDRESS

    def encode(self) -> bytes:
        return ipaddress.IPv4Address(self.value).packed


class Counter32(SNMPLeafValue):
    def __init__(self, value: int):
        self.value = value
        self.tag = ASN1.COUNTER32

    def encode(self) -> bytes:
        return asn1.Encoder._encode_integer(self.value)


class Gauge32(SNMPLeafValue):
    def __init__(self, value: int):
        self.value = value
        self.tag = ASN1.GAUGE32

    def encode(self) -> bytes:
        return asn1.Encoder._encode_integer(self.value)


class TimeTicks(SNMPLeafValue):
    def __init__(self, value: int):
        self.value = value
        self.tag = ASN1.TIME_TICKS

    def encode(self) -> bytes:
        return asn1.Encoder._encode_integer(self.value)


class Counter64(SNMPLeafValue):
    def __init__(self, value: int):
        self.value = value
        self.tag = ASN1.COUNTER64

    def encode(self) -> bytes:
        return asn1.Encoder._encode_integer(self.value)


class NoSuchObject(SNMPLeafValue):
    def __init__(self):
        self.value = None
        self.tag = ASN1.NO_SUCH_OBJECT

    def encode(self) -> bytes:
        return b''


class NoSuchInstance(SNMPLeafValue):
    def __init__(self):
        self.value = None
        self.tag = ASN1.NO_SUCH_INSTANCE

    def encode(self) -> bytes:
        return b''


class EndOfMibView(SNMPLeafValue):
    def __init__(self):
        self.value = None
        self.tag = ASN1.END_OF_MIB_VIEW

    def encode(self) -> bytes:
        return b''


class SNMPConstructedValue(SNMPValue):
    pass


class Sequence(SNMPConstructedValue):
    def __init__(self):
        self.tag = ASN1.SEQUENCE


class SnmpContext(SNMPConstructedValue):
    pass


class SnmpSetRequestContext(SnmpContext):
    def __init__(self):
        self.tag = ASN1.SET_REQUEST


class SnmpGetContext(SnmpContext):
    def __init__(self):
        self.tag = ASN1.GET_REQUEST


class SnmpGetNextContext(SnmpContext):
    def __init__(self):
        self.tag = ASN1.GET_NEXT_REQUEST


class SnmpGetBulkContext(SnmpContext):
    def __init__(self):
        self.tag = ASN1.GET_BULK_REQUEST


class SnmpGetResponseContext(SnmpContext):
    def __init__(self):
        self.tag = ASN1.GET_RESPONSE


class Encoder(object):
    def __init__(self):
        self._encoder = asn1.Encoder()
        self._encoder.start()

    def enter(self, value: SNMPConstructedValue):
        self._encoder.enter(cls=value.get_class(), nr=value.get_tag_number())

    def leave(self):
        self._encoder.leave()

    def write(self, value: SNMPLeafValue):
        self._encoder._emit_tag(cls=value.get_class(),
                                typ=value.get_pc(),
                                nr=value.get_tag_number())
        value_bytes = value.encode()
        self._encoder._emit_length(len(value_bytes))
        self._encoder._emit(value_bytes)

    def output(self) -> bytes:
        return self._encoder.output()


def encode_response(response: SNMPResponse) -> bytes:
    encoder = Encoder()

    encoder.enter(Sequence())
    encoder.write(Integer(response.version.code))
    encoder.write(OctetString(response.community))

    encoder.enter(response.context)
    encoder.write(Integer(response.request_id))
    encoder.write(Integer(response.error_status))
    encoder.write(Integer(response.error_index))

    encoder.enter(Sequence())
    for variable_binding in response.variable_bindings:
        encoder.enter(Sequence())
        encoder.write(ObjectIdentifier(variable_binding.oid))
        encoder.write(variable_binding.value)
        encoder.leave()
    encoder.leave()
    encoder.leave()
    encoder.leave()

    return encoder.output()


class Decoder(object):
    def __init__(self, data: bytes):
        self._decoder = asn1.Decoder()
        self._decoder.start(data=data)

    def enter(self):
        self._decoder.enter()

    def read(self) -> Tuple[Any, Any]:
        # TODO: Look into response type warning
        return self._decoder.read()  # (asn1.Tag, value)

    def peek(self) -> asn1.Tag:
        return self._decoder.peek()

    def eof(self) -> bool:
        return self._decoder.eof()

    def leave(self):
        self._decoder.leave()


def decode_request(data: bytes) -> SNMPRequest:
    decoder = Decoder(data=data)

    # Get version and community
    decoder.enter()
    _, _value = decoder.read()
    version_code: int = _value
    if VERSION.V1.code == version_code:
        version = VERSION.V1
    elif VERSION.V2C.code == version_code:
        version = VERSION.V2C
    else:
        raise NotImplementedError(f"SNMP Version code '{version_code}' is not implemented")

    _, _value = decoder.read()
    community = _value.decode()

    # Get pdu_type, request_id, non_repeaters and max_repetitions
    _tag = decoder.peek()
    _pdu_type_code = _tag.cls | _tag.typ | _tag.nr
    if ASN1.GET_REQUEST.code == _pdu_type_code:
        context = SnmpGetContext()
    elif ASN1.GET_NEXT_REQUEST.code == _pdu_type_code:
        context = SnmpGetNextContext()
    elif ASN1.GET_BULK_REQUEST.code == _pdu_type_code:
        context = SnmpGetBulkContext()
    elif ASN1.SET_REQUEST.code == _pdu_type_code:
        context = SnmpSetRequestContext()
    else:
        raise NotImplementedError(f"PDU-TYPE code '{_pdu_type_code}' is not implemented")

    decoder.enter()
    _, _value = decoder.read()
    request_id: int = _value

    non_repeaters: int
    max_repetitions: int
    if isinstance(context, SnmpGetBulkContext):
        _, _value = decoder.read()
        non_repeaters = _value
        _, _value = decoder.read()
        max_repetitions = _value
    else:
        _, _ = decoder.read()
        _, _ = decoder.read()
        non_repeaters = 0
        max_repetitions = 0

    # Get variable-bindings
    decoder.enter()
    variable_bindings = []
    while not decoder.eof():
        # Get oid, type and value
        decoder.enter()
        _, _value = decoder.read()
        oid: str = _value
        tag, value = decoder.read()
        # variable_bindings.append(VariableBinding(oid=oid, value=Null()))
        print(tag)
        variable_bindings.append(VariableBinding(oid=oid, value=SNMPLeafValue(ASN1.get_tag(tag), value, tag_tuple=tag)))
        decoder.leave()
    decoder.leave()
    decoder.leave()
    decoder.leave()

    return SNMPRequest(
        version=version,
        community=community,
        context=context,
        request_id=request_id,
        non_repeaters=non_repeaters,
        max_repetitions=max_repetitions,
        variable_bindings=variable_bindings)


class SNMP(object):
    def __init__(self):
        pass

    def to_dict(self):
        dict_ = self._to_primitive(self)
        return dict_

    def _to_primitive(self, value):
        if isinstance(value, dict):
            _dict = {}
            for k, v in value.items():
                _dict[k] = self._to_primitive(v)
            return _dict
        elif isinstance(value, list):
            items = []
            for item in value:
                items.append(self._to_primitive(item))
            return items
        elif isinstance(value, (int, str, bool, bytes)) or value is None:
            return value
        else:
            _dict = {}
            for k, v in vars(value).items():
                _dict[k] = self._to_primitive(v)
            return _dict


class SNMPRequest(SNMP):
    def __init__(self, version: VersionValue, community: str, context: SnmpContext,
                 request_id: int, variable_bindings: List[VariableBinding],
                 non_repeaters: int = 0,
                 max_repetitions: int = 0):
        self.version = version
        self.community = community
        self.context = context
        self.request_id = request_id
        self.non_repeaters = non_repeaters
        self.max_repetitions = max_repetitions
        self.variable_bindings = variable_bindings

    def create_response(self,
                        variable_bindings: List[VariableBinding],
                        error_status: int = 0, error_index: int = 0):
        # if isinstance(self.context, SnmpSetRequestContext) and error_status == 0:
        #    return None
        return SNMPResponse(
            version=self.version, community=self.community,
            request_id=self.request_id,
            variable_bindings=variable_bindings,
            error_status=error_status, error_index=error_index)


class SNMPResponse(SNMP):
    def __init__(self, version: VersionValue, community: str, request_id: int,
                 variable_bindings: List[VariableBinding],
                 error_status: int = 0, error_index: int = 0):
        self.version = version
        self.community = community
        self.context = SnmpGetResponseContext()
        self.request_id = request_id
        self.error_status = error_status
        self.error_index = error_index
        self.variable_bindings = variable_bindings


class VariableBinding(SNMP):
    def __init__(self, oid: str, value: SNMPLeafValue):
        super().__init__()
        self.oid = oid.lstrip(".")
        self.value = value

    def encode(self):
        return self.value.encode()


class VariableBind:
    class Access(Enum):
        READ_WRITE = auto()
        READ_ONLY = auto()
        WRITE_ONLY = auto()

    def __init__(self, oid: str, read: Callable[[VariableBinding], Tuple[int, SNMPLeafValue]] | SNMPLeafValue = None,
                 write: Callable[[VariableBinding], Any] = None, use_start_with=False, get_next: Union[Callable, str, None] = None):
        self.oid = oid
        self._read = read
        self._write = write
        self.use_start_with = use_start_with
        self.get_next = get_next

        if read and write:
            self.access = self.Access.READ_WRITE
        elif read:
            self.access = self.Access.READ_ONLY
        else:
            self.access = self.Access.WRITE_ONLY

    def write(self, vb: VariableBinding)-> Tuple[int, SNMPLeafValue|None]:
        return self._write(vb)

    def read(self, vb: VariableBinding)-> Tuple[int, SNMPLeafValue|None]:
        if isinstance(self._read, SNMPLeafValue):
            return 0, self._read
        else:
            return self._read(vb)
