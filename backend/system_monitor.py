"""
System Monitor Module for Mac Status PWA
Provides system monitoring capabilities using psutil with macOS-specific optimizations
"""
import psutil
import platform
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import subprocess
import json

# Import error handling
from error_handler import (
    handle_system_monitor_error, 
    execute_with_fallback, 
    ErrorCategory, 
    global_fallback_manager,
    error_handler_decorator
)


@dataclass
class ProcessInfo:
    """Process information data structure"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_rss: int  # Resident Set Size in bytes
    status: str
    create_time: float
    cmdline: List[str]


@dataclass
class NetworkStats:
    """Network statistics data structure"""
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int


@dataclass
class BatteryInfo:
    """Battery information data structure"""
    percent: Optional[float]
    power_plugged: Optional[bool]
    secsleft: Optional[int]  # Seconds left, None if unknown or plugged in
    status: str  # "charging", "discharging", "full", "unknown"


@dataclass
class WiFiInfo:
    """WiFi connection information data structure"""
    ssid: Optional[str]
    signal_strength: Optional[int]  # dBm value
    signal_quality: str  # "excellent", "good", "fair", "poor", "no_signal"
    channel: Optional[int]
    frequency: Optional[float]  # GHz
    security: Optional[str]
    link_speed: Optional[int]  # Mbps
    is_connected: bool
    interface_name: Optional[str]


@dataclass
class RunningAppInfo:
    """Running application information data structure"""
    name: str
    pid: int
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    status: str  # "active", "background", "suspended"
    window_count: int
    is_gui_app: bool
    bundle_id: Optional[str]
    launch_time: Optional[float]


@dataclass
class DiskInfo:
    """Disk partition information data structure"""
    device: str
    mountpoint: str
    fstype: str
    total_gb: float
    used_gb: float
    free_gb: float
    percent: float
    is_removable: bool
    is_system: bool
    label: Optional[str]


@dataclass
class DevToolInfo:
    """Development tool information data structure"""
    name: str
    version: Optional[str]
    path: Optional[str]
    is_installed: bool
    is_running: bool
    additional_info: Optional[Dict[str, Any]]


@dataclass
class ThermalInfo:
    """Thermal and fan information data structure"""
    cpu_temperature: Optional[float]  # Celsius
    gpu_temperature: Optional[float]  # Celsius
    fan_speeds: List[Dict[str, Any]]  # List of fan info
    thermal_state: str  # "normal", "warm", "hot", "critical", "unknown"
    power_metrics: Optional[Dict[str, Any]]  # Power consumption data


@dataclass
class SystemStatus:
    """Complete system status data structure"""
    timestamp: datetime
    cpu_percent: float
    cpu_count: int
    cpu_freq: Optional[float]
    memory_used: int
    memory_total: int
    memory_percent: float
    disk_used: int
    disk_total: int
    disk_percent: float
    top_processes: List[ProcessInfo]
    network_io: NetworkStats
    temperature: Optional[float]
    uptime: float
    load_average: List[float]
    battery: Optional[BatteryInfo]
    wifi: Optional[WiFiInfo]
    running_apps: List[RunningAppInfo]
    disk_details: List[DiskInfo]
    dev_tools: List[DevToolInfo]
    thermal_info: Optional[ThermalInfo]


class SystemMonitor:
    """
    System monitoring class with macOS-specific optimizations
    Provides comprehensive system information gathering capabilities
    """
    
    def __init__(self, update_interval: float = 5.0):
        """
        Initialize SystemMonitor
        
        Args:
            update_interval: Interval in seconds between system updates
        """
        self.update_interval = update_interval
        self.is_macos = platform.system() == "Darwin"
        self._last_cpu_times = None
        self._last_network_io = None
        self._monitoring_task = None
        self._is_monitoring = False
        self._callbacks = []
        self._last_status = None
        self._alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0
        }
        
        # Initialize psutil for better performance
        psutil.cpu_percent(interval=None)  # First call to initialize
        
    async def get_system_info(self) -> SystemStatus:
        """
        Get comprehensive system information with error handling and fallback
        
        Returns:
            SystemStatus object containing all system metrics
        """
        async def primary_system_info():
            # Get basic system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_freq = self._get_cpu_frequency()
            
            # Memory information
            memory = psutil.virtual_memory()
            
            # Disk information (root partition)
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network_io = self._get_network_stats()
            
            # Top processes
            top_processes = await self._get_top_processes()
            
            # System uptime
            uptime = self._get_uptime()
            
            # Load average (macOS specific)
            load_avg = self._get_load_average()
            
            # Temperature (if available)
            temperature = await self._get_temperature()
            
            # Battery information (if available)
            battery = await self._get_battery_info()
            
            # WiFi information (if available)
            wifi = await self._get_wifi_info()
            
            # Running applications information
            running_apps = await self._get_running_apps()
            
            # Disk details information
            disk_details = await self._get_disk_details()
            
            # Development tools information
            dev_tools = await self._get_dev_tools_info()
            
            # Thermal information
            thermal_info = await self._get_thermal_info()
            
            return SystemStatus(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                cpu_freq=cpu_freq,
                memory_used=memory.used,
                memory_total=memory.total,
                memory_percent=memory.percent,
                disk_used=disk.used,
                disk_total=disk.total,
                disk_percent=disk.percent,
                top_processes=top_processes,
                network_io=network_io,
                temperature=temperature,
                uptime=uptime,
                load_average=load_avg,
                battery=battery,
                wifi=wifi,
                running_apps=running_apps,
                disk_details=disk_details,
                dev_tools=dev_tools,
                thermal_info=thermal_info
            )
        
        async def fallback_system_info():
            # フォールバックシステム情報を取得
            fallback_data = await global_fallback_manager.get_fallback_system_status()
            
            return SystemStatus(
                timestamp=datetime.now(),
                cpu_percent=fallback_data.get('cpu_percent', 0.0),
                cpu_count=psutil.cpu_count() if hasattr(psutil, 'cpu_count') else 1,
                cpu_freq=None,
                memory_used=0,
                memory_total=0,
                memory_percent=fallback_data.get('memory_percent', 0.0),
                disk_used=0,
                disk_total=0,
                disk_percent=fallback_data.get('disk_percent', 0.0),
                top_processes=[],
                network_io=NetworkStats(0, 0, 0, 0),
                temperature=None,
                uptime=0.0,
                load_average=[0.0, 0.0, 0.0],
                battery=None,
                wifi=None,
                running_apps=[],
                disk_details=[],
                dev_tools=[],
                thermal_info=None
            )
        
        try:
            return await execute_with_fallback(
                primary_func=primary_system_info,
                fallback_func=fallback_system_info,
                error_category=ErrorCategory.SYSTEM_MONITOR_ERROR,
                context={'component': 'system_info_collection'}
            )
        except Exception as e:
            error_info = handle_system_monitor_error(
                e, 
                {'component': 'system_info_collection'}
            )
            raise SystemMonitorError(f"[{error_info.error_id}] Failed to get system info: {str(e)}")
    
    def _get_cpu_frequency(self) -> Optional[float]:
        """Get CPU frequency in MHz"""
        try:
            if hasattr(psutil, 'cpu_freq'):
                freq = psutil.cpu_freq()
                return freq.current if freq else None
            return None
        except (AttributeError, OSError):
            return None
    
    def _get_network_stats(self) -> NetworkStats:
        """Get network I/O statistics"""
        try:
            net_io = psutil.net_io_counters()
            return NetworkStats(
                bytes_sent=net_io.bytes_sent,
                bytes_recv=net_io.bytes_recv,
                packets_sent=net_io.packets_sent,
                packets_recv=net_io.packets_recv
            )
        except Exception:
            return NetworkStats(0, 0, 0, 0)
    
    async def _get_top_processes(self, limit: int = 10) -> List[ProcessInfo]:
        """
        Get top processes by CPU and memory usage
        
        Args:
            limit: Maximum number of processes to return
            
        Returns:
            List of ProcessInfo objects
        """
        try:
            processes = []
            
            # Get all processes with their info
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                          'memory_info', 'status', 'create_time', 'cmdline']):
                try:
                    pinfo = proc.info
                    if pinfo['cpu_percent'] is None:
                        pinfo['cpu_percent'] = 0.0
                    
                    process_info = ProcessInfo(
                        pid=pinfo['pid'],
                        name=pinfo['name'] or 'Unknown',
                        cpu_percent=pinfo['cpu_percent'],
                        memory_percent=pinfo['memory_percent'] or 0.0,
                        memory_rss=pinfo['memory_info'].rss if pinfo['memory_info'] else 0,
                        status=pinfo['status'],
                        create_time=pinfo['create_time'],
                        cmdline=pinfo['cmdline'] or []
                    )
                    processes.append(process_info)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Skip processes that can't be accessed
                    continue
            
            # Sort by CPU usage first, then by memory usage
            processes.sort(key=lambda x: (x.cpu_percent, x.memory_percent), reverse=True)
            
            return processes[:limit]
            
        except Exception as e:
            print(f"Warning: Could not get process information: {e}")
            return []
    
    async def get_processes_by_cpu(self, limit: int = 10, min_cpu_percent: float = 0.0) -> List[ProcessInfo]:
        """
        Get processes sorted by CPU usage with filtering
        
        Args:
            limit: Maximum number of processes to return
            min_cpu_percent: Minimum CPU percentage to include
            
        Returns:
            List of ProcessInfo objects sorted by CPU usage
        """
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                          'memory_info', 'status', 'create_time', 'cmdline']):
                try:
                    pinfo = proc.info
                    cpu_percent = pinfo['cpu_percent'] or 0.0
                    
                    # Filter by minimum CPU usage
                    if cpu_percent < min_cpu_percent:
                        continue
                    
                    process_info = ProcessInfo(
                        pid=pinfo['pid'],
                        name=pinfo['name'] or 'Unknown',
                        cpu_percent=cpu_percent,
                        memory_percent=pinfo['memory_percent'] or 0.0,
                        memory_rss=pinfo['memory_info'].rss if pinfo['memory_info'] else 0,
                        status=pinfo['status'],
                        create_time=pinfo['create_time'],
                        cmdline=pinfo['cmdline'] or []
                    )
                    processes.append(process_info)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by CPU usage (descending)
            processes.sort(key=lambda x: x.cpu_percent, reverse=True)
            
            return processes[:limit]
            
        except Exception as e:
            print(f"Warning: Could not get CPU processes: {e}")
            return []
    
    async def get_processes_by_memory(self, limit: int = 10, min_memory_mb: float = 0.0) -> List[ProcessInfo]:
        """
        Get processes sorted by memory usage with filtering
        
        Args:
            limit: Maximum number of processes to return
            min_memory_mb: Minimum memory usage in MB to include
            
        Returns:
            List of ProcessInfo objects sorted by memory usage
        """
        try:
            processes = []
            min_memory_bytes = min_memory_mb * 1024 * 1024  # Convert MB to bytes
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                          'memory_info', 'status', 'create_time', 'cmdline']):
                try:
                    pinfo = proc.info
                    memory_rss = pinfo['memory_info'].rss if pinfo['memory_info'] else 0
                    
                    # Filter by minimum memory usage
                    if memory_rss < min_memory_bytes:
                        continue
                    
                    process_info = ProcessInfo(
                        pid=pinfo['pid'],
                        name=pinfo['name'] or 'Unknown',
                        cpu_percent=pinfo['cpu_percent'] or 0.0,
                        memory_percent=pinfo['memory_percent'] or 0.0,
                        memory_rss=memory_rss,
                        status=pinfo['status'],
                        create_time=pinfo['create_time'],
                        cmdline=pinfo['cmdline'] or []
                    )
                    processes.append(process_info)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by memory usage (descending)
            processes.sort(key=lambda x: x.memory_rss, reverse=True)
            
            return processes[:limit]
            
        except Exception as e:
            print(f"Warning: Could not get memory processes: {e}")
            return []
    
    async def get_processes_by_name(self, name_pattern: str, case_sensitive: bool = False) -> List[ProcessInfo]:
        """
        Get processes filtered by name pattern
        
        Args:
            name_pattern: Pattern to match process names (supports partial matching)
            case_sensitive: Whether to perform case-sensitive matching
            
        Returns:
            List of ProcessInfo objects matching the name pattern
        """
        try:
            processes = []
            
            # Prepare pattern for matching
            if not case_sensitive:
                name_pattern = name_pattern.lower()
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                          'memory_info', 'status', 'create_time', 'cmdline']):
                try:
                    pinfo = proc.info
                    process_name = pinfo['name'] or 'Unknown'
                    
                    # Check if name matches pattern
                    search_name = process_name if case_sensitive else process_name.lower()
                    if name_pattern not in search_name:
                        continue
                    
                    process_info = ProcessInfo(
                        pid=pinfo['pid'],
                        name=process_name,
                        cpu_percent=pinfo['cpu_percent'] or 0.0,
                        memory_percent=pinfo['memory_percent'] or 0.0,
                        memory_rss=pinfo['memory_info'].rss if pinfo['memory_info'] else 0,
                        status=pinfo['status'],
                        create_time=pinfo['create_time'],
                        cmdline=pinfo['cmdline'] or []
                    )
                    processes.append(process_info)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Sort by CPU usage (descending)
            processes.sort(key=lambda x: x.cpu_percent, reverse=True)
            
            return processes
            
        except Exception as e:
            print(f"Warning: Could not get processes by name: {e}")
            return []
    
    async def get_process_details(self, pid: int) -> Optional[ProcessInfo]:
        """
        Get detailed information about a specific process
        
        Args:
            pid: Process ID
            
        Returns:
            ProcessInfo object or None if process not found
        """
        try:
            proc = psutil.Process(pid)
            
            # Get process information
            with proc.oneshot():
                process_info = ProcessInfo(
                    pid=proc.pid,
                    name=proc.name(),
                    cpu_percent=proc.cpu_percent(),
                    memory_percent=proc.memory_percent(),
                    memory_rss=proc.memory_info().rss,
                    status=proc.status(),
                    create_time=proc.create_time(),
                    cmdline=proc.cmdline()
                )
            
            return process_info
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None
        except Exception as e:
            print(f"Warning: Could not get process details for PID {pid}: {e}")
            return None
    
    def add_callback(self, callback):
        """
        Add a callback function to be called when system status updates
        
        Args:
            callback: Async function that takes SystemStatus as parameter
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def remove_callback(self, callback):
        """
        Remove a callback function
        
        Args:
            callback: Callback function to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def set_alert_thresholds(self, cpu_percent: float = None, memory_percent: float = None, disk_percent: float = None):
        """
        Set alert thresholds for system monitoring
        
        Args:
            cpu_percent: CPU usage threshold for alerts
            memory_percent: Memory usage threshold for alerts
            disk_percent: Disk usage threshold for alerts
        """
        if cpu_percent is not None:
            self._alert_thresholds['cpu_percent'] = cpu_percent
        if memory_percent is not None:
            self._alert_thresholds['memory_percent'] = memory_percent
        if disk_percent is not None:
            self._alert_thresholds['disk_percent'] = disk_percent
    
    async def start_monitoring(self):
        """
        Start real-time system monitoring
        """
        if self._is_monitoring:
            return
        
        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        print(f"Started system monitoring with {self.update_interval}s interval")
    
    async def stop_monitoring(self):
        """
        Stop real-time system monitoring
        """
        if not self._is_monitoring:
            return
        
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        print("Stopped system monitoring")
    
    async def _monitoring_loop(self):
        """
        Main monitoring loop that runs continuously
        """
        try:
            while self._is_monitoring:
                try:
                    # Get current system status
                    current_status = await self.get_system_info()
                    
                    # Check for alerts
                    alerts = self._check_alerts(current_status)
                    
                    # Detect significant changes
                    changes = self._detect_changes(current_status)
                    
                    # Call all registered callbacks
                    for callback in self._callbacks:
                        try:
                            await callback(current_status, alerts, changes)
                        except Exception as e:
                            print(f"Error in monitoring callback: {e}")
                    
                    # Update last status
                    self._last_status = current_status
                    
                    # Wait for next update
                    await asyncio.sleep(self.update_interval)
                    
                except Exception as e:
                    print(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(self.update_interval)
                    
        except asyncio.CancelledError:
            print("Monitoring loop cancelled")
            raise
    
    def _check_alerts(self, status: SystemStatus) -> List[Dict[str, Any]]:
        """
        Check if any system metrics exceed alert thresholds
        
        Args:
            status: Current system status
            
        Returns:
            List of alert dictionaries
        """
        alerts = []
        
        # CPU alert
        if status.cpu_percent > self._alert_thresholds['cpu_percent']:
            alerts.append({
                'type': 'cpu_high',
                'message': f'High CPU usage: {status.cpu_percent:.1f}%',
                'value': status.cpu_percent,
                'threshold': self._alert_thresholds['cpu_percent'],
                'severity': 'warning' if status.cpu_percent < 95 else 'critical'
            })
        
        # Memory alert
        if status.memory_percent > self._alert_thresholds['memory_percent']:
            alerts.append({
                'type': 'memory_high',
                'message': f'High memory usage: {status.memory_percent:.1f}%',
                'value': status.memory_percent,
                'threshold': self._alert_thresholds['memory_percent'],
                'severity': 'warning' if status.memory_percent < 95 else 'critical'
            })
        
        # Disk alert
        if status.disk_percent > self._alert_thresholds['disk_percent']:
            alerts.append({
                'type': 'disk_high',
                'message': f'High disk usage: {status.disk_percent:.1f}%',
                'value': status.disk_percent,
                'threshold': self._alert_thresholds['disk_percent'],
                'severity': 'warning' if status.disk_percent < 98 else 'critical'
            })
        
        return alerts
    
    def _detect_changes(self, current_status: SystemStatus) -> List[Dict[str, Any]]:
        """
        Detect significant changes in system status
        
        Args:
            current_status: Current system status
            
        Returns:
            List of change dictionaries
        """
        changes = []
        
        if self._last_status is None:
            return changes
        
        # CPU change detection (>10% change)
        cpu_change = abs(current_status.cpu_percent - self._last_status.cpu_percent)
        if cpu_change > 10.0:
            changes.append({
                'type': 'cpu_change',
                'message': f'CPU usage changed by {cpu_change:.1f}%',
                'old_value': self._last_status.cpu_percent,
                'new_value': current_status.cpu_percent,
                'change': cpu_change
            })
        
        # Memory change detection (>5% change)
        memory_change = abs(current_status.memory_percent - self._last_status.memory_percent)
        if memory_change > 5.0:
            changes.append({
                'type': 'memory_change',
                'message': f'Memory usage changed by {memory_change:.1f}%',
                'old_value': self._last_status.memory_percent,
                'new_value': current_status.memory_percent,
                'change': memory_change
            })
        
        # Process changes (new top processes)
        if len(current_status.top_processes) > 0 and len(self._last_status.top_processes) > 0:
            current_top = current_status.top_processes[0]
            last_top = self._last_status.top_processes[0]
            
            if current_top.pid != last_top.pid:
                changes.append({
                    'type': 'top_process_change',
                    'message': f'Top process changed from {last_top.name} to {current_top.name}',
                    'old_process': {
                        'name': last_top.name,
                        'pid': last_top.pid,
                        'cpu_percent': last_top.cpu_percent
                    },
                    'new_process': {
                        'name': current_top.name,
                        'pid': current_top.pid,
                        'cpu_percent': current_top.cpu_percent
                    }
                })
        
        return changes
    
    async def get_monitoring_stats(self) -> Dict[str, Any]:
        """
        Get monitoring statistics and status
        
        Returns:
            Dictionary with monitoring information
        """
        return {
            'is_monitoring': self._is_monitoring,
            'update_interval': self.update_interval,
            'callbacks_count': len(self._callbacks),
            'alert_thresholds': self._alert_thresholds.copy(),
            'last_update': self._last_status.timestamp.isoformat() if self._last_status else None
        }
    
    def _get_uptime(self) -> float:
        """Get system uptime in seconds"""
        try:
            return psutil.boot_time()
        except Exception:
            return 0.0
    
    def _get_load_average(self) -> List[float]:
        """Get system load average (1, 5, 15 minutes)"""
        try:
            if hasattr(psutil, 'getloadavg'):
                return list(psutil.getloadavg())
            elif self.is_macos:
                # Fallback for macOS using uptime command
                result = subprocess.run(['uptime'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Parse load averages from uptime output
                    output = result.stdout.strip()
                    if 'load averages:' in output:
                        load_part = output.split('load averages:')[1].strip()
                        loads = [float(x.strip()) for x in load_part.split()]
                        return loads[:3]  # Return first 3 values
            return [0.0, 0.0, 0.0]
        except Exception:
            return [0.0, 0.0, 0.0]
    
    async def _get_temperature(self) -> Optional[float]:
        """
        Get system temperature (macOS specific)
        Uses powermetrics or other macOS-specific tools if available
        """
        if not self.is_macos:
            return None
            
        try:
            # Try to get temperature using powermetrics (requires sudo, so might fail)
            # This is a basic implementation - in production you might want to use
            # other methods or libraries like py-cpuinfo
            
            # For now, return None as temperature monitoring on macOS
            # typically requires elevated privileges
            return None
            
        except Exception:
            return None
    
    async def _get_battery_info(self) -> Optional[BatteryInfo]:
        """
        Get battery information using psutil
        
        Returns:
            BatteryInfo object or None if no battery present
        """
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                # No battery present (desktop Mac)
                return None
            
            # Determine battery status
            if battery.power_plugged:
                if battery.percent >= 100:
                    status = "full"
                else:
                    status = "charging"
            else:
                status = "discharging"
            
            return BatteryInfo(
                percent=battery.percent,
                power_plugged=battery.power_plugged,
                secsleft=battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None,
                status=status
            )
            
        except Exception as e:
            print(f"Warning: Could not get battery information: {e}")
            return None
    
    async def _get_wifi_info(self) -> Optional[WiFiInfo]:
        """
        Get WiFi connection information using macOS-specific commands
        
        Returns:
            WiFiInfo object or None if WiFi not available or not connected
        """
        if not self.is_macos:
            return None
            
        try:
            # Get WiFi interface name first
            interface_result = subprocess.run([
                'networksetup', '-listallhardwareports'
            ], capture_output=True, text=True, timeout=10)
            
            wifi_interface = None
            if interface_result.returncode == 0:
                lines = interface_result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if 'Wi-Fi' in line and i + 1 < len(lines):
                        device_line = lines[i + 1]
                        if 'Device:' in device_line:
                            wifi_interface = device_line.split('Device:')[1].strip()
                            break
            
            if not wifi_interface:
                # Fallback to common interface names
                wifi_interface = 'en0'
            
            # Get detailed WiFi information using airport command
            airport_result = subprocess.run([
                '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport',
                '-I'
            ], capture_output=True, text=True, timeout=10)
            
            if airport_result.returncode != 0:
                return WiFiInfo(
                    ssid=None,
                    signal_strength=None,
                    signal_quality="no_signal",
                    channel=None,
                    frequency=None,
                    security=None,
                    link_speed=None,
                    is_connected=False,
                    interface_name=wifi_interface
                )
            
            # Parse airport output
            wifi_data = {}
            for line in airport_result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    wifi_data[key.strip()] = value.strip()
            
            # Extract information
            ssid = wifi_data.get('SSID')
            signal_strength = None
            channel = None
            frequency = None
            security = wifi_data.get('link auth')
            
            # Parse signal strength (RSSI)
            if 'agrCtlRSSI' in wifi_data:
                try:
                    signal_strength = int(wifi_data['agrCtlRSSI'])
                except ValueError:
                    pass
            
            # Parse channel
            if 'channel' in wifi_data:
                try:
                    channel_info = wifi_data['channel']
                    # Extract channel number (format like "6 (2.4 GHz)")
                    if '(' in channel_info:
                        channel = int(channel_info.split('(')[0].strip())
                        freq_part = channel_info.split('(')[1].split(')')[0]
                        if 'GHz' in freq_part:
                            frequency = float(freq_part.replace('GHz', '').strip())
                    else:
                        channel = int(channel_info)
                except (ValueError, IndexError):
                    pass
            
            # Get link speed using ifconfig
            link_speed = None
            try:
                ifconfig_result = subprocess.run([
                    'ifconfig', wifi_interface
                ], capture_output=True, text=True, timeout=5)
                
                if ifconfig_result.returncode == 0:
                    for line in ifconfig_result.stdout.split('\n'):
                        if 'media:' in line and 'Mbps' in line:
                            # Extract speed from line like "media: autoselect (1000baseT <full-duplex>)"
                            import re
                            speed_match = re.search(r'(\d+)(?:base|Mbps)', line)
                            if speed_match:
                                link_speed = int(speed_match.group(1))
                            break
            except Exception:
                pass
            
            # Determine signal quality
            signal_quality = "unknown"
            if signal_strength is not None:
                if signal_strength >= -30:
                    signal_quality = "excellent"
                elif signal_strength >= -50:
                    signal_quality = "good"
                elif signal_strength >= -70:
                    signal_quality = "fair"
                elif signal_strength >= -90:
                    signal_quality = "poor"
                else:
                    signal_quality = "very_poor"
            
            is_connected = ssid is not None and ssid != ""
            
            return WiFiInfo(
                ssid=ssid,
                signal_strength=signal_strength,
                signal_quality=signal_quality,
                channel=channel,
                frequency=frequency,
                security=security,
                link_speed=link_speed,
                is_connected=is_connected,
                interface_name=wifi_interface
            )
            
        except Exception as e:
            print(f"Warning: Could not get WiFi information: {e}")
            return WiFiInfo(
                ssid=None,
                signal_strength=None,
                signal_quality="unknown",
                channel=None,
                frequency=None,
                security=None,
                link_speed=None,
                is_connected=False,
                interface_name=None
            )
    
    async def _get_running_apps(self) -> List[RunningAppInfo]:
        """
        Get running GUI applications using macOS-specific commands
        
        Returns:
            List of RunningAppInfo objects
        """
        running_apps = []
        
        if not self.is_macos:
            return running_apps
            
        try:
            # Get GUI applications using AppleScript
            applescript_cmd = '''
            tell application "System Events"
                set appList to {}
                repeat with proc in (every process whose background only is false)
                    try
                        set appName to name of proc
                        set appPID to unix id of proc
                        set windowCount to count of windows of proc
                        set end of appList to {appName, appPID, windowCount}
                    end try
                end repeat
                return appList
            end tell
            '''
            
            result = subprocess.run([
                'osascript', '-e', applescript_cmd
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode != 0:
                print(f"AppleScript failed: {result.stderr}")
                return running_apps
            
            # Parse AppleScript output
            gui_apps = {}
            if result.stdout.strip():
                # Parse the AppleScript list format
                output = result.stdout.strip()
                # Remove outer braces and split by app entries
                if output.startswith('{') and output.endswith('}'):
                    output = output[1:-1]
                    
                    # Split by app entries (each app is {name, pid, windowCount})
                    import re
                    app_matches = re.findall(r'\{([^}]+)\}', output)
                    
                    for match in app_matches:
                        parts = [part.strip().strip('"') for part in match.split(',')]
                        if len(parts) >= 3:
                            try:
                                app_name = parts[0]
                                app_pid = int(parts[1])
                                window_count = int(parts[2])
                                gui_apps[app_pid] = {
                                    'name': app_name,
                                    'window_count': window_count
                                }
                            except (ValueError, IndexError):
                                continue
            
            # Get detailed process information using psutil
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                           'memory_info', 'status', 'create_time']):
                try:
                    pinfo = proc.info
                    pid = pinfo['pid']
                    
                    # Check if this is a GUI app
                    if pid in gui_apps:
                        gui_info = gui_apps[pid]
                        
                        # Get memory in MB
                        memory_mb = 0
                        if pinfo['memory_info']:
                            memory_mb = pinfo['memory_info'].rss / (1024 * 1024)
                        
                        # Determine app status
                        status = "background"
                        if gui_info['window_count'] > 0:
                            status = "active"
                        elif pinfo['status'] == psutil.STATUS_STOPPED:
                            status = "suspended"
                        
                        # Try to get bundle ID (macOS specific)
                        bundle_id = None
                        try:
                            # This is a simplified approach - in practice, you might need more complex logic
                            bundle_id = f"com.app.{gui_info['name'].lower().replace(' ', '')}"
                        except:
                            pass
                        
                        app_info = RunningAppInfo(
                            name=gui_info['name'],
                            pid=pid,
                            cpu_percent=pinfo['cpu_percent'] or 0.0,
                            memory_percent=pinfo['memory_percent'] or 0.0,
                            memory_mb=memory_mb,
                            status=status,
                            window_count=gui_info['window_count'],
                            is_gui_app=True,
                            bundle_id=bundle_id,
                            launch_time=pinfo['create_time']
                        )
                        
                        running_apps.append(app_info)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    print(f"Error processing app {pinfo.get('name', 'Unknown')}: {e}")
                    continue
            
            # Sort by CPU usage (descending)
            running_apps.sort(key=lambda x: x.cpu_percent, reverse=True)
            
            return running_apps
            
        except Exception as e:
            print(f"Warning: Could not get running apps information: {e}")
            return running_apps
    
    async def _get_disk_details(self) -> List[DiskInfo]:
        """
        Get detailed disk information for all partitions
        
        Returns:
            List of DiskInfo objects
        """
        disk_details = []
        
        try:
            # Get all disk partitions
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    # Get usage statistics
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    # Convert bytes to GB
                    total_gb = usage.total / (1024**3)
                    used_gb = usage.used / (1024**3)
                    free_gb = usage.free / (1024**3)
                    percent = (usage.used / usage.total) * 100 if usage.total > 0 else 0
                    
                    # Determine if removable (basic heuristic)
                    is_removable = (
                        '/Volumes/' in partition.mountpoint and 
                        partition.mountpoint != '/' and
                        'disk' in partition.device.lower()
                    )
                    
                    # Determine if system disk
                    is_system = partition.mountpoint == '/' or partition.mountpoint.startswith('/System')
                    
                    # Get disk label (macOS specific)
                    label = None
                    if self.is_macos:
                        try:
                            if partition.mountpoint.startswith('/Volumes/'):
                                label = partition.mountpoint.split('/Volumes/')[-1]
                            elif partition.mountpoint == '/':
                                label = 'Macintosh HD'
                            else:
                                # Try to get volume name using diskutil
                                result = subprocess.run([
                                    'diskutil', 'info', partition.device
                                ], capture_output=True, text=True, timeout=5)
                                
                                if result.returncode == 0:
                                    for line in result.stdout.split('\n'):
                                        if 'Volume Name:' in line:
                                            label = line.split('Volume Name:')[1].strip()
                                            break
                        except Exception:
                            pass
                    
                    # Skip very small partitions (< 100MB) or inaccessible ones
                    if total_gb < 0.1:
                        continue
                    
                    disk_info = DiskInfo(
                        device=partition.device,
                        mountpoint=partition.mountpoint,
                        fstype=partition.fstype,
                        total_gb=total_gb,
                        used_gb=used_gb,
                        free_gb=free_gb,
                        percent=percent,
                        is_removable=is_removable,
                        is_system=is_system,
                        label=label
                    )
                    
                    disk_details.append(disk_info)
                    
                except (PermissionError, OSError) as e:
                    # Skip inaccessible partitions
                    print(f"Warning: Could not access partition {partition.mountpoint}: {e}")
                    continue
            
            # Sort by system disks first, then by total size
            disk_details.sort(key=lambda x: (not x.is_system, -x.total_gb))
            
            return disk_details
            
        except Exception as e:
            print(f"Warning: Could not get disk details: {e}")
            return disk_details
    
    async def _get_dev_tools_info(self) -> List[DevToolInfo]:
        """
        Get development tools information
        
        Returns:
            List of DevToolInfo objects
        """
        dev_tools = []
        
        # Define tools to check
        tools_to_check = [
            {
                'name': 'Xcode',
                'command': ['xcode-select', '--print-path'],
                'version_command': ['xcodebuild', '-version'],
                'app_name': 'Xcode'
            },
            {
                'name': 'Git',
                'command': ['which', 'git'],
                'version_command': ['git', '--version'],
                'app_name': None
            },
            {
                'name': 'Homebrew',
                'command': ['which', 'brew'],
                'version_command': ['brew', '--version'],
                'app_name': None
            },
            {
                'name': 'Node.js',
                'command': ['which', 'node'],
                'version_command': ['node', '--version'],
                'app_name': None
            },
            {
                'name': 'Python',
                'command': ['which', 'python3'],
                'version_command': ['python3', '--version'],
                'app_name': None
            },
            {
                'name': 'Docker',
                'command': ['which', 'docker'],
                'version_command': ['docker', '--version'],
                'app_name': 'Docker Desktop'
            },
            {
                'name': 'VS Code',
                'command': ['which', 'code'],
                'version_command': ['code', '--version'],
                'app_name': 'Visual Studio Code'
            }
        ]
        
        for tool_config in tools_to_check:
            try:
                tool_info = await self._check_dev_tool(tool_config)
                dev_tools.append(tool_info)
            except Exception as e:
                print(f"Warning: Could not check {tool_config['name']}: {e}")
                # Add as not installed
                dev_tools.append(DevToolInfo(
                    name=tool_config['name'],
                    version=None,
                    path=None,
                    is_installed=False,
                    is_running=False,
                    additional_info=None
                ))
        
        return dev_tools
    
    async def _check_dev_tool(self, tool_config: Dict[str, Any]) -> DevToolInfo:
        """
        Check individual development tool
        
        Args:
            tool_config: Tool configuration dictionary
            
        Returns:
            DevToolInfo object
        """
        name = tool_config['name']
        command = tool_config['command']
        version_command = tool_config.get('version_command')
        app_name = tool_config.get('app_name')
        
        # Check if tool is installed
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            is_installed = result.returncode == 0
            path = result.stdout.strip() if is_installed else None
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            is_installed = False
            path = None
        
        # Get version if installed
        version = None
        if is_installed and version_command:
            try:
                version_result = subprocess.run(
                    version_command,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if version_result.returncode == 0:
                    version_output = version_result.stdout.strip()
                    # Parse version from output
                    version = self._parse_version(name, version_output)
                    
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        # Check if tool is running (for GUI apps)
        is_running = False
        if app_name and hasattr(self, '_last_status') and self._last_status:
            # Check if app is in running apps list
            if hasattr(self._last_status, 'running_apps'):
                for app in self._last_status.running_apps:
                    if app_name.lower() in app.name.lower():
                        is_running = True
                        break
        
        # Get additional info for specific tools
        additional_info = await self._get_tool_additional_info(name, is_installed, path)
        
        return DevToolInfo(
            name=name,
            version=version,
            path=path,
            is_installed=is_installed,
            is_running=is_running,
            additional_info=additional_info
        )
    
    def _parse_version(self, tool_name: str, version_output: str) -> Optional[str]:
        """Parse version from command output"""
        try:
            if tool_name == 'Git':
                # "git version 2.39.3 (Apple Git-145)"
                if 'git version' in version_output:
                    return version_output.split('git version')[1].split()[0]
            elif tool_name == 'Homebrew':
                # "Homebrew 4.1.11"
                lines = version_output.split('\n')
                for line in lines:
                    if 'Homebrew' in line:
                        return line.split('Homebrew')[1].strip()
            elif tool_name == 'Node.js':
                # "v18.17.0"
                return version_output.strip()
            elif tool_name == 'Python':
                # "Python 3.11.5"
                if 'Python' in version_output:
                    return version_output.split('Python')[1].strip()
            elif tool_name == 'Docker':
                # "Docker version 24.0.6, build ed223bc"
                if 'Docker version' in version_output:
                    return version_output.split('Docker version')[1].split(',')[0].strip()
            elif tool_name == 'VS Code':
                # Multi-line output, first line is version
                return version_output.split('\n')[0].strip()
            elif tool_name == 'Xcode':
                # "Xcode 15.0\nBuild version 15A240d"
                lines = version_output.split('\n')
                for line in lines:
                    if 'Xcode' in line:
                        return line.split('Xcode')[1].strip()
            
            # Fallback: return first line
            return version_output.split('\n')[0].strip()
            
        except Exception:
            return version_output.strip() if version_output else None
    
    async def _get_tool_additional_info(self, tool_name: str, is_installed: bool, path: Optional[str]) -> Optional[Dict[str, Any]]:
        """Get additional information for specific tools"""
        if not is_installed:
            return None
        
        additional_info = {}
        
        try:
            if tool_name == 'Git':
                # Get git config info
                try:
                    user_result = subprocess.run(
                        ['git', 'config', '--global', 'user.name'],
                        capture_output=True, text=True, timeout=3
                    )
                    if user_result.returncode == 0:
                        additional_info['user_name'] = user_result.stdout.strip()
                    
                    email_result = subprocess.run(
                        ['git', 'config', '--global', 'user.email'],
                        capture_output=True, text=True, timeout=3
                    )
                    if email_result.returncode == 0:
                        additional_info['user_email'] = email_result.stdout.strip()
                except Exception:
                    pass
            
            elif tool_name == 'Homebrew':
                # Get brew info
                try:
                    info_result = subprocess.run(
                        ['brew', '--prefix'],
                        capture_output=True, text=True, timeout=3
                    )
                    if info_result.returncode == 0:
                        additional_info['prefix'] = info_result.stdout.strip()
                except Exception:
                    pass
            
            elif tool_name == 'Node.js':
                # Get npm version
                try:
                    npm_result = subprocess.run(
                        ['npm', '--version'],
                        capture_output=True, text=True, timeout=3
                    )
                    if npm_result.returncode == 0:
                        additional_info['npm_version'] = npm_result.stdout.strip()
                except Exception:
                    pass
            
            elif tool_name == 'Python':
                # Get pip version
                try:
                    pip_result = subprocess.run(
                        ['pip3', '--version'],
                        capture_output=True, text=True, timeout=3
                    )
                    if pip_result.returncode == 0:
                        additional_info['pip_version'] = pip_result.stdout.strip().split()[1]
                except Exception:
                    pass
            
            elif tool_name == 'Docker':
                # Get docker compose version
                try:
                    compose_result = subprocess.run(
                        ['docker', 'compose', 'version'],
                        capture_output=True, text=True, timeout=3
                    )
                    if compose_result.returncode == 0:
                        additional_info['compose_version'] = compose_result.stdout.strip()
                except Exception:
                    pass
        
        except Exception:
            pass
        
        return additional_info if additional_info else None
    
    async def _get_thermal_info(self) -> Optional[ThermalInfo]:
        """
        Get thermal and fan information (macOS specific)
        
        Returns:
            ThermalInfo object or None if not available
        """
        if not self.is_macos:
            return None
        
        cpu_temperature = None
        gpu_temperature = None
        fan_speeds = []
        thermal_state = "unknown"
        power_metrics = None
        
        try:
            # Try to get temperature using powermetrics (requires sudo, likely to fail)
            try:
                powermetrics_result = subprocess.run([
                    'sudo', 'powermetrics', '--samplers', 'smc', '-n', '1', '--show-initial-usage'
                ], capture_output=True, text=True, timeout=10)
                
                if powermetrics_result.returncode == 0:
                    output = powermetrics_result.stdout
                    
                    # Parse CPU temperature
                    for line in output.split('\n'):
                        if 'CPU die temperature' in line:
                            try:
                                temp_str = line.split(':')[1].strip().replace('C', '').strip()
                                cpu_temperature = float(temp_str)
                            except (ValueError, IndexError):
                                pass
                        elif 'GPU die temperature' in line:
                            try:
                                temp_str = line.split(':')[1].strip().replace('C', '').strip()
                                gpu_temperature = float(temp_str)
                            except (ValueError, IndexError):
                                pass
                        elif 'Fan' in line and 'rpm' in line:
                            try:
                                # Parse fan speed
                                parts = line.split(':')
                                if len(parts) >= 2:
                                    fan_name = parts[0].strip()
                                    rpm_str = parts[1].strip().replace('rpm', '').strip()
                                    rpm = int(float(rpm_str))
                                    fan_speeds.append({
                                        'name': fan_name,
                                        'rpm': rpm
                                    })
                            except (ValueError, IndexError):
                                pass
            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
                # powermetrics requires sudo, so this is expected to fail in most cases
                pass
            
            # Alternative: Try to get temperature using system_profiler
            if cpu_temperature is None:
                try:
                    system_profiler_result = subprocess.run([
                        'system_profiler', 'SPHardwareDataType', '-json'
                    ], capture_output=True, text=True, timeout=10)
                    
                    if system_profiler_result.returncode == 0:
                        import json
                        data = json.loads(system_profiler_result.stdout)
                        # This doesn't typically include temperature, but we try anyway
                        pass
                except Exception:
                    pass
            
            # Alternative: Try using istats (if installed via Homebrew)
            if cpu_temperature is None:
                try:
                    istats_result = subprocess.run([
                        'istats', 'cpu', 'temp'
                    ], capture_output=True, text=True, timeout=5)
                    
                    if istats_result.returncode == 0:
                        # Parse istats output: "CPU temp: 45.0°C"
                        output = istats_result.stdout.strip()
                        if '°C' in output:
                            temp_str = output.split(':')[1].strip().replace('°C', '').strip()
                            cpu_temperature = float(temp_str)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
            
            # Try to get fan information using istats
            if not fan_speeds:
                try:
                    istats_fan_result = subprocess.run([
                        'istats', 'fan'
                    ], capture_output=True, text=True, timeout=5)
                    
                    if istats_fan_result.returncode == 0:
                        # Parse istats fan output
                        for line in istats_fan_result.stdout.split('\n'):
                            if 'Fan' in line and 'RPM' in line:
                                try:
                                    # Parse line like "Fan 0: 1200 RPM"
                                    parts = line.split(':')
                                    if len(parts) >= 2:
                                        fan_name = parts[0].strip()
                                        rpm_str = parts[1].strip().replace('RPM', '').strip()
                                        rpm = int(float(rpm_str))
                                        fan_speeds.append({
                                            'name': fan_name,
                                            'rpm': rpm
                                        })
                                except (ValueError, IndexError):
                                    pass
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
            
            # Try to get thermal state using pmset
            try:
                pmset_result = subprocess.run([
                    'pmset', '-g', 'therm'
                ], capture_output=True, text=True, timeout=5)
                
                if pmset_result.returncode == 0:
                    output = pmset_result.stdout.lower()
                    if 'cpu_speed_limit' in output:
                        # System is thermally throttling
                        thermal_state = "hot"
                    elif cpu_temperature:
                        # Estimate thermal state based on temperature
                        if cpu_temperature < 60:
                            thermal_state = "normal"
                        elif cpu_temperature < 75:
                            thermal_state = "warm"
                        elif cpu_temperature < 90:
                            thermal_state = "hot"
                        else:
                            thermal_state = "critical"
                    else:
                        thermal_state = "normal"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Try to get power metrics using powermetrics (basic info)
            try:
                power_result = subprocess.run([
                    'pmset', '-g', 'ps'
                ], capture_output=True, text=True, timeout=5)
                
                if power_result.returncode == 0:
                    power_metrics = {
                        'power_source': 'unknown'
                    }
                    
                    output = power_result.stdout
                    if 'AC Power' in output:
                        power_metrics['power_source'] = 'AC'
                    elif 'Battery Power' in output:
                        power_metrics['power_source'] = 'Battery'
            except Exception:
                pass
            
            # If we have any thermal information, return it
            if cpu_temperature is not None or gpu_temperature is not None or fan_speeds or thermal_state != "unknown":
                return ThermalInfo(
                    cpu_temperature=cpu_temperature,
                    gpu_temperature=gpu_temperature,
                    fan_speeds=fan_speeds,
                    thermal_state=thermal_state,
                    power_metrics=power_metrics
                )
            else:
                # Return basic info even if we can't get detailed thermal data
                return ThermalInfo(
                    cpu_temperature=None,
                    gpu_temperature=None,
                    fan_speeds=[],
                    thermal_state="normal",  # Assume normal if no thermal issues detected
                    power_metrics=power_metrics
                )
                
        except Exception as e:
            print(f"Warning: Could not get thermal information: {e}")
            return ThermalInfo(
                cpu_temperature=None,
                gpu_temperature=None,
                fan_speeds=[],
                thermal_state="unknown",
                power_metrics=None
            )
    
    def get_system_summary(self) -> Dict[str, Any]:
        """
        Get a quick system summary synchronously
        
        Returns:
            Dictionary with basic system information
        """
        try:
            return {
                'platform': platform.system(),
                'platform_version': platform.release(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'disk_total_gb': round(psutil.disk_usage('/').total / (1024**3), 2),
                'python_version': platform.python_version()
            }
        except Exception as e:
            return {'error': f'Could not get system summary: {str(e)}'}
    
    def to_dict(self, system_status: SystemStatus) -> Dict[str, Any]:
        """
        Convert SystemStatus to dictionary for JSON serialization
        
        Args:
            system_status: SystemStatus object to convert
            
        Returns:
            Dictionary representation
        """
        data = asdict(system_status)
        # Convert datetime to ISO string
        data['timestamp'] = system_status.timestamp.isoformat()
        return data


class SystemMonitorError(Exception):
    """Custom exception for system monitoring errors"""
    pass


# Utility functions for macOS-specific features
def is_macos() -> bool:
    """Check if running on macOS"""
    return platform.system() == "Darwin"


def get_macos_version() -> Optional[str]:
    """Get macOS version string"""
    if not is_macos():
        return None
    try:
        return platform.mac_ver()[0]
    except Exception:
        return None


async def test_monitoring_callback(status: SystemStatus, alerts: List[Dict], changes: List[Dict]):
    """Test callback for real-time monitoring"""
    print(f"[{status.timestamp.strftime('%H:%M:%S')}] CPU: {status.cpu_percent:.1f}%, Memory: {status.memory_percent:.1f}%")
    
    if alerts:
        for alert in alerts:
            print(f"  🚨 ALERT: {alert['message']} (Severity: {alert['severity']})")
    
    if changes:
        for change in changes:
            print(f"  📊 CHANGE: {change['message']}")


async def test_performance():
    """Test performance of system monitoring"""
    monitor = SystemMonitor()
    
    print("--- Performance Testing ---")
    
    # Test single call performance
    import time
    start_time = time.time()
    status = await monitor.get_system_info()
    end_time = time.time()
    
    print(f"Single system info call: {(end_time - start_time) * 1000:.1f}ms")
    
    # Test memory usage
    import tracemalloc
    tracemalloc.start()
    
    # Perform multiple calls
    for _ in range(10):
        await monitor.get_system_info()
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"Memory usage - Current: {current / 1024 / 1024:.1f}MB, Peak: {peak / 1024 / 1024:.1f}MB")


async def test_realtime_monitoring_performance():
    """
    Test performance of real-time monitoring system
    Measures memory usage, callback performance, and system impact
    """
    print("--- Real-time Monitoring Performance Test ---")
    
    monitor = SystemMonitor(update_interval=1.0)
    performance_data = []
    
    async def performance_callback(status, alerts, changes):
        """Callback to measure performance metrics"""
        import time
        callback_start = time.time()
        
        # Simulate some processing
        await asyncio.sleep(0.01)  # 10ms processing time
        
        callback_end = time.time()
        performance_data.append({
            'timestamp': status.timestamp,
            'callback_time_ms': (callback_end - callback_start) * 1000,
            'cpu_percent': status.cpu_percent,
            'memory_percent': status.memory_percent,
            'alerts_count': len(alerts),
            'changes_count': len(changes)
        })
    
    # Add performance callback
    monitor.add_callback(performance_callback)
    
    # Start memory tracking
    import tracemalloc
    tracemalloc.start()
    
    # Start monitoring
    print("Starting real-time monitoring for 10 seconds...")
    await monitor.start_monitoring()
    
    # Let it run for 10 seconds
    await asyncio.sleep(10)
    
    # Stop monitoring
    await monitor.stop_monitoring()
    
    # Get memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Analyze performance data
    if performance_data:
        avg_callback_time = sum(d['callback_time_ms'] for d in performance_data) / len(performance_data)
        max_callback_time = max(d['callback_time_ms'] for d in performance_data)
        total_alerts = sum(d['alerts_count'] for d in performance_data)
        total_changes = sum(d['changes_count'] for d in performance_data)
        
        print(f"Performance Results:")
        print(f"  - Total monitoring cycles: {len(performance_data)}")
        print(f"  - Average callback time: {avg_callback_time:.2f}ms")
        print(f"  - Maximum callback time: {max_callback_time:.2f}ms")
        print(f"  - Total alerts generated: {total_alerts}")
        print(f"  - Total changes detected: {total_changes}")
        print(f"  - Memory usage - Current: {current / 1024 / 1024:.1f}MB, Peak: {peak / 1024 / 1024:.1f}MB")
        
        # Performance assertions
        assert avg_callback_time < 50.0, f"Average callback time too high: {avg_callback_time:.2f}ms"
        assert peak / 1024 / 1024 < 100.0, f"Peak memory usage too high: {peak / 1024 / 1024:.1f}MB"
        
        print("✅ Performance test passed!")
        return {
            'cycles': len(performance_data),
            'avg_callback_time_ms': avg_callback_time,
            'max_callback_time_ms': max_callback_time,
            'total_alerts': total_alerts,
            'total_changes': total_changes,
            'memory_current_mb': current / 1024 / 1024,
            'memory_peak_mb': peak / 1024 / 1024
        }
    else:
        print("❌ No performance data collected")
        return None


async def test_monitoring_stress():
    """
    Stress test for monitoring system with multiple callbacks and high frequency updates
    """
    print("--- Monitoring Stress Test ---")
    
    monitor = SystemMonitor(update_interval=0.5)  # High frequency updates
    callback_counters = {'callback1': 0, 'callback2': 0, 'callback3': 0}
    
    async def stress_callback_1(status, alerts, changes):
        callback_counters['callback1'] += 1
        # Simulate CPU-intensive processing
        sum(i * i for i in range(1000))
    
    async def stress_callback_2(status, alerts, changes):
        callback_counters['callback2'] += 1
        # Simulate I/O-like delay
        await asyncio.sleep(0.005)  # 5ms delay
    
    async def stress_callback_3(status, alerts, changes):
        callback_counters['callback3'] += 1
        # Simulate memory allocation
        temp_data = [i for i in range(1000)]
        del temp_data
    
    # Add multiple callbacks
    monitor.add_callback(stress_callback_1)
    monitor.add_callback(stress_callback_2)
    monitor.add_callback(stress_callback_3)
    
    # Set aggressive alert thresholds for testing
    monitor.set_alert_thresholds(cpu_percent=10.0, memory_percent=10.0, disk_percent=10.0)
    
    # Start memory tracking
    import tracemalloc
    tracemalloc.start()
    
    start_time = asyncio.get_event_loop().time()
    
    # Start monitoring
    print("Starting stress test for 5 seconds...")
    await monitor.start_monitoring()
    
    # Let it run for 5 seconds
    await asyncio.sleep(5)
    
    # Stop monitoring
    await monitor.stop_monitoring()
    
    end_time = asyncio.get_event_loop().time()
    
    # Get memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Analyze results
    total_time = end_time - start_time
    total_callbacks = sum(callback_counters.values())
    
    print(f"Stress Test Results:")
    print(f"  - Test duration: {total_time:.2f}s")
    print(f"  - Total callbacks executed: {total_callbacks}")
    print(f"  - Callback 1 (CPU): {callback_counters['callback1']}")
    print(f"  - Callback 2 (I/O): {callback_counters['callback2']}")
    print(f"  - Callback 3 (Memory): {callback_counters['callback3']}")
    print(f"  - Callbacks per second: {total_callbacks / total_time:.1f}")
    print(f"  - Memory usage - Current: {current / 1024 / 1024:.1f}MB, Peak: {peak / 1024 / 1024:.1f}MB")
    
    # Stress test assertions
    assert total_callbacks > 0, "No callbacks were executed"
    assert peak / 1024 / 1024 < 200.0, f"Peak memory usage too high under stress: {peak / 1024 / 1024:.1f}MB"
    
    print("✅ Stress test passed!")
    return {
        'duration_s': total_time,
        'total_callbacks': total_callbacks,
        'callbacks_per_second': total_callbacks / total_time,
        'memory_current_mb': current / 1024 / 1024,
        'memory_peak_mb': peak / 1024 / 1024
    }


async def test_system_monitor():
    """Test function for SystemMonitor"""
    monitor = SystemMonitor(update_interval=2.0)  # Faster updates for testing
    
    print("Testing SystemMonitor...")
    print(f"Platform: {platform.system()}")
    print(f"Is macOS: {is_macos()}")
    
    # Test system summary
    summary = monitor.get_system_summary()
    print(f"System Summary: {json.dumps(summary, indent=2)}")
    
    # Test full system info
    try:
        status = await monitor.get_system_info()
        print(f"CPU: {status.cpu_percent}%")
        print(f"Memory: {status.memory_percent}% ({status.memory_used / (1024**3):.1f}GB / {status.memory_total / (1024**3):.1f}GB)")
        print(f"Disk: {status.disk_percent}% ({status.disk_used / (1024**3):.1f}GB / {status.disk_total / (1024**3):.1f}GB)")
        print(f"Top processes: {len(status.top_processes)}")
        
        if status.top_processes:
            print("Top 3 processes by CPU:")
            for i, proc in enumerate(status.top_processes[:3]):
                print(f"  {i+1}. {proc.name} (PID: {proc.pid}) - CPU: {proc.cpu_percent}%, Memory: {proc.memory_percent:.1f}%")
        
        # Test new process monitoring features
        print("\n--- Testing Enhanced Process Monitoring ---")
        
        # Test CPU-based filtering
        cpu_processes = await monitor.get_processes_by_cpu(limit=3, min_cpu_percent=0.1)
        print(f"Top 3 CPU processes (>0.1%): {len(cpu_processes)}")
        for i, proc in enumerate(cpu_processes):
            print(f"  {i+1}. {proc.name} - CPU: {proc.cpu_percent}%")
        
        # Test memory-based filtering
        memory_processes = await monitor.get_processes_by_memory(limit=3, min_memory_mb=10.0)
        print(f"Top 3 Memory processes (>10MB): {len(memory_processes)}")
        for i, proc in enumerate(memory_processes):
            print(f"  {i+1}. {proc.name} - Memory: {proc.memory_rss / (1024*1024):.1f}MB")
        
        # Test name-based filtering
        chrome_processes = await monitor.get_processes_by_name('chrome', case_sensitive=False)
        print(f"Chrome processes found: {len(chrome_processes)}")
        for proc in chrome_processes[:3]:  # Show first 3
            print(f"  - {proc.name} (PID: {proc.pid}) - CPU: {proc.cpu_percent}%")
        
        # Test process details
        if status.top_processes:
            top_pid = status.top_processes[0].pid
            details = await monitor.get_process_details(top_pid)
            if details:
                print(f"Details for PID {top_pid}:")
                print(f"  Name: {details.name}")
                print(f"  Status: {details.status}")
                print(f"  Command: {' '.join(details.cmdline[:3])}...")  # Show first 3 args
        
        # Test performance
        await test_performance()
        
        # Test real-time monitoring
        print("\n--- Testing Real-time Monitoring ---")
        
        # Set alert thresholds for testing
        monitor.set_alert_thresholds(cpu_percent=50.0, memory_percent=70.0, disk_percent=80.0)
        
        # Add callback
        monitor.add_callback(test_monitoring_callback)
        
        # Start monitoring
        await monitor.start_monitoring()
        
        # Let it run for a few seconds
        print("Monitoring for 10 seconds...")
        await asyncio.sleep(10)
        
        # Get monitoring stats
        stats = await monitor.get_monitoring_stats()
        print(f"Monitoring stats: {json.dumps(stats, indent=2)}")
        
        # Stop monitoring
        await monitor.stop_monitoring()
        
    except Exception as e:
        print(f"Error testing system monitor: {e}")
        # Make sure to stop monitoring on error
        if monitor._is_monitoring:
            await monitor.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(test_system_monitor())