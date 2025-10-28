"""
TPY File Parser - Reads TwinCAT Python interface files
Requires access to TwinCAT project folder
"""
import re
from pathlib import Path
from typing import Dict, List, Any


class TPYParser:
    """Parse TwinCAT TPY (Python interface) files"""
    
    def __init__(self, tpy_file_path: str):
        """
        Initialize TPY parser
        
        Args:
            tpy_file_path: Path to .tpy file
        """
        self.tpy_path = Path(tpy_file_path)
        if not self.tpy_path.exists():
            raise FileNotFoundError(f"TPY file not found: {tpy_file_path}")
        
        with open(self.tpy_path, 'r', encoding='utf-8') as f:
            self.content = f.read()
    
    def extract_attributes(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract all attribute definitions from TPY file
        
        Returns:
            Dictionary mapping symbol names to their attributes
        """
        symbols = {}
        
        # Pattern for attribute declarations: {attribute 'Name' := 'Value'}
        # Common in structured comments
        attr_pattern = r"\{attribute\s+'([^']+)'\s*:=\s*'([^']*)'\}"
        
        # Pattern for class/variable definitions with attributes
        class_pattern = r"class\s+(\w+).*?(?=class|\Z)"
        
        for match in re.finditer(class_pattern, self.content, re.DOTALL):
            class_name = match.group(1)
            class_body = match.group(0)
            
            # Find all attributes in this class
            attributes = {}
            for attr_match in re.finditer(attr_pattern, class_body):
                attr_name = attr_match.group(1)
                attr_value = attr_match.group(2)
                attributes[attr_name] = attr_value
            
            if attributes:
                symbols[class_name] = attributes
        
        return symbols
    
    def print_symbols(self):
        """Pretty print all symbols with attributes"""
        symbols = self.extract_attributes()
        
        if not symbols:
            print("No symbols with attributes found in TPY file")
            return
        
        print(f"Found {len(symbols)} symbols with attributes:\n")
        
        for symbol_name, attributes in symbols.items():
            print(f"Symbol: {symbol_name}")
            for attr_name, attr_value in attributes.items():
                print(f"  {attr_name} = {attr_value}")
            print()


def main():
    """Test TPY parser"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: py tpy_parser.py <path_to_tpy_file>")
        print("\nExample:")
        print("  py tpy_parser.py C:/TwinCAT/Projects/MyProject/_Config/PLC/MyPLC.tpy")
        return
    
    tpy_file = sys.argv[1]
    
    try:
        print(f"Parsing TPY file: {tpy_file}\n")
        print("=" * 80)
        parser = TPYParser(tpy_file)
        parser.print_symbols()
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error parsing TPY: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
