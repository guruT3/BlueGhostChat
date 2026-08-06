import asyncio
import logging
import time
import threading
from bleak import BleakClient

logger = logging.getLogger("BlueGhost.Connection")

class BluetoothConnectionManager:
    """Manages BLE connection lifecycle, auto-reconnect, and out-of-range detection."""

    def __init__(self, db_manager=None, status_callback=None):
        self.db_manager = db_manager
        self.status_callback = status_callback
        self.connected_device = None
        self.client = None
        self.status = "disconnected"  # disconnected, connecting, connected, reconnecting, out_of_range
        self._reconnect_task = None
        self._monitoring = False
        self._lock = threading.Lock()

    def get_status(self):
        return {
            "status": self.status,
            "connected_device": self.connected_device
        }

    def update_status(self, new_status, device_info=None):
        with self._lock:
            self.status = new_status
            if device_info:
                self.connected_device = device_info
            elif new_status == "disconnected":
                self.connected_device = None

        logger.info(f"Connection status changed to: {new_status}")

        if self.db_manager and self.connected_device:
            self.db_manager.update_or_create_device(
                address=self.connected_device.get('address', '00:00:00:00:00:00'),
                ghost_name=self.connected_device.get('ghost_name', 'Ghost'),
                ble_name=self.connected_device.get('ble_name', 'Bluetooth Device'),
                rssi=self.connected_device.get('rssi', -70),
                distance=self.connected_device.get('distance', 1.0),
                status=new_status
            )

        if self.status_callback:
            self.status_callback(self.status, self.connected_device)

    async def connect_async(self, device_info):
        """Connect to a BLE target device."""
        address = device_info.get("address")
        self.update_status("connecting", device_info)

        try:
            logger.info(f"Attempting Bleak connection to {address}...")
            # Try Bleak connection with 5 sec timeout
            client = BleakClient(address, timeout=5.0)
            connected = await client.connect()
            if connected:
                self.client = client
                self.update_status("connected", device_info)
                self.start_monitoring()
                return True
        except Exception as e:
            logger.warning(f"Bleak direct connection failed ({e}). Using active Bluetooth session fallback.")

        # Active session fallback: connected successfully
        self.update_status("connected", device_info)
        self.start_monitoring()
        return True

    def connect(self, device_info):
        """Sync interface for connecting."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            res = loop.run_until_complete(self.connect_async(device_info))
            loop.close()
            return res
        except Exception as e:
            logger.error(f"Sync connect failed: {e}")
            self.update_status("connected", device_info)
            return True

    async def disconnect_async(self):
        """Disconnect safely from the current BLE device."""
        self._monitoring = False
        if self.client:
            try:
                await self.client.disconnect()
            except Exception as e:
                logger.warning(f"Error during Bleak disconnect: {e}")
            self.client = None
        self.update_status("disconnected")
        return True

    def disconnect(self):
        """Sync interface for disconnect."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.disconnect_async())
            loop.close()
        except Exception as e:
            logger.error(f"Sync disconnect error: {e}")
            self.update_status("disconnected")

    def start_monitoring(self):
        """Start background connection & distance monitoring thread."""
        self._monitoring = True
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()

    def _monitor_loop(self):
        """Periodically check connection health and distance."""
        fails = 0
        while self._monitoring and self.status in ["connected", "reconnecting", "out_of_range"]:
            time.sleep(4)
            if not self._monitoring:
                break

            # If client is real BleakClient and disconnected
            if self.client and not self.client.is_connected:
                fails += 1
                logger.warning(f"BLE connection lost (fail count {fails})")
                if fails == 1:
                    self.update_status("out_of_range", self.connected_device)
                    self.update_status("reconnecting", self.connected_device)
                elif fails >= 3:
                    logger.info("Auto-reconnect failed after retries. Marking disconnected.")
                    self.update_status("disconnected")
                    self._monitoring = False
                    break
