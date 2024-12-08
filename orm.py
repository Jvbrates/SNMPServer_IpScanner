# Generated by ChatGPT, version October 2024, on 2024-10-17
import functools
from datetime import datetime
from enum import Enum
from typing import List, Sequence, Any, Dict, Union

import tabulate
from sqlalchemy import create_engine, Integer, String, Boolean, DateTime, ForeignKey, delete
from sqlalchemy import select
from sqlalchemy.orm import declarative_base, mapped_column, Mapped, relationship, Session, joinedload

from vendor_solver import vendor_solver


class EnumMethods(Enum):
    ICMP_ECHO_RESPONSE = 3
    ARP_2 = 2
    ICMP_ECHO_RESPONSE_TIMEOUT = 1


# Define o modelo base
Base = declarative_base()


# Define a tabela Device como um modelo
class Device(Base):
    __tablename__ = 'devices'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mac_addr: Mapped[str] = mapped_column(String, nullable=False)
    gateway: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Relação com DeviceNetwork (um Device pode ter várias entradas em DeviceNetwork)
    networks = relationship("DeviceNetwork", back_populates="device", foreign_keys="DeviceNetwork.device_id")

    def __repr__(self):
        return f"<Device(id={self.id}, mac_addr='{self.mac_addr}', gateway={self.gateway})>"


# Define a tabela DiscoveryMethod como um modelo
class DiscoveryMethod(Base):
    __tablename__ = 'discovery_method'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    method: Mapped[str] = mapped_column(String, nullable=False)
    descr: Mapped[str] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Relação com DeviceNetwork
    networks = relationship("DeviceNetwork", back_populates="discovery_method", lazy='joined',
                            foreign_keys="DeviceNetwork.discovery_method_id")

    def __repr__(self):
        return f"<DiscoveryMethod(id={self.id}, method='{self.method}')>"


# Define a tabela DeviceNetwork como um modelo
class DeviceNetwork(Base):
    __tablename__ = 'device_networks'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Chave estrangeira para a tabela Device (dispositivo)
    device_id: Mapped[int] = mapped_column(ForeignKey('devices.id'), nullable=False)
    device = relationship("Device", back_populates="networks", foreign_keys=[device_id])

    # Chave estrangeira para o método de descoberta
    discovery_method_id: Mapped[int] = mapped_column(ForeignKey('discovery_method.id'))
    discovery_method = relationship("DiscoveryMethod", back_populates="networks", lazy='joined',
                                    foreign_keys=[discovery_method_id])

    ip: Mapped[str] = mapped_column(String, nullable=False)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __init__(self):
        self.discovered_at = datetime.now()  # Atribui a hora atual

    def __repr__(self):
        return f"<DeviceNetwork(id={self.id}, ip='{self.ip}')>"

    def __str__(self):
        return (f"mac: {self.device.mac_addr} | vendor: {vendor_solver(self.device.mac_addr[0:9])} | "
                f"ip: {self.ip} | dicovered: {self.discovered_at} "
                f" | method: {self.discovery_method.method} ({'up' if self.discovery_method.active else 'down'} )"
                )


# Cria a engine SQLite
engine = create_engine('sqlite:///network_discovery.db')
Base.metadata.create_all(engine)


def get_related_mac(ip: str, session) -> Union[Any, None]:
    smnt = select(DeviceNetwork).where(DeviceNetwork.ip == ip).order_by(DeviceNetwork.discovered_at)
    devnet: DeviceNetwork = session.execute(smnt).scalar()

    if devnet is not None:
        return devnet.device.mac_addr
    else:
        return None


def get_or_create_device(mac: str, session: Session, gateway) -> Device:
    smnt = select(Device).where(Device.mac_addr == mac)
    device: Device = session.scalar(smnt)

    if device is None:
        device: Device = Device()
        device.mac_addr = mac
        device.gateway = gateway
        session.add(device)
        session.flush()
        return device
    else:
        if device.gateway != gateway:
            device.gateway = gateway
            session.add(device)
            session.flush()
        return device


def save(ip: str, method: EnumMethods, mac: Union[str, None] = None, gateway: Any = False):
    with engine.connect() as connection:
        with Session(bind=connection) as session:

            if method == EnumMethods.ICMP_ECHO_RESPONSE_TIMEOUT:
                mac = get_related_mac(ip, session)
                if mac is None:
                    return

            device = get_or_create_device(mac, session=session, gateway=gateway)
            devnet = DeviceNetwork()
            devnet.device = device
            devnet.discovery_method_id = method.value
            session.add(devnet)
            devnet.ip = ip

            session.commit()


def partition(devnetlist: Sequence[DeviceNetwork]) -> Dict[str, List[DeviceNetwork]]:
    output: Dict[str, List[DeviceNetwork]] = {}
    for devnet in devnetlist:
        if devnet.device.mac_addr in output:
            output[devnet.device.mac_addr].append(devnet)
        else:
            output[devnet.device.mac_addr] = [devnet]

    return output


