"""
Symbol Parser for TwinCAT HMI
Parses symbol attributes and categorizes symbols by type
"""

import logging
import re
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SymbolParser:
    """Parser for TwinCAT symbol attributes"""
    
    # Symbol categories
    CATEGORY_SETPOINT = 'setpoint'
    CATEGORY_PROCESS_VALUE = 'process_value'
    CATEGORY_SWITCH = 'switch'
    CATEGORY_ALARM = 'alarm'
    
    def __init__(self):
        self.symbols = {}
        self.categorized_symbols = {
            self.CATEGORY_SETPOINT: [],
            self.CATEGORY_PROCESS_VALUE: [],
            self.CATEGORY_SWITCH: [],
            self.CATEGORY_ALARM: []
        }
    
    def parse_symbols(self, symbol_dict: Dict[str, Dict]) -> Dict[str, List[Dict]]:
        """
        Parse and categorize symbols based on their attributes
        
        Args:
            symbol_dict: Dictionary from ads_client.discover_symbols()
            
        Returns:
            Dictionary with categorized symbols
        """
        self.symbols = symbol_dict
        self.categorized_symbols = {
            self.CATEGORY_SETPOINT: [],
            self.CATEGORY_PROCESS_VALUE: [],
            self.CATEGORY_SWITCH: [],
            self.CATEGORY_ALARM: []
        }
        
        for symbol_name, symbol_info in symbol_dict.items():
            parsed_symbol = self._parse_single_symbol(symbol_name, symbol_info)
            
            if parsed_symbol:
                category = parsed_symbol['category']
                self.categorized_symbols[category].append(parsed_symbol)
        
        logger.info(f"Parsed symbols: "
                   f"SP={len(self.categorized_symbols[self.CATEGORY_SETPOINT])}, "
                   f"PV={len(self.categorized_symbols[self.CATEGORY_PROCESS_VALUE])}, "
                   f"SW={len(self.categorized_symbols[self.CATEGORY_SWITCH])}, "
                   f"AL={len(self.categorized_symbols[self.CATEGORY_ALARM])}")
        
        return self.categorized_symbols
    
    def _parse_single_symbol(self, symbol_name: str, symbol_info: Dict) -> Optional[Dict]:
        """
        Parse a single symbol and extract configuration
        
        Args:
            symbol_name: Symbol name
            symbol_info: Symbol information dictionary
            
        Returns:
            Parsed symbol configuration or None
        """
        attributes = symbol_info.get('attributes', {})
        comment = symbol_info.get('comment', '')
        data_type = symbol_info.get('data_type', '')
        
        # Parse attributes from comment if not already parsed
        if not attributes and comment:
            attributes = self._extract_attributes_from_comment(comment)
        
        # Determine category based on attributes
        category = self._determine_category(attributes, data_type)
        
        if not category:
            return None
        
        parsed = {
            'name': symbol_name,
            'display_name': self._get_display_name(symbol_name),
            'category': category,
            'data_type': data_type,
            'unit': attributes.get('Unit', ''),
            'attributes': attributes
        }
        
        # Add category-specific properties
        if category == self.CATEGORY_SETPOINT:
            parsed.update(self._parse_setpoint_attributes(attributes))
        elif category == self.CATEGORY_PROCESS_VALUE:
            parsed.update(self._parse_process_value_attributes(attributes))
        elif category == self.CATEGORY_SWITCH:
            parsed.update(self._parse_switch_attributes(attributes))
        elif category == self.CATEGORY_ALARM:
            parsed.update(self._parse_alarm_attributes(attributes))
        
        # Parse alarm limits (can be on any numeric symbol)
        if data_type in ['REAL', 'LREAL', 'INT', 'DINT', 'UINT', 'UDINT']:
            parsed['alarm_config'] = self._parse_alarm_limits(attributes)
        
        return parsed
    
    def _extract_attributes_from_comment(self, comment: str) -> Dict[str, str]:
        """
        Extract attributes from TwinCAT comment string
        
        Args:
            comment: Comment string containing attributes
            
        Returns:
            Dictionary of attributes
        """
        attributes = {}
        
        # Pattern: {attribute 'Key' := 'Value'}
        pattern = r"\{attribute\s+'([^']+)'\s*:=\s*'([^']+)'\}"
        matches = re.findall(pattern, comment)
        
        for key, value in matches:
            attributes[key] = value
        
        # Also check for patterns without quotes (for HMI_ tags)
        pattern2 = r"\{attribute\s+'([^']+)'\}"
        matches2 = re.findall(pattern2, comment)
        
        for match in matches2:
            # If it's a tag like HMI_SP, store as boolean
            attributes[match] = 'true'
        
        return attributes
    
    def _determine_category(self, attributes: Dict, data_type: str) -> Optional[str]:
        """
        Determine symbol category based on attributes
        
        Args:
            attributes: Symbol attributes
            data_type: PLC data type
            
        Returns:
            Category string or None
        """
        # Check for explicit HMI tags
        if 'HMI_SP' in attributes or any('HMI_SP' in str(v) for v in attributes.values()):
            return self.CATEGORY_SETPOINT
        
        if 'HMI_PV' in attributes or any('HMI_PV' in str(v) for v in attributes.values()):
            return self.CATEGORY_PROCESS_VALUE
        
        if 'HMI_SWITCH' in attributes or any('HMI_SWITCH' in str(v) for v in attributes.values()):
            return self.CATEGORY_SWITCH
        
        if 'HMI_ALARM' in attributes or any('HMI_ALARM' in str(v) for v in attributes.values()):
            return self.CATEGORY_ALARM
        
        # If BOOL with AlarmText, it's an alarm
        if data_type == 'BOOL' and 'AlarmText' in attributes:
            return self.CATEGORY_ALARM
        
        return None
    
    def _parse_setpoint_attributes(self, attributes: Dict) -> Dict:
        """Parse setpoint-specific attributes"""
        config = {
            'min': float(attributes.get('Min', 0)),
            'max': float(attributes.get('Max', 100)),
            'step': float(attributes.get('Step', 1)),
            'decimals': int(attributes.get('Decimals', 1))
        }
        return config
    
    def _parse_process_value_attributes(self, attributes: Dict) -> Dict:
        """Parse process value-specific attributes"""
        config = {
            'decimals': int(attributes.get('Decimals', 2)),
            'format': attributes.get('Format', '{:.2f}')
        }
        return config
    
    def _parse_switch_attributes(self, attributes: Dict) -> Dict:
        """Parse switch-specific attributes"""
        # Extract position labels (Pos0, Pos1, Pos2, etc.)
        positions = {}
        for key, value in attributes.items():
            if key.startswith('Pos'):
                try:
                    pos_num = int(key[3:])
                    positions[pos_num] = value
                except ValueError:
                    continue
        
        config = {
            'positions': positions
        }
        return config
    
    def _parse_alarm_attributes(self, attributes: Dict) -> Dict:
        """Parse digital alarm attributes"""
        config = {
            'alarm_text': attributes.get('AlarmText', 'Alarm'),
            'alarm_priority': int(attributes.get('AlarmPriority', 2))
        }
        return config
    
    def _parse_alarm_limits(self, attributes: Dict) -> Dict:
        """
        Parse alarm limit attributes from any symbol
        
        Args:
            attributes: Symbol attributes
            
        Returns:
            Dictionary with alarm configuration
        """
        alarm_config = {
            'enabled': False,
            'limits': {},
            'priority': int(attributes.get('AlarmPriority', 2)),
            'deadband_percent': 2.0  # Default hysteresis
        }
        
        # Parse alarm limits
        if 'AlarmHighHigh' in attributes:
            try:
                alarm_config['limits']['high_high'] = float(attributes['AlarmHighHigh'])
                alarm_config['enabled'] = True
            except ValueError:
                pass
        
        if 'AlarmHigh' in attributes:
            try:
                alarm_config['limits']['high'] = float(attributes['AlarmHigh'])
                alarm_config['enabled'] = True
            except ValueError:
                pass
        
        if 'AlarmLow' in attributes:
            try:
                alarm_config['limits']['low'] = float(attributes['AlarmLow'])
                alarm_config['enabled'] = True
            except ValueError:
                pass
        
        if 'AlarmLowLow' in attributes:
            try:
                alarm_config['limits']['low_low'] = float(attributes['AlarmLowLow'])
                alarm_config['enabled'] = True
            except ValueError:
                pass
        
        return alarm_config
    
    def _get_display_name(self, symbol_name: str) -> str:
        """
        Convert symbol name to display-friendly format
        
        Args:
            symbol_name: Full symbol name (e.g., "GVL.TemperaturSetpunkt")
            
        Returns:
            Display name (e.g., "Temperatur Setpunkt")
        """
        # Remove prefix (e.g., "GVL.")
        name = symbol_name.split('.')[-1]
        
        # Insert spaces before capitals
        name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
        
        # Replace underscores with spaces
        name = name.replace('_', ' ')
        
        return name
    
    def get_symbols_by_category(self, category: str) -> List[Dict]:
        """
        Get all symbols in a specific category
        
        Args:
            category: Category name
            
        Returns:
            List of symbols in that category
        """
        return self.categorized_symbols.get(category, [])
    
    def get_symbol_config(self, symbol_name: str) -> Optional[Dict]:
        """
        Get parsed configuration for a specific symbol
        
        Args:
            symbol_name: Symbol name
            
        Returns:
            Symbol configuration or None
        """
        for category_symbols in self.categorized_symbols.values():
            for symbol in category_symbols:
                if symbol['name'] == symbol_name:
                    return symbol
        return None
    
    def get_symbols_with_alarms(self) -> List[Dict]:
        """
        Get all symbols that have alarm limits configured
        
        Returns:
            List of symbols with alarm configuration
        """
        symbols_with_alarms = []
        
        for category_symbols in self.categorized_symbols.values():
            for symbol in category_symbols:
                alarm_config = symbol.get('alarm_config', {})
                if alarm_config.get('enabled', False):
                    symbols_with_alarms.append(symbol)
        
        # Also include digital alarms
        symbols_with_alarms.extend(self.categorized_symbols[self.CATEGORY_ALARM])
        
        return symbols_with_alarms
