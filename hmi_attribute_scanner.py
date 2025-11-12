"""
HMI Attribute Scanner
Scans TwinCAT PLC for symbols with {attribute 'HMI'} using TMC file parser
and builds automatic symbol catalog.
"""

import pyads
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
from tmc_parser import TMCParser

logger = logging.getLogger(__name__)


@dataclass
class SymbolInfo:
    """Information about a discovered HMI symbol"""
    full_path: str
    category: str  # 'setpoint', 'process_value', 'switch', 'alarm'
    struct_type: str
    display_name: str
    parent_path: str


class HMIAttributeScanner:
    """
    Scanner PLC for symbols med {attribute 'HMI'} via TMC fil
    og bygger automatisk symbol katalog
    """
    
    # Mapping fra attribute type til HMI category
    ATTRIBUTE_TYPE_MAP = {
        'HMI_SP': 'setpoint',
        'HMI_PV': 'process_value',
        'HMI_SWITCH': 'switch',
        'HMI_ALARM': 'alarm',
    }
    
    def __init__(self, plc_connection: pyads.Connection, tmc_path: Optional[str] = None):
        """
        Initialize scanner with PLC connection and optional TMC path
        
        Args:
            plc_connection: Active pyads Connection object
            tmc_path: Path to .tmc file or directory containing it
        """
        self.plc = plc_connection
        self.tmc_path = tmc_path
        self.discovered_symbols = {}
        self.tmc_parser = None
        
    def scan_for_hmi_attributes(self) -> List[str]:
        """
        Scan TMC fil for symboler med HMI structs (ST_HMI_*)
        
        Returns:
            Liste af symbol paths til HMI structs, f.eks. ['MAIN.Motor01.HMI', ...]
        """
        logger.info("Starting scan for HMI symbols using TMC parser...")
        hmi_paths = []
        
        try:
            # Find TMC file hvis ikke angivet
            if not self.tmc_path:
                self.tmc_path = self._find_tmc_file()
                if not self.tmc_path:
                    logger.warning("No TMC file specified or found. Returning empty list.")
                    return []
            
            # Parse TMC file med expansion
            logger.info(f"Parsing TMC file: {self.tmc_path}")
            symbols, datatypes = self._parse_tmc_with_expansion()
            
            # Find symboler med ST_HMI_* typer
            hmi_paths = self._find_hmi_symbols_recursive(symbols)
            
            logger.info(f"Scan complete. Found {len(hmi_paths)} HMI symbols")
            return hmi_paths
            
        except Exception as e:
            logger.error(f"Error during HMI attribute scan: {e}", exc_info=True)
            raise
    
    def _find_tmc_file(self) -> Optional[str]:
        """
        Find TMC file i standard TwinCAT locations
        
        Returns:
            Path til TMC fil eller None
        """
        # Common TwinCAT locations
        search_paths = [
            r"C:\TwinCAT\3.1\Boot\Plc",
            r"C:\Users\Rune\Documents\TcXaeShell\Easy_TwincatHMI\Easy_TwincatHMI\PLC",
        ]
        
        for search_path in search_paths:
            path = Path(search_path)
            if path.exists():
                tmc_files = list(path.glob('*.tmc'))
                if tmc_files:
                    logger.info(f"Found TMC file: {tmc_files[0]}")
                    return str(tmc_files[0])
        
        return None
    
    def _parse_tmc_with_expansion(self) -> tuple:
        """
        Parse TMC file med fuld expansion af strukturer (som test_get_all_hmi_variables_in_tmc.py)
        
        Returns:
            Tuple af (symbols list, datatypes list)
        """
        import xml.etree.ElementTree as ET
        
        try:
            tree = ET.parse(self.tmc_path)
            root = tree.getroot()
            
            all_symbols = []
            all_datatypes = []
            
            # Parse DataTypes først
            for datatype_elem in root.findall('.//DataTypes/DataType'):
                datatype = self._parse_datatype_element(datatype_elem)
                if datatype:
                    all_datatypes.append(datatype)
            
            # Create lookup dictionary
            datatype_lookup = {dt['name']: dt for dt in all_datatypes}
            
            # Parse Symbols og expand dem
            for symbol_elem in root.findall('.//DataArea/Symbol'):
                symbol = self._parse_symbol_element(symbol_elem)
                if symbol:
                    # Filter for MAIN og GVL
                    if symbol['name'].startswith('MAIN.') or symbol['name'].startswith('GVL.'):
                        # Expand med datatype structure
                        self._expand_symbol_with_datatype(symbol, datatype_lookup)
                        all_symbols.append(symbol)
            
            # Cache parsed symbols for later type lookup
            self._parsed_symbols = all_symbols
            
            logger.info(f"Parsed {len(all_symbols)} symbols and {len(all_datatypes)} datatypes")
            return all_symbols, all_datatypes
            
        except Exception as e:
            logger.error(f"Failed to parse TMC file: {e}", exc_info=True)
            return [], []
    
    def _parse_datatype_element(self, datatype_elem) -> dict:
        """Parse DataType element fra TMC"""
        import xml.etree.ElementTree as ET
        
        name_elem = datatype_elem.find('Name')
        if name_elem is None or not name_elem.text:
            return None
        
        datatype = {
            'name': name_elem.text,
            'sub_items': []
        }
        
        # Parse SubItems
        for subitem_elem in datatype_elem.findall('SubItem'):
            subitem = self._parse_subitem_element(subitem_elem, datatype['name'])
            if subitem:
                datatype['sub_items'].append(subitem)
        
        return datatype
    
    def _parse_symbol_element(self, symbol_elem) -> dict:
        """Parse Symbol element fra TMC"""
        name_elem = symbol_elem.find('Name')
        if name_elem is None or not name_elem.text:
            return None
        
        name = name_elem.text
        
        symbol = {
            'name': name,
            'full_path': name,
            'base_type': None,
            'sub_items': []
        }
        
        # Get BaseType
        basetype_elem = symbol_elem.find('BaseType')
        if basetype_elem is not None and basetype_elem.text:
            symbol['base_type'] = basetype_elem.text
        
        return symbol
    
    def _parse_subitem_element(self, subitem_elem, parent_path: str) -> dict:
        """Parse SubItem element"""
        name_elem = subitem_elem.find('Name')
        if name_elem is None or not name_elem.text:
            return None
        
        name = name_elem.text
        
        subitem = {
            'name': name,
            'full_path': f"{parent_path}.{name}",
            'type': None,
            'sub_items': []
        }
        
        # Get Type
        type_elem = subitem_elem.find('Type')
        if type_elem is not None and type_elem.text:
            subitem['type'] = type_elem.text
        
        # Rekursiv parse nested SubItems
        for nested_elem in subitem_elem.findall('SubItem'):
            nested = self._parse_subitem_element(nested_elem, subitem['full_path'])
            if nested:
                subitem['sub_items'].append(nested)
        
        return subitem
    
    def _expand_symbol_with_datatype(self, symbol: dict, datatype_lookup: dict, depth: int = 0, max_depth: int = 10):
        """Expand symbol med datatype structure (rekursiv)"""
        if depth >= max_depth:
            return
        
        base_type = symbol.get('base_type', symbol.get('type', ''))
        
        if base_type in datatype_lookup:
            datatype = datatype_lookup[base_type]
            
            if datatype.get('sub_items') and not symbol.get('sub_items'):
                symbol['sub_items'] = []
                
                for dt_subitem in datatype['sub_items']:
                    expanded_subitem = {
                        'name': dt_subitem['name'],
                        'full_path': f"{symbol.get('full_path', symbol['name'])}.{dt_subitem['name']}",
                        'type': dt_subitem['type'],
                        'sub_items': []
                    }
                    
                    # Rekursiv expansion
                    self._expand_symbol_with_datatype(expanded_subitem, datatype_lookup, depth + 1, max_depth)
                    
                    symbol['sub_items'].append(expanded_subitem)
        
        # Expand eksisterende sub_items
        for subitem in symbol.get('sub_items', []):
            self._expand_symbol_with_datatype(subitem, datatype_lookup, depth + 1, max_depth)
    
    def _find_hmi_symbols_recursive(self, symbols: list) -> List[str]:
        """Find alle symboler med ST_HMI_* typer rekursivt"""
        hmi_paths = []
        
        for symbol in symbols:
            self._search_for_hmi_types(symbol, hmi_paths)
        
        return hmi_paths
    
    def _search_for_hmi_types(self, symbol: dict, hmi_paths: list):
        """Søg rekursivt efter ST_HMI_* typer"""
        # Check om denne symbol har en ST_HMI_* type
        symbol_type = symbol.get('base_type') or symbol.get('type', '')
        
        if symbol_type.startswith('ST_HMI_'):
            full_path = symbol.get('full_path', symbol.get('name', ''))
            hmi_paths.append(full_path)
            logger.debug(f"Found HMI symbol: {full_path} (type: {symbol_type})")
        
        # Søg i sub_items
        for subitem in symbol.get('sub_items', []):
            self._search_for_hmi_types(subitem, hmi_paths)
    
    def analyze_hmi_symbol(self, symbol_path: str) -> Dict[str, SymbolInfo]:
        """
        Analyser et enkelt HMI symbol og extract metadata
        
        Args:
            symbol_path: f.eks. "MAIN.Motor01.HMI" eller "MAIN.Motor01.HMI.SpeedSetpoint"
            
        Returns:
            Dictionary med symbol info for hvert HMI sub-symbol
        """
        logger.info(f"Analyzing HMI symbol: {symbol_path}")
        symbols = {}
        
        try:
            # Get type from TMC data
            struct_type = self._get_symbol_type_from_tmc(symbol_path)
            
            # Extract parts
            parts = symbol_path.split('.')
            symbol_name = parts[-1]
            
            # Map from struct type to category
            category = self._map_struct_type_to_category(struct_type)
            
            if category:
                symbol_info = SymbolInfo(
                    full_path=symbol_path,
                    category=category,
                    struct_type=struct_type or 'UNKNOWN',
                    display_name=symbol_name,
                    parent_path='.'.join(parts[:-1])
                )
                
                symbols[symbol_path] = symbol_info
                self.discovered_symbols[symbol_path] = symbol_info
                logger.debug(f"  Found {category}: {symbol_path} (type: {struct_type})")
            
            return symbols
            
        except Exception as e:
            logger.error(f"Error analyzing HMI symbol {symbol_path}: {e}", exc_info=True)
            return {}
    
    def _get_symbol_type_from_tmc(self, symbol_path: str) -> Optional[str]:
        """Get symbol type from cached TMC data"""
        if not hasattr(self, '_parsed_symbols'):
            return None
        
        # Search through parsed symbols recursively
        for symbol in self._parsed_symbols:
            symbol_type = self._find_symbol_type_recursive(symbol, symbol_path)
            if symbol_type:
                return symbol_type
        
        return None
    
    def _find_symbol_type_recursive(self, symbol: dict, target_path: str) -> Optional[str]:
        """Find type of symbol by path recursively"""
        if symbol.get('full_path') == target_path:
            return symbol.get('base_type') or symbol.get('type')
        
        for subitem in symbol.get('sub_items', []):
            result = self._find_symbol_type_recursive(subitem, target_path)
            if result:
                return result
        
        return None
    
    def _map_struct_type_to_category(self, struct_type: Optional[str]) -> Optional[str]:
        """Map ST_HMI_* type to category"""
        if not struct_type:
            return None
        
        type_map = {
            'ST_HMI_Setpoint': 'setpoint',
            'ST_HMI_ProcessValue': 'process_value',
            'ST_HMI_Switch': 'switch',
            'ST_HMI_Alarm': 'alarm',
        }
        
        return type_map.get(struct_type)
    
    def _determine_category_from_type(self, symbol_name: str) -> Optional[str]:
        """
        Determine HMI category from symbol name or type
        
        Args:
            symbol_name: Last part of path or type name
            
        Returns:
            Category string or None
        """
        # Check for common naming patterns first (most specific)
        name_lower = symbol_name.lower()
        
        # Check for process value indicators (før setpoint check!)
        if 'speed' in name_lower or 'current' in name_lower or 'actual' in name_lower:
            return 'process_value'
        elif 'temperature' in name_lower or 'pressure' in name_lower or 'flow' in name_lower:
            return 'process_value'
        elif 'sensor' in name_lower or 'value' in name_lower or 'measurement' in name_lower:
            return 'process_value'
        
        # Check for setpoint indicators
        elif 'setpoint' in name_lower or 'sp' in name_lower or 'target' in name_lower:
            return 'setpoint'
        
        # Check for switch/mode
        elif 'switch' in name_lower or 'mode' in name_lower or 'position' in name_lower:
            return 'switch'
        
        # Check for alarm
        elif 'alarm' in name_lower or 'fault' in name_lower or 'error' in name_lower:
            return 'alarm'
        
        return None
    
    def _determine_category_from_attributes(self, attributes: Dict[str, str]) -> Optional[str]:
        """
        Determine HMI category from TMC attributes
        
        Args:
            attributes: Dictionary of symbol attributes from TMC
            
        Returns:
            Category string or None
        """
        for attr_name in self.ATTRIBUTE_TYPE_MAP:
            if attr_name in attributes:
                return self.ATTRIBUTE_TYPE_MAP[attr_name]
        
        return None
    
    def get_symbol_attributes(self, symbol_path: str) -> Dict[str, str]:
        """
        Get all attributes for a symbol from TMC data
        
        Args:
            symbol_path: Full path to symbol (e.g., 'GVL.TemperaturSetpunkt')
            
        Returns:
            Dictionary of attributes (Unit, Min, Max, etc.)
        """
        if not self.tmc_parser:
            logger.warning("TMC parser not initialized")
            return {}
        
        tmc_symbols = self.tmc_parser.get_all_symbols()
        symbol_data = next((s for s in tmc_symbols if s['name'] == symbol_path), None)
        
        if symbol_data:
            return symbol_data.get('attributes', {})
        
        return {}
    
    def get_all_discovered_symbols(self) -> Dict[str, List[SymbolInfo]]:
        """
        Få alle opdagede symboler kategoriseret
        
        Returns:
            Dictionary med symboler grupperet efter category:
            {
                'setpoints': [SymbolInfo, ...],
                'process_values': [SymbolInfo, ...],
                'switches': [SymbolInfo, ...],
                'alarms': [SymbolInfo, ...]
            }
        """
        categorized = {
            'setpoints': [],
            'process_values': [],
            'switches': [],
            'alarms': []
        }
        
        for symbol_info in self.discovered_symbols.values():
            if symbol_info.category == 'setpoint':
                categorized['setpoints'].append(symbol_info)
            elif symbol_info.category == 'process_value':
                categorized['process_values'].append(symbol_info)
            elif symbol_info.category == 'switch':
                categorized['switches'].append(symbol_info)
            elif symbol_info.category == 'alarm':
                categorized['alarms'].append(symbol_info)
                
        return categorized
    
    def get_symbol_with_metadata(self, symbol_path: str) -> Optional[Dict]:
        """
        Få symbol med fuld metadata (type, comment, attributes)
        
        Args:
            symbol_path: Path til symbol i PLC
            
        Returns:
            Dictionary med metadata eller None hvis fejl:
            {
                'name': 'Motor[1].HMI',
                'type': 'ST_HMI_Motor',
                'comment': '{attribute 'HMI'} Motor HMI interface',
                'size': 256,
                'sub_items': [...]
            }
        """
        try:
            symbol = self.plc.get_symbol(symbol_path)
            
            metadata = {
                'name': symbol.name,
                'type': symbol.plc_type if hasattr(symbol, 'plc_type') else 'UNKNOWN',
                'comment': symbol.comment if hasattr(symbol, 'comment') else '',
                'size': symbol.size if hasattr(symbol, 'size') else 0,
                'sub_items': []
            }
            
            # Få sub-items hvis det er en STRUCT
            if hasattr(symbol, 'sub_items') or hasattr(symbol, 'subitems'):
                items = symbol.sub_items if hasattr(symbol, 'sub_items') else symbol.subitems
                for sub in items:
                    metadata['sub_items'].append({
                        'name': sub.name,
                        'type': sub.plc_type if hasattr(sub, 'plc_type') else 'UNKNOWN'
                    })
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get metadata for {symbol_path}: {e}")
            return None
