"""
Alarm Manager for TwinCAT HMI
Handles alarm detection, state management, and acknowledgment
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlarmState(Enum):
    """Alarm state enumeration"""
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    CLEARED = "CLEARED"


class AlarmType(Enum):
    """Alarm type enumeration"""
    HIGH_HIGH = "HighHigh"
    HIGH = "High"
    LOW = "Low"
    LOW_LOW = "LowLow"
    DIGITAL = "Digital"


class AlarmPriority(Enum):
    """Alarm priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class Alarm:
    """Individual alarm instance"""
    
    def __init__(self, symbol_name: str, alarm_type: AlarmType, priority: AlarmPriority,
                 value: float, limit: float, message: str):
        self.id = f"{symbol_name}_{alarm_type.value}_{datetime.now().timestamp()}"
        self.symbol_name = symbol_name
        self.alarm_type = alarm_type
        self.priority = priority
        self.value = value
        self.limit = limit
        self.message = message
        self.state = AlarmState.ACTIVE
        self.timestamp = datetime.now()
        self.acknowledged_time = None
        self.acknowledged_by = None
        self.cleared_time = None
    
    def acknowledge(self, user: str = "User"):
        """Acknowledge the alarm"""
        if self.state == AlarmState.ACTIVE:
            self.state = AlarmState.ACKNOWLEDGED
            self.acknowledged_time = datetime.now()
            self.acknowledged_by = user
            logger.info(f"Alarm acknowledged: {self.message}")
    
    def clear(self):
        """Clear the alarm"""
        self.state = AlarmState.CLEARED
        self.cleared_time = datetime.now()
        logger.info(f"Alarm cleared: {self.message}")
    
    def is_active(self) -> bool:
        """Check if alarm is active"""
        return self.state in [AlarmState.ACTIVE, AlarmState.ACKNOWLEDGED]
    
    def to_dict(self) -> Dict:
        """Convert alarm to dictionary"""
        return {
            'id': self.id,
            'symbol_name': self.symbol_name,
            'alarm_type': self.alarm_type.value,
            'priority': self.priority.value,
            'value': self.value,
            'limit': self.limit,
            'message': self.message,
            'state': self.state.value,
            'timestamp': self.timestamp.isoformat(),
            'acknowledged_time': self.acknowledged_time.isoformat() if self.acknowledged_time else None,
            'acknowledged_by': self.acknowledged_by,
            'cleared_time': self.cleared_time.isoformat() if self.cleared_time else None
        }


