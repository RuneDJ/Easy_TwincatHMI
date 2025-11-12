"""
STRUCT Reader for TwinCAT HMI
Reads ST_HMI_* structures from PLC via ADS
"""

import pyads
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class StructReader:
    """
    Reads TwinCAT STRUCT data via ADS with encoding support
    """
    
    def __init__(self, plc_connection: pyads.Connection):
        """
        Initialize reader with PLC connection
        
        Args:
            plc_connection: Active pyads Connection object
        """
        self.plc = plc_connection
    
    def _read_string(self, symbol_path: str, max_length: int = 255) -> str:
        """
        Read string from PLC with encoding fallback
        
        Args:
            symbol_path: Full path to string variable
            max_length: Maximum string length
            
        Returns:
            Decoded string
        """
        try:
            # Try UTF-8 first
            data = self.plc.read_by_name(symbol_path, pyads.PLCTYPE_STRING)
            return data
        except UnicodeDecodeError:
            # Fallback to Windows-1252 for Danish characters
            try:
                raw_data = self.plc.read_by_name(symbol_path, pyads.PLCTYPE_STRING)
                if isinstance(raw_data, bytes):
                    return raw_data.decode('windows-1252')
                return str(raw_data)
            except Exception as e:
                logger.warning(f"Failed to decode string from {symbol_path}: {e}")
                return ""
        except Exception as e:
            logger.warning(f"Failed to read string from {symbol_path}: {e}")
            return ""
    
    def read_setpoint(self, base_path: str) -> Dict[str, Any]:
        """
        Read ST_HMI_Setpoint structure
        
        Args:
            base_path: Base path to setpoint (e.g., "MAIN.HMI.TemperaturSetpunkt")
            
        Returns:
            Dictionary with setpoint data
        """
        try:
            data = {
                'name': base_path,
                'value': 0.0,
                'config': {
                    'min': 0.0,
                    'max': 100.0,
                    'unit': '',
                    'decimals': 1,
                    'step': 1.0
                },
                'alarm_limits': {
                    'high_high': None,
                    'high': None,
                    'low': None,
                    'low_low': None,
                    'hysteresis': 0.0,
                    'alarm_active': False,
                    'warning_active': False
                },
                'display': {
                    'display_name': '',
                    'description': '',
                    'visible': True,
                    'read_only': False
                }
            }
            
            # Read Value
            try:
                data['value'] = self.plc.read_by_name(f"{base_path}.Value", pyads.PLCTYPE_REAL)
            except Exception as e:
                logger.debug(f"Failed to read {base_path}.Value: {e}")
            
            # Read Config (note: nMin/nMax in PLC)
            try:
                data['config']['min'] = self.plc.read_by_name(f"{base_path}.Config.nMin", pyads.PLCTYPE_REAL)
            except Exception as e:
                logger.debug(f"Failed to read {base_path}.Config.nMin: {e}")
            
            try:
                data['config']['max'] = self.plc.read_by_name(f"{base_path}.Config.nMax", pyads.PLCTYPE_REAL)
            except Exception as e:
                logger.debug(f"Failed to read {base_path}.Config.nMax: {e}")
            
            try:
                data['config']['unit'] = self._read_string(f"{base_path}.Config.Unit")
            except Exception as e:
                logger.debug(f"Failed to read {base_path}.Config.Unit: {e}")
            
            try:
                data['config']['decimals'] = self.plc.read_by_name(f"{base_path}.Config.Decimals", pyads.PLCTYPE_USINT)
            except Exception as e:
                logger.debug(f"Failed to read {base_path}.Config.Decimals: {e}")
            
            try:
                data['config']['step'] = self.plc.read_by_name(f"{base_path}.Config.Step", pyads.PLCTYPE_REAL)
            except Exception as e:
                logger.debug(f"Failed to read {base_path}.Config.Step: {e}")
            
            # Read AlarmLimits
            try:
                data['alarm_limits']['high_high'] = self.plc.read_by_name(f"{base_path}.AlarmLimits.AlarmHighHigh", pyads.PLCTYPE_REAL)
            except:
                pass
            
            try:
                data['alarm_limits']['high'] = self.plc.read_by_name(f"{base_path}.AlarmLimits.AlarmHigh", pyads.PLCTYPE_REAL)
            except:
                pass
            
            try:
                data['alarm_limits']['low'] = self.plc.read_by_name(f"{base_path}.AlarmLimits.AlarmLow", pyads.PLCTYPE_REAL)
            except:
                pass
            
            try:
                data['alarm_limits']['low_low'] = self.plc.read_by_name(f"{base_path}.AlarmLimits.AlarmLowLow", pyads.PLCTYPE_REAL)
            except:
                pass
            
            try:
                data['alarm_limits']['hysteresis'] = self.plc.read_by_name(f"{base_path}.AlarmLimits.Hysteresis", pyads.PLCTYPE_REAL)
            except:
                pass
            
            try:
                data['alarm_limits']['alarm_active'] = self.plc.read_by_name(f"{base_path}.AlarmLimits.AlarmActive", pyads.PLCTYPE_BOOL)
            except:
                pass
            
            try:
                data['alarm_limits']['warning_active'] = self.plc.read_by_name(f"{base_path}.AlarmLimits.WarningActive", pyads.PLCTYPE_BOOL)
            except:
                pass
            
            # Read Display
            try:
                data['display']['display_name'] = self._read_string(f"{base_path}.Display.DisplayName")
            except Exception as e:
                logger.debug(f"Failed to read {base_path}.Display.DisplayName: {e}")
            
            try:
                data['display']['description'] = self._read_string(f"{base_path}.Display.Description")
            except:
                pass
            
            try:
                data['display']['visible'] = self.plc.read_by_name(f"{base_path}.Display.Visible", pyads.PLCTYPE_BOOL)
            except:
                pass
            
            try:
                data['display']['read_only'] = self.plc.read_by_name(f"{base_path}.Display.ReadOnly", pyads.PLCTYPE_BOOL)
            except:
                pass
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to read setpoint {base_path}: {e}")
            return None
    
    def read_process_value(self, base_path: str) -> Dict[str, Any]:
        """
        Read ST_HMI_ProcessValue structure
        
        Args:
            base_path: Base path to process value
            
        Returns:
            Dictionary with process value data
        """
        try:
            data = {
                'name': base_path,
                'value': 0.0,
                'config': {
                    'min': 0.0,
                    'max': 100.0,
                    'unit': '',
                    'decimals': 1,
                    'step': 1.0
                },
                'alarm_limits': {
                    'high_high': None,
                    'high': None,
                    'low': None,
                    'low_low': None,
                    'hysteresis': 0.0,
                    'alarm_active': False,
                    'warning_active': False
                },
                'display': {
                    'display_name': '',
                    'description': '',
                    'visible': True,
                    'read_only': True
                },
                'quality': 'Unknown',
                'sensor_fault': False
            }
            
            # Read Value
            try:
                data['value'] = self.plc.read_by_name(f"{base_path}.Value", pyads.PLCTYPE_REAL)
            except Exception as e:
                logger.debug(f"Failed to read {base_path}.Value: {e}")
            
            # Read Config
            try:
                data['config']['min'] = self.plc.read_by_name(f"{base_path}.Config.nMin", pyads.PLCTYPE_REAL)
            except:
                pass
            
            try:
                data['config']['max'] = self.plc.read_by_name(f"{base_path}.Config.nMax", pyads.PLCTYPE_REAL)
            except:
                pass
            
            try:
                data['config']['unit'] = self._read_string(f"{base_path}.Config.Unit")
            except:
                pass
            
            try:
                data['config']['decimals'] = self.plc.read_by_name(f"{base_path}.Config.Decimals", pyads.PLCTYPE_USINT)
            except:
                pass
            
            # Read AlarmLimits (same as setpoint)
            try:
                data['alarm_limits']['high_high'] = self.plc.read_by_name(f"{base_path}.AlarmLimits.AlarmHighHigh", pyads.PLCTYPE_REAL)
            except:
                pass
            
            try:
                data['alarm_limits']['high'] = self.plc.read_by_name(f"{base_path}.AlarmLimits.AlarmHigh", pyads.PLCTYPE_REAL)
            except:
                pass
            
            try:
                data['alarm_limits']['low'] = self.plc.read_by_name(f"{base_path}.AlarmLimits.AlarmLow", pyads.PLCTYPE_REAL)
            except:
                pass
            
            try:
                data['alarm_limits']['low_low'] = self.plc.read_by_name(f"{base_path}.AlarmLimits.AlarmLowLow", pyads.PLCTYPE_REAL)
            except:
                pass
            
            # Read Display
            try:
                data['display']['display_name'] = self._read_string(f"{base_path}.Display.DisplayName")
            except:
                pass
            
            try:
                data['display']['description'] = self._read_string(f"{base_path}.Display.Description")
            except:
                pass
            
            try:
                data['display']['visible'] = self.plc.read_by_name(f"{base_path}.Display.Visible", pyads.PLCTYPE_BOOL)
            except:
                pass
            
            # Read Quality and SensorFault
            try:
                quality_int = self.plc.read_by_name(f"{base_path}.Quality", pyads.PLCTYPE_USINT)
                quality_map = {0: 'Bad', 1: 'Uncertain', 2: 'Good'}
                data['quality'] = quality_map.get(quality_int, 'Unknown')
            except:
                pass
            
            try:
                data['sensor_fault'] = self.plc.read_by_name(f"{base_path}.SensorFault", pyads.PLCTYPE_BOOL)
            except:
                pass
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to read process value {base_path}: {e}")
            return None
    
    def read_switch(self, base_path: str) -> Dict[str, Any]:
        """
        Read ST_HMI_Switch structure
        
        Args:
            base_path: Base path to switch
            
        Returns:
            Dictionary with switch data
        """
        try:
            data = {
                'name': base_path,
                'position': 0,
                'config': {
                    'num_positions': 2,
                    'labels': []
                },
                'display': {
                    'display_name': '',
                    'description': '',
                    'visible': True,
                    'read_only': False
                },
                'positions': {}  # For GUI compatibility
            }
            
            # Read Position
            try:
                data['position'] = self.plc.read_by_name(f"{base_path}.Position", pyads.PLCTYPE_INT)
            except Exception as e:
                logger.debug(f"Failed to read {base_path}.Position: {e}")
            
            # Read Config
            try:
                data['config']['num_positions'] = self.plc.read_by_name(f"{base_path}.Config.NumPositions", pyads.PLCTYPE_USINT)
            except:
                pass
            
            # Read position labels (Pos0_Label through Pos7_Label)
            labels = []
            for i in range(8):
                try:
                    label = self._read_string(f"{base_path}.Config.Pos{i}_Label")
                    if label:  # Only add non-empty labels
                        labels.append(label)
                except:
                    break
            
            data['config']['labels'] = labels
            
            # Convert labels list to positions dict for GUI compatibility
            data['positions'] = {str(i): label for i, label in enumerate(labels)}
            
            # Read Display
            try:
                data['display']['display_name'] = self._read_string(f"{base_path}.Display.DisplayName")
            except:
                pass
            
            try:
                data['display']['description'] = self._read_string(f"{base_path}.Display.Description")
            except:
                pass
            
            try:
                data['display']['visible'] = self.plc.read_by_name(f"{base_path}.Display.Visible", pyads.PLCTYPE_BOOL)
            except:
                pass
            
            try:
                data['display']['read_only'] = self.plc.read_by_name(f"{base_path}.Display.ReadOnly", pyads.PLCTYPE_BOOL)
            except:
                pass
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to read switch {base_path}: {e}")
            return None
    
    def read_alarm(self, base_path: str) -> Dict[str, Any]:
        """
        Read ST_HMI_Alarm structure
        
        Args:
            base_path: Base path to alarm
            
        Returns:
            Dictionary with alarm data
        """
        try:
            data = {
                'name': base_path,
                'active': False,
                'text': '',
                'priority': 3,
                'acknowledged': False,
                'timestamp': None,
                'display': {
                    'display_name': '',
                    'description': '',
                    'visible': True,
                    'read_only': True
                }
            }
            
            # Read Active
            try:
                data['active'] = self.plc.read_by_name(f"{base_path}.Active", pyads.PLCTYPE_BOOL)
            except Exception as e:
                logger.debug(f"Failed to read {base_path}.Active: {e}")
            
            # Read AlarmText
            try:
                data['text'] = self._read_string(f"{base_path}.AlarmText")
            except:
                pass
            
            # Read Priority
            try:
                data['priority'] = self.plc.read_by_name(f"{base_path}.AlarmPriority", pyads.PLCTYPE_USINT)
            except:
                pass
            
            # Read Acknowledged
            try:
                data['acknowledged'] = self.plc.read_by_name(f"{base_path}.Acknowledged", pyads.PLCTYPE_BOOL)
            except:
                pass
            
            # Read Display
            try:
                data['display']['display_name'] = self._read_string(f"{base_path}.Display.DisplayName")
            except:
                pass
            
            try:
                data['display']['description'] = self._read_string(f"{base_path}.Display.Description")
            except:
                pass
            
            try:
                data['display']['visible'] = self.plc.read_by_name(f"{base_path}.Display.Visible", pyads.PLCTYPE_BOOL)
            except:
                pass
            
            # Read Timestamp (if available)
            try:
                timestamp = self.plc.read_by_name(f"{base_path}.TriggerTime", pyads.PLCTYPE_DT)
                data['timestamp'] = timestamp
            except:
                pass
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to read alarm {base_path}: {e}")
            return None
    
    def write_setpoint_value(self, base_path: str, value: float) -> bool:
        """
        Write value to setpoint
        
        Args:
            base_path: Base path to setpoint
            value: New value
            
        Returns:
            True if successful
        """
        try:
            self.plc.write_by_name(f"{base_path}.Value", value, pyads.PLCTYPE_REAL)
            logger.info(f"Wrote {value} to {base_path}.Value")
            return True
        except Exception as e:
            logger.error(f"Failed to write to {base_path}.Value: {e}")
            return False
    
    def write_switch_position(self, base_path: str, position: int) -> bool:
        """
        Write position to switch
        
        Args:
            base_path: Base path to switch
            position: New position
            
        Returns:
            True if successful
        """
        try:
            self.plc.write_by_name(f"{base_path}.Position", position, pyads.PLCTYPE_INT)
            logger.info(f"Wrote position {position} to {base_path}.Position")
            return True
        except Exception as e:
            logger.error(f"Failed to write to {base_path}.Position: {e}")
            return False
    
    def acknowledge_alarm(self, base_path: str) -> bool:
        """
        Acknowledge an alarm
        
        Args:
            base_path: Base path to alarm
            
        Returns:
            True if successful
        """
        try:
            self.plc.write_by_name(f"{base_path}.Acknowledged", True, pyads.PLCTYPE_BOOL)
            logger.info(f"Acknowledged alarm {base_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to acknowledge alarm {base_path}: {e}")
            return False
    
    def read_all_symbols(self, symbols_config: Dict[str, List[str]], base_path: str = "MAIN.HMI") -> Dict[str, Dict]:
        """
        Read all symbols from configuration
        
        Args:
            symbols_config: Dictionary with symbol categories and names
            base_path: Base path to HMI symbols (e.g., "MAIN.HMI")
            
        Returns:
            Dictionary with all symbol data categorized
        """
        all_data = {
            'setpoints': {},
            'process_values': {},
            'switches': {},
            'alarms': {}
        }
        
        # Read setpoints
        for name in symbols_config.get('setpoints', []):
            full_path = f"{base_path}.{name}"
            data = self.read_setpoint(full_path)
            if data:
                all_data['setpoints'][full_path] = data
        
        # Read process values
        for name in symbols_config.get('process_values', []):
            full_path = f"{base_path}.{name}"
            data = self.read_process_value(full_path)
            if data:
                all_data['process_values'][full_path] = data
        
        # Read switches
        for name in symbols_config.get('switches', []):
            full_path = f"{base_path}.{name}"
            data = self.read_switch(full_path)
            if data:
                all_data['switches'][full_path] = data
        
        # Read alarms
        for name in symbols_config.get('alarms', []):
            full_path = f"{base_path}.{name}"
            data = self.read_alarm(full_path)
            if data:
                all_data['alarms'][full_path] = data
        
        return all_data
