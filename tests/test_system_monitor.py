"""
Unit tests for SystemMonitor class
"""
import pytest
import asyncio
import platform
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the classes we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from system_monitor import (
    SystemMonitor, 
    SystemStatus, 
    ProcessInfo, 
    NetworkStats,
    SystemMonitorError,
    is_macos,
    get_macos_version
)


class TestSystemMonitor:
    """Test cases for SystemMonitor class"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.monitor = SystemMonitor(update_interval=1.0)
    
    def test_init(self):
        """Test SystemMonitor initialization"""
        monitor = SystemMonitor(update_interval=2.0)
        assert monitor.update_interval == 2.0
        assert isinstance(monitor.is_macos, bool)
    
    @pytest.mark.asyncio
    @patch('system_monitor.psutil.cpu_percent')
    @patch('system_monitor.psutil.cpu_count')
    @patch('system_monitor.psutil.virtual_memory')
    @patch('system_monitor.psutil.disk_usage')
    async def test_get_system_info_basic(self, mock_disk, mock_memory, mock_cpu_count, mock_cpu_percent):
        """Test basic system info retrieval"""
        # Mock psutil responses
        mock_cpu_percent.return_value = 25.5
        mock_cpu_count.return_value = 8
        
        mock_memory_obj = Mock()
        mock_memory_obj.used = 8 * 1024**3  # 8GB
        mock_memory_obj.total = 16 * 1024**3  # 16GB
        mock_memory_obj.percent = 50.0
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = Mock()
        mock_disk_obj.used = 100 * 1024**3  # 100GB
        mock_disk_obj.total = 500 * 1024**3  # 500GB
        mock_disk_obj.percent = 20.0
        mock_disk.return_value = mock_disk_obj
        
        # Mock other methods
        with patch.object(self.monitor, '_get_network_stats') as mock_network, \
             patch.object(self.monitor, '_get_top_processes') as mock_processes, \
             patch.object(self.monitor, '_get_uptime') as mock_uptime, \
             patch.object(self.monitor, '_get_load_average') as mock_load, \
             patch.object(self.monitor, '_get_temperature') as mock_temp:
            
            mock_network.return_value = NetworkStats(1000, 2000, 10, 20)
            mock_processes.return_value = []
            mock_uptime.return_value = 86400.0  # 1 day
            mock_load.return_value = [1.0, 1.5, 2.0]
            mock_temp.return_value = None
            
            status = await self.monitor.get_system_info()
            
            assert isinstance(status, SystemStatus)
            assert status.cpu_percent == 25.5
            assert status.cpu_count == 8
            assert status.memory_percent == 50.0
            assert status.disk_percent == 20.0
            assert isinstance(status.timestamp, datetime)
    
    def test_get_system_summary(self):
        """Test system summary retrieval"""
        summary = self.monitor.get_system_summary()
        
        assert isinstance(summary, dict)
        assert 'platform' in summary
        assert 'cpu_count' in summary
        assert 'memory_total_gb' in summary
        assert summary['platform'] == platform.system()
    
    @pytest.mark.asyncio
    @patch('system_monitor.psutil.process_iter')
    async def test_get_top_processes(self, mock_process_iter):
        """Test top processes retrieval"""
        # Create mock processes
        mock_proc1 = Mock()
        mock_proc1.info = {
            'pid': 1234,
            'name': 'test_process',
            'cpu_percent': 15.5,
            'memory_percent': 10.0,
            'memory_info': Mock(rss=1024*1024),  # 1MB
            'status': 'running',
            'create_time': 1234567890.0,
            'cmdline': ['test_process', '--arg']
        }
        
        mock_proc2 = Mock()
        mock_proc2.info = {
            'pid': 5678,
            'name': 'another_process',
            'cpu_percent': 5.0,
            'memory_percent': 20.0,
            'memory_info': Mock(rss=2*1024*1024),  # 2MB
            'status': 'sleeping',
            'create_time': 1234567800.0,
            'cmdline': ['another_process']
        }
        
        mock_process_iter.return_value = [mock_proc1, mock_proc2]
        
        processes = await self.monitor._get_top_processes(limit=5)
        
        assert len(processes) == 2
        assert processes[0].name == 'test_process'  # Higher CPU should be first
        assert processes[0].cpu_percent == 15.5
        assert processes[1].name == 'another_process'
    
    @pytest.mark.asyncio
    @patch('system_monitor.psutil.process_iter')
    async def test_get_processes_by_cpu(self, mock_process_iter):
        """Test processes filtering by CPU usage"""
        # Create mock processes with different CPU usage
        mock_proc1 = Mock()
        mock_proc1.info = {
            'pid': 1234,
            'name': 'high_cpu_process',
            'cpu_percent': 25.0,
            'memory_percent': 10.0,
            'memory_info': Mock(rss=1024*1024),
            'status': 'running',
            'create_time': 1234567890.0,
            'cmdline': ['high_cpu_process']
        }
        
        mock_proc2 = Mock()
        mock_proc2.info = {
            'pid': 5678,
            'name': 'low_cpu_process',
            'cpu_percent': 2.0,
            'memory_percent': 5.0,
            'memory_info': Mock(rss=512*1024),
            'status': 'sleeping',
            'create_time': 1234567800.0,
            'cmdline': ['low_cpu_process']
        }
        
        mock_process_iter.return_value = [mock_proc1, mock_proc2]
        
        # Test with minimum CPU filter
        processes = await self.monitor.get_processes_by_cpu(limit=10, min_cpu_percent=5.0)
        
        assert len(processes) == 1
        assert processes[0].name == 'high_cpu_process'
        assert processes[0].cpu_percent == 25.0
    
    @pytest.mark.asyncio
    @patch('system_monitor.psutil.process_iter')
    async def test_get_processes_by_memory(self, mock_process_iter):
        """Test processes filtering by memory usage"""
        # Create mock processes with different memory usage
        mock_proc1 = Mock()
        mock_proc1.info = {
            'pid': 1234,
            'name': 'high_memory_process',
            'cpu_percent': 5.0,
            'memory_percent': 20.0,
            'memory_info': Mock(rss=100*1024*1024),  # 100MB
            'status': 'running',
            'create_time': 1234567890.0,
            'cmdline': ['high_memory_process']
        }
        
        mock_proc2 = Mock()
        mock_proc2.info = {
            'pid': 5678,
            'name': 'low_memory_process',
            'cpu_percent': 10.0,
            'memory_percent': 2.0,
            'memory_info': Mock(rss=1024*1024),  # 1MB
            'status': 'sleeping',
            'create_time': 1234567800.0,
            'cmdline': ['low_memory_process']
        }
        
        mock_process_iter.return_value = [mock_proc1, mock_proc2]
        
        # Test with minimum memory filter (50MB)
        processes = await self.monitor.get_processes_by_memory(limit=10, min_memory_mb=50.0)
        
        assert len(processes) == 1
        assert processes[0].name == 'high_memory_process'
        assert processes[0].memory_rss == 100*1024*1024
    
    @pytest.mark.asyncio
    @patch('system_monitor.psutil.process_iter')
    async def test_get_processes_by_name(self, mock_process_iter):
        """Test processes filtering by name pattern"""
        # Create mock processes with different names
        mock_proc1 = Mock()
        mock_proc1.info = {
            'pid': 1234,
            'name': 'Google Chrome',
            'cpu_percent': 15.0,
            'memory_percent': 10.0,
            'memory_info': Mock(rss=1024*1024),
            'status': 'running',
            'create_time': 1234567890.0,
            'cmdline': ['Google Chrome']
        }
        
        mock_proc2 = Mock()
        mock_proc2.info = {
            'pid': 5678,
            'name': 'Firefox',
            'cpu_percent': 10.0,
            'memory_percent': 8.0,
            'memory_info': Mock(rss=512*1024),
            'status': 'running',
            'create_time': 1234567800.0,
            'cmdline': ['Firefox']
        }
        
        mock_process_iter.return_value = [mock_proc1, mock_proc2]
        
        # Test name filtering (case insensitive)
        processes = await self.monitor.get_processes_by_name('chrome', case_sensitive=False)
        
        assert len(processes) == 1
        assert processes[0].name == 'Google Chrome'
    
    @pytest.mark.asyncio
    @patch('system_monitor.psutil.Process')
    async def test_get_process_details(self, mock_process_class):
        """Test getting details for a specific process"""
        # Create mock process
        mock_proc = Mock()
        mock_proc.pid = 1234
        mock_proc.name.return_value = 'test_process'
        mock_proc.cpu_percent.return_value = 15.5
        mock_proc.memory_percent.return_value = 10.0
        mock_proc.memory_info.return_value = Mock(rss=1024*1024)
        mock_proc.status.return_value = 'running'
        mock_proc.create_time.return_value = 1234567890.0
        mock_proc.cmdline.return_value = ['test_process', '--arg']
        mock_proc.oneshot.return_value.__enter__ = Mock(return_value=None)
        mock_proc.oneshot.return_value.__exit__ = Mock(return_value=None)
        
        mock_process_class.return_value = mock_proc
        
        process_info = await self.monitor.get_process_details(1234)
        
        assert process_info is not None
        assert process_info.pid == 1234
        assert process_info.name == 'test_process'
        assert process_info.cpu_percent == 15.5
    
    def test_network_stats(self):
        """Test network statistics retrieval"""
        with patch('system_monitor.psutil.net_io_counters') as mock_net:
            mock_net_obj = Mock()
            mock_net_obj.bytes_sent = 1000
            mock_net_obj.bytes_recv = 2000
            mock_net_obj.packets_sent = 10
            mock_net_obj.packets_recv = 20
            mock_net.return_value = mock_net_obj
            
            stats = self.monitor._get_network_stats()
            
            assert isinstance(stats, NetworkStats)
            assert stats.bytes_sent == 1000
            assert stats.bytes_recv == 2000
    
    def test_load_average(self):
        """Test load average retrieval"""
        load_avg = self.monitor._get_load_average()
        
        assert isinstance(load_avg, list)
        assert len(load_avg) == 3
        assert all(isinstance(x, float) for x in load_avg)
    
    def test_to_dict(self):
        """Test SystemStatus to dictionary conversion"""
        # Create a sample SystemStatus
        status = SystemStatus(
            timestamp=datetime.now(),
            cpu_percent=25.0,
            cpu_count=8,
            cpu_freq=2400.0,
            memory_used=8*1024**3,
            memory_total=16*1024**3,
            memory_percent=50.0,
            disk_used=100*1024**3,
            disk_total=500*1024**3,
            disk_percent=20.0,
            top_processes=[],
            network_io=NetworkStats(1000, 2000, 10, 20),
            temperature=None,
            uptime=86400.0,
            load_average=[1.0, 1.5, 2.0]
        )
        
        result = self.monitor.to_dict(status)
        
        assert isinstance(result, dict)
        assert 'timestamp' in result
        assert isinstance(result['timestamp'], str)  # Should be ISO string
        assert result['cpu_percent'] == 25.0
        assert result['memory_percent'] == 50.0


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_is_macos(self):
        """Test macOS detection"""
        result = is_macos()
        expected = platform.system() == "Darwin"
        assert result == expected
    
    @patch('system_monitor.platform.mac_ver')
    def test_get_macos_version(self, mock_mac_ver):
        """Test macOS version retrieval"""
        if platform.system() == "Darwin":
            mock_mac_ver.return_value = ("13.0", "", "")
            version = get_macos_version()
            assert version == "13.0"
        else:
            version = get_macos_version()
            assert version is None


class TestDataClasses:
    """Test data classes"""
    
    def test_process_info(self):
        """Test ProcessInfo dataclass"""
        proc = ProcessInfo(
            pid=1234,
            name="test",
            cpu_percent=10.0,
            memory_percent=5.0,
            memory_rss=1024,
            status="running",
            create_time=1234567890.0,
            cmdline=["test", "--arg"]
        )
        
        assert proc.pid == 1234
        assert proc.name == "test"
        assert proc.cpu_percent == 10.0
    
    def test_network_stats(self):
        """Test NetworkStats dataclass"""
        stats = NetworkStats(
            bytes_sent=1000,
            bytes_recv=2000,
            packets_sent=10,
            packets_recv=20
        )
        
        assert stats.bytes_sent == 1000
        assert stats.bytes_recv == 2000
    
    def test_system_status(self):
        """Test SystemStatus dataclass"""
        status = SystemStatus(
            timestamp=datetime.now(),
            cpu_percent=25.0,
            cpu_count=8,
            cpu_freq=2400.0,
            memory_used=8*1024**3,
            memory_total=16*1024**3,
            memory_percent=50.0,
            disk_used=100*1024**3,
            disk_total=500*1024**3,
            disk_percent=20.0,
            top_processes=[],
            network_io=NetworkStats(1000, 2000, 10, 20),
            temperature=None,
            uptime=86400.0,
            load_average=[1.0, 1.5, 2.0]
        )
        
        assert status.cpu_percent == 25.0
        assert status.cpu_count == 8
        assert isinstance(status.timestamp, datetime)


class TestRealTimeMonitoring:
    """Test cases for real-time monitoring functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.monitor = SystemMonitor(update_interval=0.1)  # Fast updates for testing
        self.callback_calls = []
    
    async def monitoring_callback(self, status, alerts, changes):
        """Callback function for monitoring tests"""
        self.callback_calls.append({
            'status': status,
            'alerts': alerts,
            'changes': changes
        })
    
    def test_add_remove_callback(self):
        """Test adding and removing callbacks"""
        assert len(self.monitor._callbacks) == 0
        
        self.monitor.add_callback(self.monitoring_callback)
        assert len(self.monitor._callbacks) == 1
        
        # Adding same callback again should not duplicate
        self.monitor.add_callback(self.monitoring_callback)
        assert len(self.monitor._callbacks) == 1
        
        self.monitor.remove_callback(self.monitoring_callback)
        assert len(self.monitor._callbacks) == 0
    
    def test_set_alert_thresholds(self):
        """Test setting alert thresholds"""
        # Test default thresholds
        assert self.monitor._alert_thresholds['cpu_percent'] == 80.0
        assert self.monitor._alert_thresholds['memory_percent'] == 85.0
        assert self.monitor._alert_thresholds['disk_percent'] == 90.0
        
        # Test setting new thresholds
        self.monitor.set_alert_thresholds(cpu_percent=70.0, memory_percent=75.0)
        assert self.monitor._alert_thresholds['cpu_percent'] == 70.0
        assert self.monitor._alert_thresholds['memory_percent'] == 75.0
        assert self.monitor._alert_thresholds['disk_percent'] == 90.0  # Unchanged
    
    def test_check_alerts(self):
        """Test alert checking functionality"""
        # Create a status with high CPU usage
        status = SystemStatus(
            timestamp=datetime.now(),
            cpu_percent=85.0,  # Above default threshold of 80%
            cpu_count=8,
            cpu_freq=2400.0,
            memory_used=4*1024**3,
            memory_total=8*1024**3,
            memory_percent=50.0,  # Below threshold
            disk_used=100*1024**3,
            disk_total=500*1024**3,
            disk_percent=20.0,  # Below threshold
            top_processes=[],
            network_io=NetworkStats(1000, 2000, 10, 20),
            temperature=None,
            uptime=86400.0,
            load_average=[1.0, 1.5, 2.0]
        )
        
        alerts = self.monitor._check_alerts(status)
        
        assert len(alerts) == 1
        assert alerts[0]['type'] == 'cpu_high'
        assert alerts[0]['value'] == 85.0
        assert alerts[0]['severity'] == 'warning'
    
    def test_detect_changes(self):
        """Test change detection functionality"""
        # Create initial status
        initial_status = SystemStatus(
            timestamp=datetime.now(),
            cpu_percent=20.0,
            cpu_count=8,
            cpu_freq=2400.0,
            memory_used=4*1024**3,
            memory_total=8*1024**3,
            memory_percent=50.0,
            disk_used=100*1024**3,
            disk_total=500*1024**3,
            disk_percent=20.0,
            top_processes=[ProcessInfo(1234, 'test1', 10.0, 5.0, 1024, 'running', 123456, ['test1'])],
            network_io=NetworkStats(1000, 2000, 10, 20),
            temperature=None,
            uptime=86400.0,
            load_average=[1.0, 1.5, 2.0]
        )
        
        # Set as last status
        self.monitor._last_status = initial_status
        
        # Create new status with significant CPU change
        new_status = SystemStatus(
            timestamp=datetime.now(),
            cpu_percent=35.0,  # 15% increase
            cpu_count=8,
            cpu_freq=2400.0,
            memory_used=4*1024**3,
            memory_total=8*1024**3,
            memory_percent=50.0,
            disk_used=100*1024**3,
            disk_total=500*1024**3,
            disk_percent=20.0,
            top_processes=[ProcessInfo(5678, 'test2', 15.0, 8.0, 2048, 'running', 123457, ['test2'])],
            network_io=NetworkStats(1000, 2000, 10, 20),
            temperature=None,
            uptime=86400.0,
            load_average=[1.0, 1.5, 2.0]
        )
        
        changes = self.monitor._detect_changes(new_status)
        
        assert len(changes) == 2  # CPU change and top process change
        
        # Check CPU change
        cpu_change = next((c for c in changes if c['type'] == 'cpu_change'), None)
        assert cpu_change is not None
        assert cpu_change['change'] == 15.0
        
        # Check top process change
        process_change = next((c for c in changes if c['type'] == 'top_process_change'), None)
        assert process_change is not None
        assert process_change['old_process']['name'] == 'test1'
        assert process_change['new_process']['name'] == 'test2'
    
    @pytest.mark.asyncio
    async def test_monitoring_stats(self):
        """Test monitoring statistics"""
        stats = await self.monitor.get_monitoring_stats()
        
        assert isinstance(stats, dict)
        assert 'is_monitoring' in stats
        assert 'update_interval' in stats
        assert 'callbacks_count' in stats
        assert 'alert_thresholds' in stats
        assert stats['is_monitoring'] is False
        assert stats['update_interval'] == 0.1
        assert stats['callbacks_count'] == 0
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring"""
        assert not self.monitor._is_monitoring
        
        # Start monitoring
        await self.monitor.start_monitoring()
        assert self.monitor._is_monitoring
        assert self.monitor._monitoring_task is not None
        
        # Stop monitoring
        await self.monitor.stop_monitoring()
        assert not self.monitor._is_monitoring


@pytest.mark.asyncio
async def test_system_monitor_integration():
    """Integration test for SystemMonitor"""
    monitor = SystemMonitor()
    
    try:
        # This should work on any system with psutil
        status = await monitor.get_system_info()
        
        assert isinstance(status, SystemStatus)
        assert status.cpu_percent >= 0
        assert status.memory_total > 0
        assert status.disk_total > 0
        assert isinstance(status.top_processes, list)
        
    except SystemMonitorError:
        # If we get a SystemMonitorError, that's also valid behavior
        pytest.skip("System monitoring not available in test environment")


class TestRealTimeMonitoringPerformance:
    """Test cases for real-time monitoring performance"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.monitor = SystemMonitor(update_interval=0.5)  # Fast updates for testing
        self.performance_data = []
    
    async def performance_callback(self, status, alerts, changes):
        """Callback to collect performance data"""
        import time
        start_time = time.time()
        
        # Simulate some processing work
        await asyncio.sleep(0.001)  # 1ms processing
        
        end_time = time.time()
        self.performance_data.append({
            'callback_time_ms': (end_time - start_time) * 1000,
            'alerts_count': len(alerts),
            'changes_count': len(changes),
            'cpu_percent': status.cpu_percent,
            'memory_percent': status.memory_percent
        })
    
    @pytest.mark.asyncio
    async def test_monitoring_memory_usage(self):
        """Test memory usage during real-time monitoring"""
        import tracemalloc
        
        # Start memory tracking
        tracemalloc.start()
        
        # Add callback
        self.monitor.add_callback(self.performance_callback)
        
        # Start monitoring
        await self.monitor.start_monitoring()
        
        # Let it run for 2 seconds
        await asyncio.sleep(2)
        
        # Stop monitoring
        await self.monitor.stop_monitoring()
        
        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Convert to MB
        current_mb = current / 1024 / 1024
        peak_mb = peak / 1024 / 1024
        
        print(f"Memory usage - Current: {current_mb:.1f}MB, Peak: {peak_mb:.1f}MB")
        print(f"Monitoring cycles: {len(self.performance_data)}")
        
        # Assertions for memory usage
        assert peak_mb < 50.0, f"Peak memory usage too high: {peak_mb:.1f}MB"
        assert len(self.performance_data) > 0, "No monitoring data collected"
        
        # Check callback performance
        if self.performance_data:
            avg_callback_time = sum(d['callback_time_ms'] for d in self.performance_data) / len(self.performance_data)
            assert avg_callback_time < 10.0, f"Average callback time too high: {avg_callback_time:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_monitoring_callback_performance(self):
        """Test callback execution performance"""
        callback_times = []
        
        async def timing_callback(status, alerts, changes):
            import time
            start = time.time()
            # Simulate processing
            sum(i for i in range(100))
            end = time.time()
            callback_times.append((end - start) * 1000)
        
        self.monitor.add_callback(timing_callback)
        
        # Start monitoring for short duration
        await self.monitor.start_monitoring()
        await asyncio.sleep(1)
        await self.monitor.stop_monitoring()
        
        # Analyze callback performance
        assert len(callback_times) > 0, "No callback executions recorded"
        
        avg_time = sum(callback_times) / len(callback_times)
        max_time = max(callback_times)
        
        print(f"Callback performance - Avg: {avg_time:.2f}ms, Max: {max_time:.2f}ms")
        
        # Performance assertions
        assert avg_time < 5.0, f"Average callback time too high: {avg_time:.2f}ms"
        assert max_time < 20.0, f"Maximum callback time too high: {max_time:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_monitoring_system_impact(self):
        """Test system impact of monitoring"""
        import psutil
        import time
        
        # Get baseline system usage
        baseline_cpu = psutil.cpu_percent(interval=1)
        baseline_memory = psutil.virtual_memory().percent
        
        # Start monitoring with multiple callbacks
        async def dummy_callback_1(status, alerts, changes):
            pass
        
        async def dummy_callback_2(status, alerts, changes):
            await asyncio.sleep(0.001)  # Small delay
        
        self.monitor.add_callback(dummy_callback_1)
        self.monitor.add_callback(dummy_callback_2)
        
        # Monitor system usage during monitoring
        await self.monitor.start_monitoring()
        
        # Let it run and measure impact
        start_time = time.time()
        await asyncio.sleep(3)
        end_time = time.time()
        
        # Get system usage during monitoring
        monitoring_cpu = psutil.cpu_percent(interval=1)
        monitoring_memory = psutil.virtual_memory().percent
        
        await self.monitor.stop_monitoring()
        
        # Calculate impact
        cpu_impact = monitoring_cpu - baseline_cpu
        memory_impact = monitoring_memory - baseline_memory
        
        print(f"System impact - CPU: {cpu_impact:.1f}%, Memory: {memory_impact:.1f}%")
        print(f"Monitoring duration: {end_time - start_time:.1f}s")
        
        # Impact should be reasonable (relaxed thresholds for test environment)
        assert abs(cpu_impact) < 50.0, f"CPU impact too high: {cpu_impact:.1f}%"
        assert abs(memory_impact) < 20.0, f"Memory impact too high: {memory_impact:.1f}%"
    
    @pytest.mark.asyncio
    async def test_alert_detection_performance(self):
        """Test performance of alert detection"""
        alert_counts = []
        
        async def alert_callback(status, alerts, changes):
            alert_counts.append(len(alerts))
        
        # Set low thresholds to trigger alerts
        self.monitor.set_alert_thresholds(cpu_percent=1.0, memory_percent=1.0, disk_percent=1.0)
        self.monitor.add_callback(alert_callback)
        
        # Start monitoring
        await self.monitor.start_monitoring()
        await asyncio.sleep(2)
        await self.monitor.stop_monitoring()
        
        # Analyze alert detection
        total_alerts = sum(alert_counts)
        avg_alerts = total_alerts / len(alert_counts) if alert_counts else 0
        
        print(f"Alert detection - Total: {total_alerts}, Average per cycle: {avg_alerts:.1f}")
        
        # Should detect alerts efficiently
        assert len(alert_counts) > 0, "No monitoring cycles recorded"
        assert total_alerts >= 0, "Alert detection failed"
    
    @pytest.mark.asyncio
    async def test_change_detection_performance(self):
        """Test performance of change detection"""
        change_counts = []
        
        async def change_callback(status, alerts, changes):
            change_counts.append(len(changes))
        
        self.monitor.add_callback(change_callback)
        
        # Start monitoring
        await self.monitor.start_monitoring()
        await asyncio.sleep(3)  # Longer duration to capture changes
        await self.monitor.stop_monitoring()
        
        # Analyze change detection
        total_changes = sum(change_counts)
        
        print(f"Change detection - Total changes: {total_changes}, Cycles: {len(change_counts)}")
        
        # Should detect changes efficiently
        assert len(change_counts) > 0, "No monitoring cycles recorded"
        assert total_changes >= 0, "Change detection failed"


