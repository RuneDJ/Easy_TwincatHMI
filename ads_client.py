"""
ADS Client for TwinCAT 3 Communication
Handles connection, symbol reading/writing, and symbol discovery
"""

import pyads
import logging
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ADSClient:
    """ADS Client for TwinCAT 3 communication"""
    
    def __init__(self, ams_net_id: str, ams_port: int):
        """
        Initialize ADS client
        
        Args:
            ams_net_id: AMS Net ID (e.g., "127.0.0.1.1.1")
            ams_port: AMS Port (typically 851 for PLC runtime)
        """
        self.ams_net_id = ams_net_id
        self.ams_port = ams_port
        self.plc = None
        self.connected = False
        self.symbol_info_cache = {}
        
    def connect(self) -> bool:
        """
        Connect to TwinCAT PLC
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.plc = pyads.Connection(self.ams_net_id, self.ams_port)
            self.plc.open()
            self.connected = True
            logger.info(f"Connected to PLC: {self.ams_net_id}:{self.ams_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PLC: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from TwinCAT PLC"""
        if self.plc and self.connected:
            try:
                self.plc.close()
                self.connected = False
                logger.info("Disconnected from PLC")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
    
    def read_symbol(self, symbol_name: str) -> Optional[Any]:
        """
        Read symbol value from PLC
        
        Args:
            symbol_name: Full symbol name (e.g., "GVL.TemperaturSetpunkt")
            
        Returns:
            Symbol value or None if error
        """
        if not self.connected:
            logger.warning("Not connected to PLC")
            return None
        
        try:
            value = self.plc.read_by_name(symbol_name)
            return value
        except Exception as e:
            logger.error(f"Failed to read symbol '{symbol_name}': {e}")
            return None
    
    def write_symbol(self, symbol_name: str, value: Any) -> bool:
        """
        Write value to PLC symbol
        
        Args:
            symbol_name: Full symbol name
            value: Value to write
            
        Returns:
            True if write successful, False otherwise
        """
        if not self.connected:
            logger.warning("Not connected to PLC")
            return False
        
        try:
            self.plc.write_by_name(symbol_name, value)
            logger.debug(f"Written {value} to '{symbol_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to write to symbol '{symbol_name}': {e}")
            return False
    
    def read_multiple_symbols(self, symbol_names: List[str]) -> Dict[str, Any]:
        """
        Read multiple symbols at once
        
        Args:
            symbol_names: List of symbol names
            
        Returns:
            Dictionary with symbol_name: value pairs
        """
        results = {}
        for symbol_name in symbol_names:
            value = self.read_symbol(symbol_name)
            if value is not None:
                results[symbol_name] = value
        return results
    
    def get_symbol_info(self, symbol_name: str) -> Optional[Dict]:
        """
        Get detailed information about a symbol including attributes
        
        Args:
            symbol_name: Symbol name
            
        Returns:
            Dictionary with symbol information or None
        """
        if not self.connected:
            return None
        
        # Check cache first
        if symbol_name in self.symbol_info_cache:
            return self.symbol_info_cache[symbol_name]
        
        try:
            # Get symbol handle
            symbol_info = self.plc.get_symbol(symbol_name)
            
            info = {
                'name': symbol_name,
                'data_type': symbol_info.plc_type,
                'comment': symbol_info.comment if hasattr(symbol_info, 'comment') else '',
                'attributes': self._parse_attributes(symbol_info.comment) if hasattr(symbol_info, 'comment') else {}
            }
            
            # Cache the result
            self.symbol_info_cache[symbol_name] = info
            return info
            
        except Exception as e:
            logger.error(f"Failed to get symbol info for '{symbol_name}': {e}")
            return None
    
    def _parse_attributes(self, comment: str) -> Dict[str, str]:
        """
        Parse TwinCAT attributes from comment string
        
        Args:
            comment: Symbol comment containing attributes
            
        Returns:
            Dictionary of attribute key-value pairs
        """
        attributes = {}
        if not comment:
            return attributes
        
        # TwinCAT attributes are typically in format:
        # {attribute 'Key' := 'Value'}
        import re
        pattern = r"\{attribute\s+'([^']+)'\s*:=\s*'([^']+)'\}"
        matches = re.findall(pattern, comment)
        
        for key, value in matches:
            attributes[key] = value
        
        return attributes
    
    def discover_symbols(self, patterns: List[str] = None) -> Dict[str, Dict]:
        """
        Discover all symbols in PLC, optionally filtered by attribute patterns
        
        Args:
            patterns: List of attribute patterns to search for (e.g., ['HMI_SP', 'HMI_PV'])
            
        Returns:
            Dictionary of symbol_name: symbol_info pairs
        """
        if not self.connected:
            logger.warning("Not connected to PLC")
            return {}
        
        discovered_symbols = {}
        
        try:
            # Get all symbols from PLC
            symbols = self.plc.get_all_symbols()
            logger.info(f"Found {len(symbols)} total symbols in PLC")
            
            for symbol in symbols:
                symbol_name = symbol.name
                
                try:
                    # Build info dict directly from symbol object
                    info = {
                        'name': symbol_name,
                        'data_type': str(symbol.plc_type) if hasattr(symbol, 'plc_type') else 'UNKNOWN',
                        'comment': '',
                        'attributes': {}
                    }
                    
                    # Try to get comment
                    if hasattr(symbol, 'comment'):
                        info['comment'] = symbol.comment or ''
                        info['attributes'] = self._parse_attributes(info['comment'])
                    
                    # Debug: Log first few symbols
                    if len(discovered_symbols) < 3:
                        logger.debug(f"Symbol: {symbol_name}, Type: {info['data_type']}, Comment: {info['comment'][:100] if info['comment'] else 'None'}")
                    
                    # If patterns specified, filter by attributes OR by symbol name
                    if patterns:
                        attributes = info.get('attributes', {})
                        
                        # Check attributes
                        found = False
                        for pattern in patterns:
                            # Check in attribute values
                            if any(pattern in str(attr_value) for attr_value in attributes.values()):
                                discovered_symbols[symbol_name] = info
                                found = True
                                break
                            # Check in attribute keys
                            if pattern in attributes:
                                discovered_symbols[symbol_name] = info
                                found = True
                                break
                            # Check in comment text directly (fallback)
                            if pattern in info.get('comment', ''):
                                discovered_symbols[symbol_name] = info
                                found = True
                                break
                        
                        if found:
                            logger.debug(f"Added symbol: {symbol_name} (matched pattern)")
                    else:
                        # No filter, add all symbols
                        discovered_symbols[symbol_name] = info
                
                except Exception as e:
                    logger.warning(f"Error processing symbol {symbol_name}: {e}")
                    continue
            
            logger.info(f"Discovered {len(discovered_symbols)} symbols matching HMI patterns")
            
            # If no symbols found with patterns, log for debugging
            if len(discovered_symbols) == 0 and len(symbols) > 0:
                logger.warning("No symbols matched HMI patterns. Try checking a few symbols manually:")
                for i, symbol in enumerate(symbols[:5]):
                    try:
                        comment = symbol.comment if hasattr(symbol, 'comment') else 'No comment'
                        logger.info(f"  Sample {i+1}: {symbol.name} - Comment: {comment[:100] if comment else 'None'}")
                    except:
                        pass
            
            return discovered_symbols
            
        except Exception as e:
            logger.error(f"Failed to discover symbols: {e}", exc_info=True)
            return {}
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get current connection status and PLC information
        
        Returns:
            Dictionary with connection status information
        """
        status = {
            'connected': self.connected,
            'ams_net_id': self.ams_net_id,
            'ams_port': self.ams_port
        }
        
        if self.connected and self.plc:
            try:
                # Try to read PLC state
                device_info = self.plc.read_state()
                status['plc_state'] = device_info.ads_state
                status['device_state'] = device_info.device_state
            except Exception as e:
                logger.error(f"Failed to read PLC state: {e}")
                status['error'] = str(e)
        
        return status
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
