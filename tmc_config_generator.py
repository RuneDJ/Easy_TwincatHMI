"""
TMC-based Configuration Generator
Generates complete HMI configuration from TMC file with all attributes
"""
import json
from pathlib import Path
from typing import Dict, List, Any
from tmc_parser import TMCParser


class TMCConfigGenerator:
    """Generate HMI config from TMC file"""
    
    def __init__(self, tmc_file_path: str):
        """Initialize with TMC file path"""
        self.parser = TMCParser(tmc_file_path)
        self.hmi_symbols = self.parser.find_hmi_symbols()
    
    def generate_config(self) -> Dict[str, Any]:
        """
        Generate complete configuration from TMC file
        
        Returns:
            Configuration dictionary ready for config.json
        """
        config = {
            'plc': {
                'ams_net_id': '5.112.50.143.1.1',
                'port': 851
            },
            'ads': {
                'ams_net_id': '5.112.50.143.1.1',
                'ams_port': 851,
                'update_interval': 1.0
            },
            'tmc_file': '',  # Will be set by caller
            'auto_scan_on_start': False,  # Disable auto-scan when using TMC
            'symbols': {
                'setpoints': [],
                'process_values': [],
                'switches': [],
                'alarms': []
            },
            'alarms': {
                'enabled': True,
                'sound_enabled': True,
                'blink_interval': 500,
                'auto_acknowledge': False,
                'log_to_csv': True
            },
            'symbol_search': {
                'enabled': True,
                'search_patterns': ['HMI_SP', 'HMI_PV', 'HMI_SWITCH', 'HMI_ALARM']
            },
            'gui': {
                'window_title': 'TwinCAT HMI',
                'window_width': 1200,
                'window_height': 800
            }
        }
        
        # Process each HMI symbol
        for symbol in self.hmi_symbols:
            attrs = symbol['attributes']
            
            if 'HMI_SP' in attrs:
                config['symbols']['setpoints'].append(
                    self._create_setpoint_config(symbol)
                )
            elif 'HMI_PV' in attrs:
                config['symbols']['process_values'].append(
                    self._create_process_value_config(symbol)
                )
            elif 'HMI_SWITCH' in attrs:
                config['symbols']['switches'].append(
                    self._create_switch_config(symbol)
                )
            elif 'HMI_ALARM' in attrs:
                config['symbols']['alarms'].append(
                    self._create_alarm_config(symbol)
                )
        
        return config
    
    def _create_setpoint_config(self, symbol: Dict[str, Any]) -> Dict[str, Any]:
        """Create setpoint configuration from symbol"""
        attrs = symbol['attributes']
        name = symbol['name']
        
        # Create display name (remove GVL. prefix)
        display_name = name.split('.')[-1] if '.' in name else name
        
        config = {
            'name': name,
            'display_name': display_name,
            'unit': attrs.get('Unit', ''),
            'min': float(attrs.get('Min', 0)),
            'max': float(attrs.get('Max', 100)),
            'decimals': int(attrs.get('Decimals', 2)),
            'step': float(attrs.get('Step', 1.0))
        }
        
        # Add alarm limits if present
        alarm_limits = {}
        if 'AlarmHighHigh' in attrs:
            alarm_limits['high_high'] = float(attrs['AlarmHighHigh'])
        if 'AlarmHigh' in attrs:
            alarm_limits['high'] = float(attrs['AlarmHigh'])
        if 'AlarmLow' in attrs:
            alarm_limits['low'] = float(attrs['AlarmLow'])
        if 'AlarmLowLow' in attrs:
            alarm_limits['low_low'] = float(attrs['AlarmLowLow'])
        
        if alarm_limits:
            config['alarm_limits'] = alarm_limits
            config['alarm_priority'] = int(attrs.get('AlarmPriority', 3))
        
        return config
    
    def _create_process_value_config(self, symbol: Dict[str, Any]) -> Dict[str, Any]:
        """Create process value configuration from symbol"""
        attrs = symbol['attributes']
        name = symbol['name']
        
        display_name = name.split('.')[-1] if '.' in name else name
        
        config = {
            'name': name,
            'display_name': display_name,
            'unit': attrs.get('Unit', ''),
            'decimals': int(attrs.get('Decimals', 2))
        }
        
        # Add alarm limits if present
        alarm_limits = {}
        if 'AlarmHighHigh' in attrs:
            alarm_limits['high_high'] = float(attrs['AlarmHighHigh'])
        if 'AlarmHigh' in attrs:
            alarm_limits['high'] = float(attrs['AlarmHigh'])
        if 'AlarmLow' in attrs:
            alarm_limits['low'] = float(attrs['AlarmLow'])
        if 'AlarmLowLow' in attrs:
            alarm_limits['low_low'] = float(attrs['AlarmLowLow'])
        
        if alarm_limits:
            config['alarm_limits'] = alarm_limits
            config['alarm_priority'] = int(attrs.get('AlarmPriority', 3))
        
        return config
    
    def _create_switch_config(self, symbol: Dict[str, Any]) -> Dict[str, Any]:
        """Create switch configuration from symbol"""
        attrs = symbol['attributes']
        name = symbol['name']
        
        display_name = name.split('.')[-1] if '.' in name else name
        
        # Extract position labels (Pos0, Pos1, Pos2, etc.)
        positions = {}
        for key, value in attrs.items():
            if key.startswith('Pos') and key[3:].isdigit():
                pos_num = int(key[3:])
                positions[pos_num] = value
        
        # Sort positions by number
        position_labels = [positions[i] for i in sorted(positions.keys())]
        
        config = {
            'name': name,
            'display_name': display_name,
            'positions': position_labels
        }
        
        return config
    
    def _create_alarm_config(self, symbol: Dict[str, Any]) -> Dict[str, Any]:
        """Create alarm configuration from symbol"""
        attrs = symbol['attributes']
        name = symbol['name']
        
        config = {
            'name': name,
            'text': attrs.get('AlarmText', name),
            'priority': int(attrs.get('AlarmPriority', 3))
        }
        
        return config
    
    def save_config(self, output_path: str = 'config.json', tmc_file_path: str = None):
        """
        Generate and save configuration to JSON file
        
        Args:
            output_path: Path to output config file
            tmc_file_path: Path to TMC file to store in config
        """
        config = self.generate_config()
        
        # Add TMC file path if provided
        if tmc_file_path:
            config['tmc_file'] = tmc_file_path
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"Configuration saved to: {output_path}")
        
        # Print summary
        symbols = config['symbols']
        print(f"\nGenerated configuration:")
        print(f"  Setpoints: {len(symbols['setpoints'])}")
        print(f"  Process Values: {len(symbols['process_values'])}")
        print(f"  Switches: {len(symbols['switches'])}")
        print(f"  Alarms: {len(symbols['alarms'])}")
    
    def print_preview(self):
        """Print preview of generated configuration"""
        config = self.generate_config()
        
        print("=" * 80)
        print("CONFIGURATION PREVIEW")
        print("=" * 80)
        
        print("\n📊 SETPOINTS:")
        for sp in config['symbols']['setpoints']:
            print(f"\n  {sp['display_name']}")
            print(f"    Symbol: {sp['name']}")
            print(f"    Range: {sp['min']} - {sp['max']} {sp['unit']}")
            print(f"    Decimals: {sp['decimals']}, Step: {sp['step']}")
            if 'alarm_limits' in sp:
                limits = sp['alarm_limits']
                print(f"    Alarms: {limits} (Priority {sp['alarm_priority']})")
        
        print("\n📈 PROCESS VALUES:")
        for pv in config['symbols']['process_values']:
            print(f"\n  {pv['display_name']}")
            print(f"    Symbol: {pv['name']}")
            print(f"    Unit: {pv['unit']}, Decimals: {pv['decimals']}")
            if 'alarm_limits' in pv:
                limits = pv['alarm_limits']
                print(f"    Alarms: {limits} (Priority {pv['alarm_priority']})")
        
        print("\n🔘 SWITCHES:")
        for sw in config['symbols']['switches']:
            print(f"\n  {sw['display_name']}")
            print(f"    Symbol: {sw['name']}")
            print(f"    Positions: {', '.join(sw['positions'])}")
        
        print("\n🚨 ALARMS:")
        for alarm in config['symbols']['alarms']:
            print(f"\n  {alarm['text']}")
            print(f"    Symbol: {alarm['name']}")
            print(f"    Priority: {alarm['priority']}")
        
        print("\n" + "=" * 80)


def main():
    """Generate configuration from TMC file"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: py tmc_config_generator.py <path_to_tmc_file> [output_config.json]")
        print("\nExamples:")
        print('  py tmc_config_generator.py "C:\\TwinCAT\\Projects\\MyProject\\PLC\\PLC.tmc"')
        print('  py tmc_config_generator.py "C:\\TwinCAT\\Projects\\MyProject\\PLC\\PLC.tmc" my_config.json')
        return
    
    tmc_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'config_from_tmc.json'
    
    try:
        print(f"Reading TMC file: {tmc_file}\n")
        
        generator = TMCConfigGenerator(tmc_file)
        
        # Show preview
        generator.print_preview()
        
        # Save configuration
        print()
        generator.save_config(output_file, tmc_file)
        
        print(f"\n✅ Configuration generated successfully!")
        print(f"\nTo use this configuration:")
        print(f"1. Backup your current config.json")
        print(f"2. Replace config.json with {output_file}")
        print(f"3. Restart HMI application")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error generating configuration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
