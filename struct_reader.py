"""
struct_reader.py - Læser TwinCAT STRUCTs via ADS
"""
import pyads
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class StructReader:
    """Read TwinCAT STRUCT data via ADS"""
    
    def __init__(self, plc):
        """
        Initialize STRUCT reader
        
        Args:
            plc: pyads.Connection object
        """
        self.plc = plc
    
    def _read_string(self, path: str) -> str:
        """
        Helper function to read STRING with proper encoding handling
        
        Args:
            path: Full symbol path to string
            
        Returns:
            Decoded string value
        """
        try:
            return self.plc.read_by_name(path, pyads.PLCTYPE_STRING)
        except UnicodeDecodeError:
            # TwinCAT uses Windows-1252 encoding for special characters
            try:
                raw_bytes = self.plc.read(self.plc.get_handle(path), pyads.PLCTYPE_STRING)
                if isinstance(raw_bytes, bytes):
                    # Decode with windows-1252 and remove null terminator
                    return raw_bytes.split(b'\x00')[0].decode('windows-1252', errors='replace')
                return str(raw_bytes)
            except:
                return ""
        except:
            return ""
    
    def read_setpoint(self, symbol_path: str) -> Optional[Dict[str, Any]]:
        """
        Read ST_HMI_Setpoint STRUCT
        
        Args:
            symbol_path: Full symbol path (e.g., "MAIN.HMI.TemperaturSetpunkt")
            
        Returns:
            Dict with value and all config fields
        """
        try:
            result = {
                'value': self.plc.read_by_name(f"{symbol_path}.Value", pyads.PLCTYPE_REAL),
                'config': {
                    'unit': self._read_string(f"{symbol_path}.Config.Unit"),
                    'min': self.plc.read_by_name(f"{symbol_path}.Config.nMin", pyads.PLCTYPE_REAL),
                    'max': self.plc.read_by_name(f"{symbol_path}.Config.nMax", pyads.PLCTYPE_REAL),
                    'decimals': self.plc.read_by_name(f"{symbol_path}.Config.Decimals", pyads.PLCTYPE_USINT),
                    'step': self.plc.read_by_name(f"{symbol_path}.Config.Step", pyads.PLCTYPE_REAL),
                },
                'alarm_limits': {
                    'high_high': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmHighHigh", pyads.PLCTYPE_REAL),
                    'high': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmHigh", pyads.PLCTYPE_REAL),
                    'low': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmLow", pyads.PLCTYPE_REAL),
                    'low_low': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmLowLow", pyads.PLCTYPE_REAL),
                    'priority': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmPriority", pyads.PLCTYPE_USINT),
                    'active': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmActive", pyads.PLCTYPE_BOOL),
                    'warning': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.WarningActive", pyads.PLCTYPE_BOOL),
                    'text': self._read_string(f"{symbol_path}.AlarmLimits.AlarmText"),
                    'hysteresis': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.Hysteresis", pyads.PLCTYPE_REAL),
                },
                'display': {
                    'name': self._read_string(f"{symbol_path}.Display.DisplayName"),
                    'description': self._read_string(f"{symbol_path}.Display.Description"),
                    'visible': self.plc.read_by_name(f"{symbol_path}.Display.Visible", pyads.PLCTYPE_BOOL),
                    'readonly': self.plc.read_by_name(f"{symbol_path}.Display.ReadOnly", pyads.PLCTYPE_BOOL),
                }
            }
            
            logger.debug(f"Read setpoint {symbol_path}: {result['value']} {result['config']['unit']}")
            return result
            
        except Exception as e:
            logger.error(f"Error reading setpoint {symbol_path}: {e}")
            return None
    
    def read_process_value(self, symbol_path: str) -> Optional[Dict[str, Any]]:
        """
        Read ST_HMI_ProcessValue STRUCT
        
        Args:
            symbol_path: Full symbol path (e.g., "MAIN.HMI.Temperatur_1")
            
        Returns:
            Dict with value and config fields
        """
        try:
            result = {
                'value': self.plc.read_by_name(f"{symbol_path}.Value", pyads.PLCTYPE_REAL),
                'config': {
                    'unit': self._read_string(f"{symbol_path}.Config.Unit"),
                    'decimals': self.plc.read_by_name(f"{symbol_path}.Config.Decimals", pyads.PLCTYPE_USINT),
                    'min': self.plc.read_by_name(f"{symbol_path}.Config.nMin", pyads.PLCTYPE_REAL),
                    'max': self.plc.read_by_name(f"{symbol_path}.Config.nMax", pyads.PLCTYPE_REAL),
                    'step': self.plc.read_by_name(f"{symbol_path}.Config.Step", pyads.PLCTYPE_REAL),
                },
                'alarm_limits': {
                    'high_high': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmHighHigh", pyads.PLCTYPE_REAL),
                    'high': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmHigh", pyads.PLCTYPE_REAL),
                    'low': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmLow", pyads.PLCTYPE_REAL),
                    'low_low': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmLowLow", pyads.PLCTYPE_REAL),
                    'priority': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmPriority", pyads.PLCTYPE_USINT),
                    'active': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.AlarmActive", pyads.PLCTYPE_BOOL),
                    'warning': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.WarningActive", pyads.PLCTYPE_BOOL),
                    'text': self._read_string(f"{symbol_path}.AlarmLimits.AlarmText"),
                    'hysteresis': self.plc.read_by_name(f"{symbol_path}.AlarmLimits.Hysteresis", pyads.PLCTYPE_REAL),
                },
                'display': {
                    'name': self._read_string(f"{symbol_path}.Display.DisplayName"),
                    'description': self._read_string(f"{symbol_path}.Display.Description"),
                    'visible': self.plc.read_by_name(f"{symbol_path}.Display.Visible", pyads.PLCTYPE_BOOL),
                    'readonly': self.plc.read_by_name(f"{symbol_path}.Display.ReadOnly", pyads.PLCTYPE_BOOL),
                },
                'quality': self.plc.read_by_name(f"{symbol_path}.Quality", pyads.PLCTYPE_USINT),
                'sensor_fault': self.plc.read_by_name(f"{symbol_path}.SensorFault", pyads.PLCTYPE_BOOL),
            }
            
            logger.debug(f"Read process value {symbol_path}: {result['value']} {result['config']['unit']}")
            return result
            
        except Exception as e:
            logger.error(f"Error reading process value {symbol_path}: {e}")
            return None
    
    def read_switch(self, symbol_path: str) -> Optional[Dict[str, Any]]:
        """
        Read ST_HMI_Switch STRUCT
        
        Args:
            symbol_path: Full symbol path (e.g., "MAIN.HMI.DriftMode")
            
        Returns:
            Dict with position and labels
        """
        try:
            num_pos = self.plc.read_by_name(f"{symbol_path}.Config.NumPositions", pyads.PLCTYPE_USINT)
            
            # Læs labels for alle positioner
            labels = []
            for i in range(min(num_pos, 8)):  # Max 8 positions
                try:
                    label = self._read_string(f"{symbol_path}.Config.Pos{i}_Label")
                    labels.append(label)
                except:
                    labels.append(f"Pos {i}")
            
            result = {
                'position': self.plc.read_by_name(f"{symbol_path}.Position", pyads.PLCTYPE_INT),
                'config': {
                    'num_positions': num_pos,
                    'labels': labels,
                },
                'display': {
                    'name': self._read_string(f"{symbol_path}.Display.DisplayName"),
                    'description': self._read_string(f"{symbol_path}.Display.Description"),
                    'visible': self.plc.read_by_name(f"{symbol_path}.Display.Visible", pyads.PLCTYPE_BOOL),
                    'readonly': self.plc.read_by_name(f"{symbol_path}.Display.ReadOnly", pyads.PLCTYPE_BOOL),
                },
            }
            
            logger.debug(f"Read switch {symbol_path}: pos={result['position']}, labels={labels}")
            return result
            
        except Exception as e:
            logger.error(f"Error reading switch {symbol_path}: {e}")
            return None
    
    def read_alarm(self, symbol_path: str) -> Optional[Dict[str, Any]]:
        """
        Read ST_HMI_Alarm STRUCT
        
        Args:
            symbol_path: Full symbol path (e.g., "MAIN.HMI.Motor1Fejl")
            
        Returns:
            Dict with alarm status
        """
        try:
            result = {
                'active': self.plc.read_by_name(f"{symbol_path}.Active", pyads.PLCTYPE_BOOL),
                'text': self._read_string(f"{symbol_path}.AlarmText"),
                'priority': self.plc.read_by_name(f"{symbol_path}.AlarmPriority", pyads.PLCTYPE_USINT),
                'acknowledged': self.plc.read_by_name(f"{symbol_path}.Acknowledged", pyads.PLCTYPE_BOOL),
                'trigger_count': self.plc.read_by_name(f"{symbol_path}.TriggerCount", pyads.PLCTYPE_UDINT),
                'display': {
                    'name': self._read_string(f"{symbol_path}.Display.DisplayName"),
                    'description': self._read_string(f"{symbol_path}.Display.Description"),
                    'visible': self.plc.read_by_name(f"{symbol_path}.Display.Visible", pyads.PLCTYPE_BOOL),
                },
            }
            
            logger.debug(f"Read alarm {symbol_path}: active={result['active']}")
            return result
            
        except Exception as e:
            logger.error(f"Error reading alarm {symbol_path}: {e}")
            return None
    
    def write_setpoint_value(self, symbol_path: str, value: float) -> bool:
        """
        Write setpoint value
        
        Args:
            symbol_path: Full symbol path
            value: New value to write
            
        Returns:
            True if successful
        """
        try:
            self.plc.write_by_name(f"{symbol_path}.Value", value, pyads.PLCTYPE_REAL)
            logger.info(f"Wrote setpoint {symbol_path}.Value = {value}")
            return True
        except Exception as e:
            logger.error(f"Error writing setpoint {symbol_path}: {e}")
            return False
    
    def write_switch_position(self, symbol_path: str, position: int) -> bool:
        """
        Write switch position
        
        Args:
            symbol_path: Full symbol path
            position: New position (0-7)
            
        Returns:
            True if successful
        """
        try:
            self.plc.write_by_name(f"{symbol_path}.Position", position, pyads.PLCTYPE_INT)
            logger.info(f"Wrote switch {symbol_path}.Position = {position}")
            return True
        except Exception as e:
            logger.error(f"Error writing switch {symbol_path}: {e}")
            return False
    
    def acknowledge_alarm(self, symbol_path: str) -> bool:
        """
        Acknowledge alarm
        
        Args:
            symbol_path: Full symbol path
            
        Returns:
            True if successful
        """
        try:
            self.plc.write_by_name(f"{symbol_path}.Acknowledged", True, pyads.PLCTYPE_BOOL)
            logger.info(f"Acknowledged alarm {symbol_path}")
            return True
        except Exception as e:
            logger.error(f"Error acknowledging alarm {symbol_path}: {e}")
            return False
    
    def read_all_symbols(self, symbols_config: Dict[str, List[str]], base_path: str = "MAIN.HMI") -> Dict[str, Dict[str, Any]]:
        """
        Read all symbols from config
        
        Args:
            symbols_config: Dict with 'setpoints', 'process_values', 'switches', 'alarms' lists
            base_path: Base path to HMI struct (default: "MAIN.HMI")
            
        Returns:
            Dict mapping symbol names to their data
        """
        all_symbols = {}
        
        # Read setpoints
        for sp_name in symbols_config.get('setpoints', []):
            full_path = f"{base_path}.{sp_name}"
            sp_data = self.read_setpoint(full_path)
            if sp_data:
                all_symbols[sp_name] = {
                    'path': full_path,
                    'type': 'setpoint',
                    'data': sp_data
                }
        
        # Read process values
        for pv_name in symbols_config.get('process_values', []):
            full_path = f"{base_path}.{pv_name}"
            pv_data = self.read_process_value(full_path)
            if pv_data:
                all_symbols[pv_name] = {
                    'path': full_path,
                    'type': 'process_value',
                    'data': pv_data
                }
        
        # Read switches
        for sw_name in symbols_config.get('switches', []):
            full_path = f"{base_path}.{sw_name}"
            sw_data = self.read_switch(full_path)
            if sw_data:
                all_symbols[sw_name] = {
                    'path': full_path,
                    'type': 'switch',
                    'data': sw_data
                }
        
        # Read alarms
        for al_name in symbols_config.get('alarms', []):
            full_path = f"{base_path}.{al_name}"
            al_data = self.read_alarm(full_path)
            if al_data:
                all_symbols[al_name] = {
                    'path': full_path,
                    'type': 'alarm',
                    'data': al_data
                }
        
        logger.info(f"Read {len(all_symbols)} symbols from PLC")
        return all_symbols
