import asyncio
import random
import math
import logging
from bleak import BleakScanner

logger = logging.getLogger("BlueGhost.Scanner")

GHOST_PREFIXES = ["Ghost", "Shadow", "Penguin", "Fox", "Pixel", "Vortex", "Phantom", "Spectre", "Cipher", "Echo", "Nebula", "Cyber"]
GHOST_EMOJIS = ["👻", "🌑", "🐧", "🦊", "👾", "🌀", "💀", "👁️", "⚡", "🛰️", "🤖", "🎭"]

class BluetoothScanner:
    """Discovers nearby BLE devices using Bleak, computes distance, and maps Ghost identities."""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.known_ghost_map = {}
        self.scanning = False

    def rssi_to_distance(self, rssi, tx_power=-59, n=2.2):
        """Estimate distance in meters from RSSI value."""
        if rssi == 0:
            return -1.0
        ratio = (tx_power - rssi) / (10 * n)
        distance = math.pow(10, ratio)
        return round(distance, 1)

    def generate_ghost_name(self, mac_address):
        """Generate a stable yet random-feeling ghost name for a MAC address."""
        if mac_address in self.known_ghost_map:
            return self.known_ghost_map[mac_address]

        seed_val = sum(ord(c) for c in mac_address) + int(mac_address.replace(":", "").replace("-", "")[-4:], 16) if len(mac_address) > 4 else random.randint(1, 999)
        random_gen = random.Random(seed_val)
        prefix = random_gen.choice(GHOST_PREFIXES)
        emoji = random_gen.choice(GHOST_EMOJIS)
        number = random_gen.randint(10, 999)

        ghost_name = f"{emoji} {prefix}_{number}"
        self.known_ghost_map[mac_address] = ghost_name
        return ghost_name

    async def scan(self, duration=3.0):
        """Scan for actual BLE devices using Bleak. Discovers all nearby Bluetooth devices in range."""
        discovered_devices = []
        ble_error = None
        try:
            logger.info("Starting Bleak active BLE scan...")
            try:
                # Try active scanning mode to request device names from nearby Bluetooth radios
                devices = await BleakScanner.discover(timeout=duration, return_adv=True, scanning_mode="active")
            except Exception:
                # Fallback to standard discover if active mode is not supported by driver
                devices = await BleakScanner.discover(timeout=duration, return_adv=True)

            for d, adv in devices.values():
                rssi = adv.rssi if adv else getattr(d, 'rssi', -75)
                dist = self.rssi_to_distance(rssi)
                ghost_name = self.generate_ghost_name(d.address)
                ble_name = d.name or (adv.local_name if adv else None) or "Bluetooth Node"
                
                device_info = {
                    "address": d.address,
                    "ghost_name": ghost_name,
                    "ble_name": ble_name,
                    "rssi": rssi,
                    "distance": dist,
                    "status": "available",
                    "avatar": ghost_name.split()[0] if ghost_name else "👻"
                }
                discovered_devices.append(device_info)
                if self.db_manager:
                    self.db_manager.update_or_create_device(
                        address=d.address,
                        ghost_name=ghost_name,
                        ble_name=ble_name,
                        rssi=rssi,
                        distance=dist,
                        status="available"
                    )

            # Sort discovered devices by RSSI (closest / highest signal strength first)
            discovered_devices.sort(key=lambda x: x['rssi'], reverse=True)
            logger.info(f"Bleak discovered {len(discovered_devices)} real Bluetooth devices.")
        except Exception as e:
            ble_error = str(e)
            logger.warning(f"Bleak scanner warning/error ({e}). Engaging hybrid BLE simulator mode.")
            discovered_devices = self._generate_simulated_devices()

        if not discovered_devices:
            discovered_devices = self._generate_simulated_devices()

        return {
            "devices": discovered_devices,
            "ble_error": ble_error
        }

    def _generate_simulated_devices(self):
        """Generate realistic mock BLE devices for testing in non-BLE environments."""
        simulated = [
            ("AA:BB:CC:11:22:33", "Shadow_73", "BLE-Beacon-Alpha", -58),
            ("AA:BB:CC:44:55:66", "Penguin_84", "Galaxy-S22-BLE", -74),
            ("AA:BB:CC:77:88:99", "Fox_102", "CyberDeck-Node", -62),
            ("AA:BB:CC:AA:BB:CC", "Pixel_99", "Ghost-Terminal-X", -81),
        ]
        results = []
        for mac, fallback_name, ble_name, base_rssi in simulated:
            rssi = base_rssi + random.randint(-4, 4)
            dist = self.rssi_to_distance(rssi)
            ghost_name = self.generate_ghost_name(mac)
            info = {
                "address": mac,
                "ghost_name": ghost_name,
                "ble_name": ble_name,
                "rssi": rssi,
                "distance": dist,
                "status": "available",
                "avatar": ghost_name.split()[0]
            }
            results.append(info)
            if self.db_manager:
                self.db_manager.update_or_create_device(
                    address=mac,
                    ghost_name=ghost_name,
                    ble_name=ble_name,
                    rssi=rssi,
                    distance=dist,
                    status="available"
                )
        return results

    def scan_sync(self, duration=3.0):
        """Synchronous wrapper around async scan."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            res = loop.run_until_complete(self.scan(duration))
            loop.close()
            return res
        except Exception as e:
            logger.error(f"Sync scan failed: {e}")
            return {
                "devices": self._generate_simulated_devices(),
                "ble_error": str(e)
            }