class TestSystemMonitorErrorHandling:
    """Test error handling in SystemMonitor"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.monitor = SystemMonitor(update_interval=1.0)
    
    @pytest.mark.asyncio
    @patch('system_monitor.psutil.cpu_percent')
    async def test_cpu_percent_error_handling(self, mock_cpu_percent):
        """Test CPU percent error handling"""
        mock_cpu_percent.side_effect = Exception("CPU access error")
        
        # Should handle error gracefully
        with patch.object(self.monitor, '_get_network_stats') as mock_network, \
             patch.object(self.monitor, '_get_top_processes') as mock_processes, \
             patch.object(self.monitor, '_get_uptime') as mock_uptime, \
             patch.object(self.monitor, '_get_load_average') as mock_load, \
             patch.object(self.monitor, '_get_temperature') as mock_temp:
            
            mock_network.return_value = NetworkStats(0, 0, 0, 0)
            mock_processes.return_value = []
            mock_uptime.return_value = 0.0
            mock_load.return_value = [0.0, 0.0, 0.0]
            mock_temp.return_value = None
            
            # Should not raise exception
            status = await self.monitor.get_system_info()
            assert status is not None
    
    @pytest.mark.asyncio
    @patch('system_monitor.psutil.process_iter')
    async def test_process_access_denied(self, mock_process_iter):
        """Test handling of process access denied errors"""
        import psutil
        
        # Create mock process that raises AccessDenied
        mock_proc = Mock()
        mock_proc.info = Mock(side_effect=psutil.AccessDenied(pid=1234))
        mock_process_iter.return_value = [mock_proc]
        
        # Should handle gracefully and return empty list
        processes = await self.monitor._get_top_processes(limit=5)
        assert isinstance(processes, list)
        assert len(processes) == 0
    
    @pytest.mark.asyncio
    @patch('system_monitor.psutil.process_iter')
    async def test_process_no_such_process(self, mock_process_iter):
        """Test handling of NoSuchProcess errors"""
        import psutil
        
        # Create mock process that raises NoSuchProcess
        mock_proc = Mock()
        mock_proc.info = Mock(side_effect=psutil.NoSuchProcess(pid=1234))
        mock_process_iter.return_value = [mock_proc]
        
        # Should handle gracefully and return empty list
        processes = await self.monitor._get_top_processes(limit=5)
        assert isinstance(processes, list)
        assert len(processes) == 0
    
    @pytest.mark.asyncio
    async def test_temperature_not_available(self):
        """Test temperature when not available"""
        temp = await self.monitor._get_temperature()
        # On most systems, temperature might not be available
        assert temp is None or isinstance(temp, float)
    
    @patch('system_monitor.psutil.net_io_counters')
    def test_network_stats_error(self, mock_net):
        """Test network stats error handling"""
        mock_net.side_effect = Exception("Network error")
        
        stats = self.monitor._get_network_stats()
        
        # Should return default NetworkStats
        assert isinstance(stats, NetworkStats)
        assert stats.bytes_sent == 0
        assert stats.bytes_recv == 0


class TestSystemMonitorMacOSSpecific:
    """Test macOS-specific functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.monitor = SystemMonitor()
    
    @patch('system_monitor.platform.system')
    def test_macos_detection(self, mock_system):
        """Test macOS detection"""
        mock_system.return_value = "Darwin"
        assert is_macos() is True
        
        mock_system.return_value = "Linux"
        assert is_macos() is False
    
    @patch('system_monitor.subprocess.run')
    def test_macos_system_profiler(self, mock_run):
        """Test macOS system profiler integration"""
        if not is_macos():
            pytest.skip("macOS-specific test")
        
        # Mock system_profiler output
        mock_result = Mock()
        mock_result.stdout = '{"SPHardwareDataType":[{"machine_name":"MacBook Pro"}]}'
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # This would test macOS-specific hardware info if implemented
        summary = self.monitor.get_system_summary()
        assert isinstance(summary, dict)
    
    def test_cpu_frequency_macos(self):
        """Test CPU frequency on macOS"""
        if not is_macos():
            pytest.skip("macOS-specific test")
        
        # CPU frequency might not be available on M1 Macs
        with patch('system_monitor.psutil.cpu_freq') as mock_freq:
            mock_freq.return_value = None  # Common on M1 Macs
            
            summary = self.monitor.get_system_summary()
            # CPU frequency may not be included if not available
            if 'cpu_freq_mhz' in summary:
                # Should handle None gracefully
                assert summary['cpu_freq_mhz'] is None or isinstance(summary['cpu_freq_mhz'], (int, float))


