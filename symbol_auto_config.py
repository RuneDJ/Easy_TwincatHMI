"""
Automatic Symbol Configuration Generator
Scans PLC and generates config.json automatically
"""

import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SymbolAutoConfig:
    """Automatically generate symbol configuration from PLC"""
    
    # Common units to detect
    UNITS = ['°C', '°F', 'K', 'bar', 'psi', 'Pa', 'kPa', 'MPa', 
             'L/min', 'L/h', 'm³/h', 'kg/h', '%', 'RPM', 'Hz', 
             'mm', 'cm', 'm', 'A', 'V', 'W', 'kW', 's', 'min', 'h']
    
    # Keywords for category detection (Danish and English)
    SETPOINT_KEYWORDS = ['setpoint', 'setpunkt', 'sollwert', 'target', 'set']
    ALARM_KEYWORDS = ['alarm', 'fejl', 'fault', 'error', 'warning', 'advarsel', 
                     'reminder', 'paamindelse']
    SWITCH_KEYWORDS = ['mode', 'switch', 'selector', 'valg', 'position', 'choice']
    
    # Measurement keywords (indicates process value)
    MEASUREMENT_KEYWORDS = ['measurement', 'sensor', 'måling', 'proces', 'process', 'value']
    
    def __init__(self, ads_client):
        self.ads_client = ads_client
    
    def scan_and_generate_config(self, config_file: str = 'config.json') -> bool:
        """
        Scan PLC and generate/update config.json
        
        Args:
            config_file: Path to config file
            
        Returns:
            True if successful
        """
        try:
            logger.info("Starting automatic symbol scan...")
            
            # Get all symbols
            symbols = self.ads_client.plc.get_all_symbols()
            logger.info(f"Found {len(symbols)} total symbols")
            
            # Filter to GVL symbols (or other relevant prefix)
            gvl_symbols = [s for s in symbols if s.name.startswith('GVL.')]
            logger.info(f"Found {len(gvl_symbols)} GVL symbols")
            
            # Analyze symbols
            analyzed_symbols = {}
            for symbol in gvl_symbols:
                config = self._analyze_symbol(symbol)
                if config:
                    analyzed_symbols[symbol.name] = config
            
            logger.info(f"Analyzed {len(analyzed_symbols)} symbols")
            
            # Load existing config
            config_path = Path(config_file)
            if config_path.exists():
                # Backup existing config
                backup_path = config_path.with_suffix('.json.backup')
                with open(config_path, 'r') as f:
                    existing_config = json.load(f)
                with open(backup_path, 'w') as f:
                    json.dump(existing_config, f, indent=2)
                logger.info(f"Backed up existing config to {backup_path}")
            else:
                existing_config = self._get_default_config()
            
            # Update manual_symbols section
            existing_config['manual_symbols'] = {
                'enabled': True,
                'auto_discovered': True,
                'last_scan': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'symbols': analyzed_symbols
            }
            
            # Save updated config
            with open(config_path, 'w') as f:
                json.dump(existing_config, f, indent=2)
            
            logger.info(f"Config saved to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to scan and generate config: {e}", exc_info=True)
            return False
    
    def _analyze_symbol(self, symbol) -> Optional[Dict[str, Any]]:
        """
        Analyze a single symbol and determine its configuration
        
        Args:
            symbol: pyads symbol object
            
        Returns:
            Configuration dict or None if symbol should be skipped
        """
        try:
            symbol_name = symbol.name
            data_type = str(symbol.plc_type) if hasattr(symbol, 'plc_type') else ''
            comment = symbol.comment if hasattr(symbol, 'comment') and symbol.comment else ''
            
            # Skip version info and system symbols
            if any(skip in symbol_name.lower() for skip in ['version', 'system', 'constant']):
                logger.debug(f"Skipping {symbol_name}: system symbol")
                return None
            
            # Skip symbols without useful types
            if 'None' in data_type or not data_type:
                logger.debug(f"Skipping {symbol_name}: no type info")
                return None
            
            config = {}
            
            # Determine category
            category = self._determine_category(symbol_name, comment, data_type)
            if not category:
                logger.debug(f"Skipping {symbol_name}: no category (type={data_type}, comment='{comment[:50]}')")
                return None
            
            logger.info(f"Categorized {symbol_name} as {category}")
            config['category'] = category
            
            # Extract unit
            unit = self._extract_unit(comment)
            if unit:
                config['unit'] = unit
            
            # Category-specific configuration
            if category in ['setpoint', 'process_value']:
                config.update(self._analyze_numeric_symbol(symbol_name, comment, data_type))
            elif category == 'switch':
                config.update(self._analyze_switch_symbol(symbol_name, comment))
            elif category == 'alarm':
                config.update(self._analyze_alarm_symbol(symbol_name, comment))
            
            # Extract alarm limits from comment
            alarm_limits = self._extract_alarm_limits(comment)
            if alarm_limits:
                config.update(alarm_limits)
            
            return config
            
        except Exception as e:
            logger.warning(f"Error analyzing symbol {symbol.name}: {e}")
            return None
    
    def _determine_category(self, name: str, comment: str, data_type: str) -> Optional[str]:
        """
        Determine symbol category using multiple strategies
        Works even when HMI markers are not exported by TwinCAT
        """
        name_lower = name.lower()
        comment_lower = comment.lower()
        data_type_upper = data_type.upper()
        
        logger.debug(f"Analyzing {name}: type={data_type}, comment='{comment}'")
        
        # Strategy 1: Check for HMI tags in comment (most reliable when available)
        if 'hmi_sp' in comment_lower:
            logger.debug(f"  -> setpoint (HMI_SP marker)")
            return 'setpoint'
        if 'hmi_pv' in comment_lower:
            logger.debug(f"  -> process_value (HMI_PV marker)")
            return 'process_value'
        if 'hmi_switch' in comment_lower:
            logger.debug(f"  -> switch (HMI_SWITCH marker)")
            return 'switch'
        if 'hmi_alarm' in comment_lower:
            logger.debug(f"  -> alarm (HMI_ALARM marker)")
            return 'alarm'
        
        # Strategy 2: BOOL type detection
        if 'BOOL' in data_type_upper:
            # Check for alarm-like names or comments
            alarm_patterns = ['fejl', 'fault', 'error', 'alarm', 'warning', 'advarsel', 
                            'nod', 'emergency', 'lav', 'hoj', 'low', 'high', 'reminder', 'paamindelse']
            text = name_lower + ' ' + comment_lower
            if any(pattern in text for pattern in alarm_patterns):
                return 'alarm'
            # Skip other BOOLs (status flags, etc.)
            return None
        
        # Strategy 3: INT/DINT type - likely switches
        # Note: pyads returns ctypes like 'c_short', 'c_int', 'c_long' for INT/DINT
        if any(t in data_type_upper for t in ['INT', 'DINT', 'SHORT', 'LONG']):
            # Combine name and comment for keyword search
            text = name_lower + ' ' + comment_lower
            
            logger.debug(f"  -> INT type, analyzing text='{text[:80]}'")
            
            # Check for switch/mode/selector keywords in name OR comment
            if any(kw in text for kw in self.SWITCH_KEYWORDS):
                logger.debug(f"  -> switch (found switch keyword)")
                return 'switch'
            # Check for position indicators in comment
            if re.search(r'pos\d', text):
                logger.debug(f"  -> switch (found pos indicator)")
                return 'switch'
            # Check for drift/mode/valg in name or comment
            if any(word in text for word in ['drift', 'mode', 'valg', 'select', 'priorit', 'choice', 'option', 'pump', 'pumpe']):
                logger.debug(f"  -> switch (found mode/select keyword)")
                return 'switch'
            logger.debug(f"  -> None (INT but no switch indicators)")
            return None
        
        # Strategy 4: REAL/LREAL type - distinguish setpoint vs process value
        # Note: pyads returns ctypes like 'c_float', 'c_double' for REAL/LREAL
        if 'REAL' in data_type_upper or 'LREAL' in data_type_upper or 'FLOAT' in data_type_upper or 'DOUBLE' in data_type_upper:
            # Combine name and comment for analysis
            text = name_lower + ' ' + comment_lower
            
            logger.debug(f"  -> REAL type, analyzing text='{text[:80]}'")
            
            # Strong setpoint indicators - check in both name AND comment
            setpoint_indicators = ['setpunkt', 'setpoint', 'sp_', '_sp', 'sollwert', 'target']
            if any(ind in text for ind in setpoint_indicators):
                logger.debug(f"  -> setpoint (found setpoint indicator)")
                return 'setpoint'
            
            # Check for measurement words in name or comment
            measurement_words = ['temperatur', 'temp', 'tryk', 'pressure', 'flow', 
                               'niveau', 'level', 'hastighed', 'speed', 'position',
                               'sensor', 'measurement', 'måling', 'proces', 'process']
            is_measurement = any(word in text for word in measurement_words)
            
            logger.debug(f"  -> is_measurement={is_measurement}")
            
            # Check if comment has units (indicates it's a measured value)
            has_unit = any(unit.lower() in comment_lower for unit in self.UNITS)
            
            # Check for alarm limits in comment (indicates it's monitored = process value)
            has_alarm_limits = any(word in comment_lower for word in 
                                  ['alarmhigh', 'alarmlow', 'high', 'low', 'limit'])
            
            # If it's clearly a measurement, it's a process value
            if is_measurement:
                # Unless it explicitly says "setpoint" in name
                if any(ind in name_lower for ind in setpoint_indicators):
                    logger.debug(f"  -> setpoint (measurement + setpoint in name)")
                    return 'setpoint'
                logger.debug(f"  -> process_value (is measurement)")
                return 'process_value'
            
            # If has units or alarm limits, likely process value
            if has_unit or has_alarm_limits:
                logger.debug(f"  -> process_value (has unit or alarm limits)")
                return 'process_value'
            
            # Default for REAL - assume it's a process value
            # (Most REAL variables in PLC are measurements, not setpoints)
            logger.debug(f"  -> process_value (default for REAL)")
            return 'process_value'
        
        logger.debug(f"  -> None (no category match)")
        return None
    
    def _extract_unit(self, comment: str) -> Optional[str]:
        """Extract unit from comment"""
        for unit in self.UNITS:
            if unit in comment:
                return unit
        
        # Check for common patterns
        match = re.search(r'\[([^\]]+)\]', comment)
        if match:
            potential_unit = match.group(1)
            if len(potential_unit) < 10:  # Reasonable unit length
                return potential_unit
        
        return None
    
    def _analyze_numeric_symbol(self, name: str, comment: str, data_type: str) -> Dict:
        """Analyze numeric symbol (REAL, INT, etc.)"""
        config = {}
        
        # Determine decimals based on type
        if 'REAL' in data_type.upper() or 'LREAL' in data_type.upper():
            config['decimals'] = 2
        else:
            config['decimals'] = 0
        
        # Try to extract min/max from comment
        min_match = re.search(r'min[:\s=]+(\d+(?:\.\d+)?)', comment.lower())
        max_match = re.search(r'max[:\s=]+(\d+(?:\.\d+)?)', comment.lower())
        
        if min_match:
            config['min'] = float(min_match.group(1))
        else:
            config['min'] = 0
        
        if max_match:
            config['max'] = float(max_match.group(1))
        else:
            # Default max based on unit
            unit = self._extract_unit(comment)
            if unit == '%':
                config['max'] = 100
            elif unit in ['°C', '°F']:
                config['max'] = 200
            elif unit == 'bar':
                config['max'] = 10
            else:
                config['max'] = 100
        
        # Step for setpoints
        if config.get('decimals', 0) > 0:
            config['step'] = 0.1
        else:
            config['step'] = 1
        
        return config
    
    def _analyze_switch_symbol(self, name: str, comment: str) -> Dict:
        """Analyze switch symbol and determine position labels"""
        config = {'positions': {}}
        
        # Try to extract positions from comment
        # Look for patterns like "Pos0 := 'Stop'" or "0: Stop"
        pos_patterns = [
            r'pos(\d+)[:\s]*[:=]+\s*[\'"]([^\'"]+)[\'"]',  # Pos0 := 'Stop'
            r'(\d+)[:\s]*[:=]+\s*[\'"]([^\'"]+)[\'"]',      # 0: Stop
            r'(\d+)\s*[-=]\s*([^\n,;]+)',                   # 0 - Stop
        ]
        
        found_positions = {}
        for pattern in pos_patterns:
            matches = re.finditer(pattern, comment, re.IGNORECASE)
            for match in matches:
                pos_num = match.group(1)
                pos_label = match.group(2).strip()
                found_positions[pos_num] = pos_label
        
        if found_positions:
            config['positions'] = found_positions
            return config
        
        # If no positions found in comment, use intelligent defaults based on name
        name_lower = name.lower()
        comment_lower = comment.lower()
        
        # Common switch patterns (Danish and English)
        if any(word in name_lower for word in ['drift', 'mode', 'operation']):
            # Operating mode: Stop / Manual / Auto
            config['positions'] = {
                '0': 'Stop',
                '1': 'Auto',
                '2': 'Manuel'
            }
        elif any(word in name_lower for word in ['pumpe', 'pump', 'motor']):
            # Pump/Motor selection
            config['positions'] = {
                '0': 'Fra',
                '1': 'Pumpe 1',
                '2': 'Pumpe 2',
                '3': 'Begge'
            }
        elif any(word in name_lower for word in ['prioritet', 'priority']):
            # Priority levels
            config['positions'] = {
                '0': 'Normal',
                '1': 'Høj',
                '2': 'Kritisk'
            }
        elif any(word in name_lower for word in ['valg', 'select', 'choice']):
            # Generic selection
            config['positions'] = {
                '0': 'Valg 0',
                '1': 'Valg 1',
                '2': 'Valg 2',
                '3': 'Valg 3'
            }
        else:
            # Generic default positions
            config['positions'] = {
                '0': 'Position 0',
                '1': 'Position 1',
                '2': 'Position 2',
                '3': 'Position 3'
            }
        
        return config
    
    def _analyze_alarm_symbol(self, name: str, comment: str) -> Dict:
        """Analyze alarm symbol (BOOL)"""
        config = {}
        
        # Extract alarm text from comment or use name
        alarm_text_match = re.search(r'alarmtext[:\s=]+[\'"]([^\'"]+)[\'"]', comment.lower())
        if alarm_text_match:
            config['alarm_text'] = alarm_text_match.group(1)
        else:
            # Use first line of comment or cleaned name
            first_line = comment.split('\n')[0].strip()
            if first_line and len(first_line) < 50:
                config['alarm_text'] = first_line
            else:
                # Clean up name
                alarm_text = name.split('.')[-1]
                alarm_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', alarm_text)
                config['alarm_text'] = alarm_text
        
        # Try to determine priority from comment or name
        priority = 2  # Default to HIGH
        
        priority_match = re.search(r'priority[:\s=]+(\d+)', comment.lower())
        if priority_match:
            priority = int(priority_match.group(1))
        else:
            # Guess from keywords
            text = (name + ' ' + comment).lower()
            if any(kw in text for kw in ['critical', 'kritisk', 'emergency', 'nød']):
                priority = 1
            elif any(kw in text for kw in ['warning', 'advarsel', 'medium']):
                priority = 2
            elif any(kw in text for kw in ['info', 'low', 'lav']):
                priority = 4
        
        config['alarm_priority'] = priority
        
        return config
    
    def _extract_alarm_limits(self, comment: str) -> Dict:
        """Extract alarm limits from comment"""
        limits = {}
        
        # Patterns for alarm limits
        patterns = {
            'alarm_high_high': [r'highhigh[:\s=]+(\d+(?:\.\d+)?)', r'hh[:\s=]+(\d+(?:\.\d+)?)'],
            'alarm_high': [r'(?<!high)high[:\s=]+(\d+(?:\.\d+)?)', r'(?<!h)h[:\s=]+(\d+(?:\.\d+)?)'],
            'alarm_low': [r'(?<!low)low[:\s=]+(\d+(?:\.\d+)?)', r'(?<!l)l[:\s=]+(\d+(?:\.\d+)?)'],
            'alarm_low_low': [r'lowlow[:\s=]+(\d+(?:\.\d+)?)', r'll[:\s=]+(\d+(?:\.\d+)?)'],
        }
        
        comment_lower = comment.lower()
        
        for limit_name, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, comment_lower)
                if match:
                    limits[limit_name] = float(match.group(1))
                    break
        
        # Try to extract priority
        priority_match = re.search(r'priority[:\s=]+(\d+)', comment_lower)
        if priority_match:
            limits['alarm_priority'] = int(priority_match.group(1))
        
        return limits
    
    def _get_default_config(self) -> Dict:
        """Get default config structure"""
        return {
            "ads": {
                "ams_net_id": "127.0.0.1.1.1",
                "ams_port": 851,
                "update_interval": 1.0
            },
            "alarms": {
                "enabled": True,
                "sound_enabled": True,
                "blink_interval": 500,
                "auto_acknowledge": False,
                "log_to_csv": True,
                "hysteresis_percent": 2.0
            },
            "symbol_search": {
                "enabled": True,
                "search_patterns": [
                    "HMI_SP",
                    "HMI_PV",
                    "HMI_SWITCH",
                    "HMI_ALARM"
                ]
            },
            "gui": {
                "window_title": "TwinCAT HMI",
                "window_width": 1200,
                "window_height": 800,
                "alarm_banner_max_visible": 5
            }
        }