def format_output_device_network(devlist: List[DeviceNetwork]) -> List:
    if not devlist[0].discovery_method.active:
        status = "OFFLINE"
    elif len(devlist) == 1:
        status = "ONLINE(NEW)"
    elif devlist[1].discovery_method.active:
        status = "ONLINE"
    else:
        status = "RECONNECTED"

    first_conn = devlist[-1].discovered_at

    return [status, devlist[0].device.mac_addr, vendor_solver(devlist[0].device.mac_addr[0:8]), devlist[0].ip,
            devlist[0].device.gateway, str(first_conn)]


def drop_devices():
    with engine.connect() as connection:
        with Session(bind=connection) as session:
            session.execute(delete(Device))
            session.execute(delete(DeviceNetwork))
            session.commit()


def drop_history():
    with engine.connect() as connection:
        with Session(bind=connection) as session:
            DeviceNetwork.query.delete()


def get_devices() -> str:
    with engine.connect() as connection:
        with Session(bind=connection) as session:
            query = select(DeviceNetwork) \
                .options(joinedload(DeviceNetwork.discovery_method), joinedload(DeviceNetwork.device)) \
                .order_by(DeviceNetwork.discovered_at.desc())

            res = session.execute(query)

            device_network_dict: Dict[str, List[DeviceNetwork]] = partition(res.unique().scalars().all())

            header = ["STATUS", "MAC", "MAC_VENDOR", "IP", "GATEWAY", "FIRST_CONN_AT"]
            table = []
            for device_network_list in device_network_dict.values():
                table.append(format_output_device_network(device_network_list))

            return tabulate.tabulate(table, headers=header, tablefmt="double_grid")


def history_device(mac: str) -> str:
    with engine.connect() as connection:
        with Session(bind=connection) as session:
            query = select(DeviceNetwork).where(DeviceNetwork.device.has(Device.mac_addr == mac)) \
                .options(joinedload(DeviceNetwork.discovery_method), joinedload(DeviceNetwork.device)) \
                .order_by(DeviceNetwork.discovered_at.desc())

            res: Sequence[DeviceNetwork] = session.execute(query).unique().scalars().all()

            header = ["TIME", "MAC_ADDRESS", "IP", "GATEWAY", "DISCOVER_METHOD"]

            table = []
            for devnet in res:
                row = [
                    devnet.discovered_at,
                    devnet.device.mac_addr,
                    devnet.ip,
                    devnet.device.gateway,
                    devnet.discovery_method.method
                ]
                table.append(row)

            return tabulate.tabulate(table, headers=header, tablefmt="double_grid")


def count_history_line() -> int:
    with engine.connect() as connection:
        with Session(bind=connection) as session:
            value = session.query(DeviceNetwork.id).count()

    return value


def count_device_line() -> int:
    with engine.connect() as connection:
        with Session(bind=connection) as session:
            query = select(DeviceNetwork) \
                .options(joinedload(DeviceNetwork.discovery_method), joinedload(DeviceNetwork.device)) \
                .order_by(DeviceNetwork.discovered_at.desc())

            res = session.execute(query)

            device_network_dict: Dict[str, List[DeviceNetwork]] = partition(res.unique().scalars().all())

            return len(device_network_dict)


@functools.cache
def get_line_history(id_: int) -> Union[List, None]:
    with engine.connect() as connection:
        with Session(bind=connection) as session:
            query = select(DeviceNetwork) \
                .options(joinedload(DeviceNetwork.discovery_method), joinedload(DeviceNetwork.device)) \
                .order_by(DeviceNetwork.discovered_at.desc())

            res: Sequence[DeviceNetwork] = session.execute(query).unique().scalars().all()
            print(f"Numero de entradas no historico {len(res)}")
            print(res, id_)
            if len(res) > id_:
                devnet = res[id_]
                return [
                    devnet.device.mac_addr,
                    devnet.ip,
                    devnet.discovery_method.method,
                    devnet.discovered_at,
                    devnet.device.gateway,

                ]

            return None


@functools.cache
def get_line_device(id_: int) -> List:
    with engine.connect() as connection:
        with Session(bind=connection) as session:
            query = select(DeviceNetwork).where(DeviceNetwork.device_id == id_) \
                .options(joinedload(DeviceNetwork.discovery_method), joinedload(DeviceNetwork.device)) \
                .order_by(DeviceNetwork.discovered_at.desc())

            res = session.execute(query)

            device_network_dict: Dict[str, List[DeviceNetwork]] = partition(res.unique().scalars().all())

            device_list = list(device_network_dict.values())

            pre_formated = format_output_device_network(device_list[0])
            return [pre_formated[1], pre_formated[3], pre_formated[0], pre_formated[4], pre_formated[5], len(device_list[0])]