class AlarmManager:
    """Manager for all alarm detection and handling"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.alarms_enabled = config.get('alarms', {}).get('enabled', True)
        self.sound_enabled = config.get('alarms', {}).get('sound_enabled', True)
        self.auto_acknowledge = config.get('alarms', {}).get('auto_acknowledge', False)
        self.hysteresis_percent = config.get('alarms', {}).get('hysteresis_percent', 2.0)
        
        self.active_alarms: Dict[str, Alarm] = {}  # Key: symbol_name_alarmtype
        self.alarm_history: List[Alarm] = []
        self.callbacks: List[Callable] = []
        
        # Track alarm states for hysteresis
        self.alarm_states: Dict[str, bool] = {}
        
        logger.info(f"AlarmManager initialized (enabled={self.alarms_enabled})")
    
    def register_callback(self, callback: Callable):
        """
        Register callback function to be called when alarms change
        
        Args:
            callback: Function to call with alarm list
        """
        self.callbacks.append(callback)
    
    def check_alarms(self, symbol_values: Dict[str, float], symbol_configs: List[Dict]):
        """
        Check all symbols for alarm conditions
        
        Args:
            symbol_values: Dictionary of symbol_name: current_value
            symbol_configs: List of parsed symbol configurations
        """
        if not self.alarms_enabled:
            return
        
        # Check each symbol that has alarm configuration
        for symbol_config in symbol_configs:
            symbol_name = symbol_config['name']
            
            # Skip if no current value
            if symbol_name not in symbol_values:
                continue
            
            current_value = symbol_values[symbol_name]
            
            # Check for analog alarms
            if 'alarm_config' in symbol_config:
                alarm_config = symbol_config['alarm_config']
                if alarm_config.get('enabled', False):
                    self._check_analog_alarms(symbol_name, current_value, alarm_config, symbol_config)
            
            # Check for digital alarms
            if symbol_config.get('category') == 'alarm':
                self._check_digital_alarm(symbol_name, current_value, symbol_config)
    
    def _check_analog_alarms(self, symbol_name: str, value: float, 
                            alarm_config: Dict, symbol_config: Dict):
        """
        Check analog value against alarm limits with hysteresis
        
        Args:
            symbol_name: Symbol name
            value: Current value
            alarm_config: Alarm configuration with limits
            symbol_config: Full symbol configuration
        """
        limits = alarm_config.get('limits', {})
        priority = AlarmPriority(alarm_config.get('priority', 2))
        unit = symbol_config.get('unit', '')
        
        # Check each alarm type
        self._check_limit(symbol_name, value, limits, 'high_high', 
                         AlarmType.HIGH_HIGH, priority, unit, operator='>=')
        self._check_limit(symbol_name, value, limits, 'high', 
                         AlarmType.HIGH, priority, unit, operator='>=')
        self._check_limit(symbol_name, value, limits, 'low', 
                         AlarmType.LOW, priority, unit, operator='<=')
        self._check_limit(symbol_name, value, limits, 'low_low', 
                         AlarmType.LOW_LOW, priority, unit, operator='<=')
    
    def _check_limit(self, symbol_name: str, value: float, limits: Dict, 
                    limit_key: str, alarm_type: AlarmType, priority: AlarmPriority,
                    unit: str, operator: str):
        """
        Check a specific alarm limit with hysteresis
        
        Args:
            symbol_name: Symbol name
            value: Current value
            limits: Dictionary of limits
            limit_key: Key in limits dict (e.g., 'high_high')
            alarm_type: Type of alarm
            priority: Alarm priority
            unit: Unit of measurement
            operator: Comparison operator ('>=', '<=')
        """
        if limit_key not in limits:
            return
        
        limit = limits[limit_key]
        alarm_key = f"{symbol_name}_{alarm_type.value}"
        
        # Calculate hysteresis
        hysteresis = abs(limit * self.hysteresis_percent / 100.0)
        
        # Check if alarm should trigger
        alarm_condition = False
        clear_condition = False
        
        if operator == '>=':
            alarm_condition = value >= limit
            clear_condition = value < (limit - hysteresis)
        else:  # operator == '<='
            alarm_condition = value <= limit
            clear_condition = value > (limit + hysteresis)
        
        # Check if alarm is already active
        existing_alarm = self.active_alarms.get(alarm_key)
        
        if alarm_condition and not existing_alarm:
            # New alarm
            message = f"{symbol_name}: {value:.2f}{unit} {operator} {limit}{unit} ({alarm_type.value})"
            alarm = Alarm(symbol_name, alarm_type, priority, value, limit, message)
            self.active_alarms[alarm_key] = alarm
            self.alarm_history.append(alarm)
            logger.warning(f"NEW ALARM: {message}")
            self._trigger_callbacks()
            
            if self.sound_enabled:
                self._play_alarm_sound(priority)
        
        elif clear_condition and existing_alarm:
            # Clear alarm (with hysteresis)
            if existing_alarm.is_active():
                existing_alarm.clear()
                del self.active_alarms[alarm_key]
                logger.info(f"Alarm cleared: {existing_alarm.message}")
                self._trigger_callbacks()
        
        elif existing_alarm and alarm_condition:
            # Update existing alarm value
            existing_alarm.value = value
    
    def _check_digital_alarm(self, symbol_name: str, value: bool, symbol_config: Dict):
        """
        Check digital (BOOL) alarm
        
        Args:
            symbol_name: Symbol name
            value: Current boolean value
            symbol_config: Symbol configuration
        """
        alarm_key = f"{symbol_name}_{AlarmType.DIGITAL.value}"
        alarm_text = symbol_config.get('alarm_text', f'{symbol_name} Alarm')
        priority = AlarmPriority(symbol_config.get('alarm_priority', 2))
        
        existing_alarm = self.active_alarms.get(alarm_key)
        
        if value and not existing_alarm:
            # Alarm activated
            message = alarm_text
            alarm = Alarm(symbol_name, AlarmType.DIGITAL, priority, 
                         1.0, 1.0, message)
            self.active_alarms[alarm_key] = alarm
            self.alarm_history.append(alarm)
            logger.warning(f"NEW DIGITAL ALARM: {message}")
            self._trigger_callbacks()
            
            if self.sound_enabled:
                self._play_alarm_sound(priority)
        
        elif not value and existing_alarm:
            # Alarm cleared
            if existing_alarm.is_active():
                existing_alarm.clear()
                del self.active_alarms[alarm_key]
                logger.info(f"Digital alarm cleared: {existing_alarm.message}")
                self._trigger_callbacks()
    
    def acknowledge_alarm(self, alarm_id: str, user: str = "User"):
        """
        Acknowledge a specific alarm
        
        Args:
            alarm_id: Alarm ID
            user: User who acknowledged
        """
        for alarm in self.active_alarms.values():
            if alarm.id == alarm_id:
                alarm.acknowledge(user)
                self._trigger_callbacks()
                return True
        return False
    
    def acknowledge_all(self, user: str = "User"):
        """
        Acknowledge all active alarms
        
        Args:
            user: User who acknowledged
        """
        count = 0
        for alarm in self.active_alarms.values():
            if alarm.state == AlarmState.ACTIVE:
                alarm.acknowledge(user)
                count += 1
        
        if count > 0:
            logger.info(f"Acknowledged {count} alarms")
            self._trigger_callbacks()
    
    def get_active_alarms(self, sort_by_priority: bool = True) -> List[Alarm]:
        """
        Get list of active alarms
        
        Args:
            sort_by_priority: Sort by priority (highest first)
            
        Returns:
            List of active alarms
        """
        alarms = list(self.active_alarms.values())
        
        if sort_by_priority:
            alarms.sort(key=lambda a: (a.priority.value, a.timestamp))
        else:
            alarms.sort(key=lambda a: a.timestamp, reverse=True)
        
        return alarms
    
    def get_unacknowledged_alarms(self) -> List[Alarm]:
        """Get list of unacknowledged alarms"""
        return [a for a in self.active_alarms.values() if a.state == AlarmState.ACTIVE]
    
    def get_alarm_count(self) -> Dict[str, int]:
        """
        Get count of alarms by state
        
        Returns:
            Dictionary with alarm counts
        """
        counts = {
            'active': 0,
            'acknowledged': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for alarm in self.active_alarms.values():
            if alarm.state == AlarmState.ACTIVE:
                counts['active'] += 1
            elif alarm.state == AlarmState.ACKNOWLEDGED:
                counts['acknowledged'] += 1
            
            if alarm.priority == AlarmPriority.CRITICAL:
                counts['critical'] += 1
            elif alarm.priority == AlarmPriority.HIGH:
                counts['high'] += 1
            elif alarm.priority == AlarmPriority.MEDIUM:
                counts['medium'] += 1
            elif alarm.priority == AlarmPriority.LOW:
                counts['low'] += 1
        
        return counts
    
    def get_alarm_history(self, limit: int = 100) -> List[Alarm]:
        """
        Get alarm history
        
        Args:
            limit: Maximum number of alarms to return
            
        Returns:
            List of historical alarms (newest first)
        """
        return self.alarm_history[-limit:][::-1]
    
    def clear_alarm_history(self):
        """Clear alarm history (keep active alarms)"""
        # Only keep alarms that are still active
        self.alarm_history = [a for a in self.alarm_history if a.is_active()]
        logger.info("Alarm history cleared")
    
    def _trigger_callbacks(self):
        """Trigger all registered callbacks"""
        active_alarms = self.get_active_alarms()
        for callback in self.callbacks:
            try:
                callback(active_alarms)
            except Exception as e:
                logger.error(f"Error in alarm callback: {e}")
    
    def _play_alarm_sound(self, priority: AlarmPriority):
        """
        Play alarm sound
        
        Args:
            priority: Alarm priority (affects sound)
        """
        if not self.sound_enabled:
            return
        
        try:
            import winsound
            
            # Different frequencies/durations based on priority
            if priority == AlarmPriority.CRITICAL:
                winsound.Beep(1500, 500)  # High pitch, longer
            elif priority == AlarmPriority.HIGH:
                winsound.Beep(1000, 300)  # Medium pitch
            else:
                winsound.Beep(800, 200)   # Lower pitch, shorter
        except Exception as e:
            logger.error(f"Failed to play alarm sound: {e}")
    
    def set_sound_enabled(self, enabled: bool):
        """Enable/disable alarm sound"""
        self.sound_enabled = enabled
        logger.info(f"Alarm sound {'enabled' if enabled else 'disabled'}")