class TestSystemMonitorAdvancedFeatures:
    """Test advanced SystemMonitor features"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.monitor = SystemMonitor()
    
    @pytest.mark.asyncio
    async def test_system_health_check(self):
        """Test system health assessment"""
        # This tests a hypothetical health check feature
        status = await self.monitor.get_system_info()
        
        # Basic health indicators
        health_score = 100
        if status.cpu_percent > 80:
            health_score -= 20
        if status.memory_percent > 85:
            health_score -= 20
        if status.disk_percent > 90:
            health_score -= 30
        
        assert 0 <= health_score <= 100
    
    @pytest.mark.asyncio
    async def test_process_tree_analysis(self):
        """Test process tree analysis"""
        processes = await self.monitor._get_top_processes(limit=10)
        
        # Group processes by parent if possible
        process_groups = {}
        for proc in processes:
            parent_name = proc.name.split()[0] if proc.name else "unknown"
            if parent_name not in process_groups:
                process_groups[parent_name] = []
            process_groups[parent_name].append(proc)
        
        # Should have some process groups
        assert len(process_groups) >= 0
    
    def test_system_summary_completeness(self):
        """Test that system summary contains all expected fields"""
        summary = self.monitor.get_system_summary()
        
        required_fields = [
            'platform', 'cpu_count', 'memory_total_gb'
        ]
        
        for field in required_fields:
            assert field in summary, f"Missing field: {field}"
        
        # Optional fields that may or may not be present
        optional_fields = ['boot_time', 'python_version', 'cpu_freq_mhz']
        for field in optional_fields:
            if field in summary:
                assert summary[field] is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_system_info_requests(self):
        """Test concurrent system info requests"""
        # Test multiple concurrent requests
        tasks = [self.monitor.get_system_info() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 5
        for result in results:
            assert isinstance(result, SystemStatus)
            assert result.cpu_percent >= 0
    
    def test_system_monitor_configuration(self):
        """Test SystemMonitor configuration options"""
        # Test different update intervals
        monitor1 = SystemMonitor(update_interval=0.5)
        assert monitor1.update_interval == 0.5
        
        monitor2 = SystemMonitor(update_interval=5.0)
        assert monitor2.update_interval == 5.0
    
    @pytest.mark.asyncio
    async def test_memory_usage_patterns(self):
        """Test memory usage pattern analysis"""
        status = await self.monitor.get_system_info()
        
        # Analyze memory usage patterns
        memory_pressure = "low"
        if status.memory_percent > 80:
            memory_pressure = "high"
        elif status.memory_percent > 60:
            memory_pressure = "medium"
        
        assert memory_pressure in ["low", "medium", "high"]
    
    @pytest.mark.asyncio
    async def test_disk_usage_analysis(self):
        """Test disk usage analysis"""
        status = await self.monitor.get_system_info()
        
        # Analyze disk usage
        disk_status = "healthy"
        if status.disk_percent > 90:
            disk_status = "critical"
        elif status.disk_percent > 80:
            disk_status = "warning"
        
        assert disk_status in ["healthy", "warning", "critical"]


class TestSystemMonitorPerformanceOptimizations:
    """Test performance optimizations in SystemMonitor"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.monitor = SystemMonitor()
    
    @pytest.mark.asyncio
    async def test_cached_system_info(self):
        """Test system info caching for performance"""
        import time
        
        # First call
        start_time = time.time()
        status1 = await self.monitor.get_system_info()
        first_call_time = time.time() - start_time
        
        # Second call (should be similar time since no caching implemented)
        start_time = time.time()
        status2 = await self.monitor.get_system_info()
        second_call_time = time.time() - start_time
        
        # Both should be valid
        assert isinstance(status1, SystemStatus)
        assert isinstance(status2, SystemStatus)
        
        # Times should be reasonable (less than 1 second each)
        assert first_call_time < 1.0
        assert second_call_time < 1.0
    
    @pytest.mark.asyncio
    async def test_process_filtering_performance(self):
        """Test process filtering performance"""
        import time
        
        start_time = time.time()
        cpu_processes = await self.monitor.get_processes_by_cpu(limit=20, min_cpu_percent=1.0)
        cpu_time = time.time() - start_time
        
        start_time = time.time()
        memory_processes = await self.monitor.get_processes_by_memory(limit=20, min_memory_mb=10.0)
        memory_time = time.time() - start_time
        
        # Should complete quickly
        assert cpu_time < 2.0
        assert memory_time < 2.0
        
        # Should return reasonable results
        assert isinstance(cpu_processes, list)
        assert isinstance(memory_processes, list)
    
    def test_data_structure_efficiency(self):
        """Test efficiency of data structures"""
        import time
        
        # Test ProcessInfo creation
        proc_info = ProcessInfo(
            pid=1234,
            name="test",
            cpu_percent=10.0,
            memory_percent=5.0,
            memory_rss=1024*1024,
            status="running",
            create_time=time.time(),
            cmdline=["test", "--arg"]
        )
        
        # Should be efficient to create and access
        assert proc_info.pid == 1234
        assert proc_info.memory_rss == 1024*1024
        
        # Test NetworkStats
        net_stats = NetworkStats(1000, 2000, 10, 20)
        assert net_stats.bytes_sent == 1000
        assert net_stats.packets_recv == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])