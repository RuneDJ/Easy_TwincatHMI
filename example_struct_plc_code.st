(*
    TwinCAT 3 PLC Example Code with STRUCT/DUT Auto-Import
    Demonstrates how to use HMI_STRUCT attribute for automatic struct import
*)

// ========================================
// STRUCT DEFINITIONS (DUT - Data Unit Types)
// ========================================

(*
    Analog Input Struct
    Used for temperature, pressure, flow sensors, etc.
*)
TYPE ST_AnalogInput :
STRUCT
    // Process value - will be imported as Process Value widget
    {attribute 'HMI_PV'}
    {attribute 'Unit' := '°C'}
    {attribute 'Decimals' := '2'}
    {attribute 'AlarmHighHigh' := '100'}
    {attribute 'AlarmHigh' := '90'}
    {attribute 'AlarmLow' := '5'}
    {attribute 'AlarmLowLow' := '2'}
    {attribute 'AlarmPriority' := '1'}
    Value : REAL;
    
    // Scaled value (0-100%)
    {attribute 'HMI_PV'}
    {attribute 'Unit' := '%'}
    {attribute 'Decimals' := '1'}
    Scaled : REAL;
    
    // Sensor error alarm
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Sensor Kommunikationsfejl'}
    {attribute 'AlarmPriority' := '2'}
    Error : BOOL;
    
    // Calibration offset setpoint
    {attribute 'HMI_SP'}
    {attribute 'Unit' := 'Offset'}
    {attribute 'Min' := '-10'}
    {attribute 'Max' := '10'}
    {attribute 'Decimals' := '2'}
    {attribute 'Step' := '0.1'}
    CalibrationOffset : REAL;
    
    // Internal values - NOT imported (no HMI attribute)
    RawValue : INT;
    LastUpdateTime : TIME;
    SampleCount : UDINT;
END_STRUCT
END_TYPE

(*
    Motor Control Struct
    Complete motor control with setpoints and feedback
*)
TYPE ST_Motor :
STRUCT
    // Speed setpoint
    {attribute 'HMI_SP'}
    {attribute 'Unit' := 'RPM'}
    {attribute 'Min' := '0'}
    {attribute 'Max' := '3000'}
    {attribute 'Decimals' := '0'}
    {attribute 'Step' := '10'}
    SpeedSetpoint : REAL;
    
    // Actual speed
    {attribute 'HMI_PV'}
    {attribute 'Unit' := 'RPM'}
    {attribute 'Decimals' := '0'}
    {attribute 'AlarmHigh' := '3100'}
    ActualSpeed : REAL;
    
    // Current consumption
    {attribute 'HMI_PV'}
    {attribute 'Unit' := 'A'}
    {attribute 'Decimals' := '1'}
    {attribute 'AlarmHigh' := '15'}
    Current : REAL;
    
    // Run command switch
    {attribute 'HMI_SWITCH'}
    {attribute 'Pos0' := 'Stop'}
    {attribute 'Pos1' := 'Start'}
    {attribute 'Pos2' := 'Reset'}
    Command : INT;
    
    // Fault alarm
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Motor Fejl'}
    {attribute 'AlarmPriority' := '1'}
    Fault : BOOL;
    
    // Overload alarm
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Motor Overbelastet'}
    {attribute 'AlarmPriority' := '2'}
    Overload : BOOL;
    
    // Internal state - NOT imported
    InternalState : INT;
    RunningHours : TIME;
END_STRUCT
END_TYPE

(*
    PID Controller Struct
    Nested struct example
*)
TYPE ST_PIDParams :
STRUCT
    {attribute 'HMI_SP'}
    {attribute 'Min' := '0'}
    {attribute 'Max' := '100'}
    {attribute 'Decimals' := '2'}
    Kp : REAL;
    
    {attribute 'HMI_SP'}
    {attribute 'Min' := '0'}
    {attribute 'Max' := '10'}
    {attribute 'Decimals' := '3'}
    Ki : REAL;
    
    {attribute 'HMI_SP'}
    {attribute 'Min' := '0'}
    {attribute 'Max' := '10'}
    {attribute 'Decimals' := '3'}
    Kd : REAL;
END_STRUCT
END_TYPE

TYPE ST_TempController :
STRUCT
    // Temperature setpoint
    {attribute 'HMI_SP'}
    {attribute 'Unit' := '°C'}
    {attribute 'Min' := '0'}
    {attribute 'Max' := '100'}
    {attribute 'Decimals' := '1'}
    {attribute 'Step' := '0.5'}
    Setpoint : REAL;
    
    // Temperature process value
    {attribute 'HMI_PV'}
    {attribute 'Unit' := '°C'}
    {attribute 'Decimals' := '1'}
    {attribute 'AlarmHighHigh' := '98'}
    {attribute 'AlarmHigh' := '95'}
    ProcessValue : REAL;
    
    // Controller output
    {attribute 'HMI_PV'}
    {attribute 'Unit' := '%'}
    {attribute 'Decimals' := '1'}
    Output : REAL;
    
    // PID parameters (nested struct)
    // Note: PID members will also be imported if ST_PIDParams has HMI attributes
    PID : ST_PIDParams;
    
    // Control mode
    {attribute 'HMI_SWITCH'}
    {attribute 'Pos0' := 'Off'}
    {attribute 'Pos1' := 'Manual'}
    {attribute 'Pos2' := 'Automatic'}
    Mode : INT;
END_STRUCT
END_TYPE

(*
    Tank Level Monitoring
    Simple struct for level sensors
*)
TYPE ST_Tank :
STRUCT
    {attribute 'HMI_PV'}
    {attribute 'Unit' := '%'}
    {attribute 'Decimals' := '1'}
    {attribute 'AlarmHigh' := '90'}
    {attribute 'AlarmLow' := '10'}
    Level : REAL;
    
    {attribute 'HMI_PV'}
    {attribute 'Unit' := 'L'}
    {attribute 'Decimals' := '0'}
    Volume : REAL;
    
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Tank Overfyldt'}
    {attribute 'AlarmPriority' := '1'}
    OverflowAlarm : BOOL;
    
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Tank Næsten Tom'}
    {attribute 'AlarmPriority' := '3'}
    LowLevelWarning : BOOL;
END_STRUCT
END_TYPE

// ========================================
// GLOBAL VARIABLES WITH HMI_STRUCT MARKER
// ========================================

{attribute 'qualified_only'}
VAR_GLOBAL
    
    // ========================================
    // TEMPERATURE SENSORS
    // ========================================
    
    // Temperature sensor 1 - Auto-import entire struct
    {attribute 'HMI_STRUCT'}
    Temperature_Sensor_1 : ST_AnalogInput;
    
    // Temperature sensor 2
    {attribute 'HMI_STRUCT'}
    Temperature_Sensor_2 : ST_AnalogInput;
    
    // Pressure sensor
    {attribute 'HMI_STRUCT'}
    Pressure_Sensor_1 : ST_AnalogInput;
    
    // Flow sensor
    {attribute 'HMI_STRUCT'}
    Flow_Sensor_1 : ST_AnalogInput;
    
    // ========================================
    // MOTORS
    // ========================================
    
    // Main pump motor
    {attribute 'HMI_STRUCT'}
    Pump_Motor_1 : ST_Motor;
    
    // Backup pump motor
    {attribute 'HMI_STRUCT'}
    Pump_Motor_2 : ST_Motor;
    
    // Fan motor
    {attribute 'HMI_STRUCT'}
    Fan_Motor : ST_Motor;
    
    // ========================================
    // TEMPERATURE CONTROLLER
    // ========================================
    
    // Temperature controller (with nested PID params)
    {attribute 'HMI_STRUCT'}
    Temp_Controller_1 : ST_TempController;
    
    // ========================================
    // TANKS
    // ========================================
    
    // Storage tanks
    {attribute 'HMI_STRUCT'}
    Tank_1 : ST_Tank;
    
    {attribute 'HMI_STRUCT'}
    Tank_2 : ST_Tank;
    
    {attribute 'HMI_STRUCT'}
    Tank_3 : ST_Tank;
    
    // ========================================
    // ARRAY OF STRUCTS EXAMPLE
    // ========================================
    
    // Array of analog inputs
    {attribute 'HMI_STRUCT_ARRAY'}
    AnalogInputs : ARRAY[1..8] OF ST_AnalogInput;
    
    // ========================================
    // NON-HMI VARIABLES (not imported)
    // ========================================
    
    // These variables don't have HMI_STRUCT, so won't be auto-imported
    InternalCounter : UDINT;
    SystemState : INT;
    DebugFlags : WORD;
    
END_VAR

(*
    EXPECTED HMI IMPORT RESULT:
    
    When you click "Scan PLC" in the HMI application, it will find:
    
    GROUP: Temperature_Sensor_1 (ST_AnalogInput)
      ├─ Value              (Process Value, °C)
      ├─ Scaled             (Process Value, %)
      ├─ Error              (Alarm: Sensor Kommunikationsfejl)
      └─ CalibrationOffset  (Setpoint, Offset)
    
    GROUP: Temperature_Sensor_2 (ST_AnalogInput)
      ├─ Value              (Process Value, °C)
      ├─ Scaled             (Process Value, %)
      ├─ Error              (Alarm: Sensor Kommunikationsfejl)
      └─ CalibrationOffset  (Setpoint, Offset)
    
    GROUP: Pressure_Sensor_1 (ST_AnalogInput)
      ├─ Value              (Process Value, °C)
      ├─ Scaled             (Process Value, %)
      ├─ Error              (Alarm: Sensor Kommunikationsfejl)
      └─ CalibrationOffset  (Setpoint, Offset)
    
    GROUP: Pump_Motor_1 (ST_Motor)
      ├─ SpeedSetpoint      (Setpoint, RPM)
      ├─ ActualSpeed        (Process Value, RPM)
      ├─ Current            (Process Value, A)
      ├─ Command            (Switch: Stop/Start/Reset)
      ├─ Fault              (Alarm: Motor Fejl)
      └─ Overload           (Alarm: Motor Overbelastet)
    
    GROUP: Temp_Controller_1 (ST_TempController)
      ├─ Setpoint           (Setpoint, °C)
      ├─ ProcessValue       (Process Value, °C)
      ├─ Output             (Process Value, %)
      ├─ PID.Kp             (Setpoint)
      ├─ PID.Ki             (Setpoint)
      ├─ PID.Kd             (Setpoint)
      └─ Mode               (Switch: Off/Manual/Automatic)
    
    GROUP: Tank_1 (ST_Tank)
      ├─ Level              (Process Value, %)
      ├─ Volume             (Process Value, L)
      ├─ OverflowAlarm      (Alarm: Tank Overfyldt)
      └─ LowLevelWarning    (Alarm: Tank Næsten Tom)
    
    And similar groups for all other structs marked with {attribute 'HMI_STRUCT'}
    
    IMPORTANT NOTES:
    
    1. Only members with HMI attributes are imported:
       - HMI_SP, HMI_PV, HMI_SWITCH, HMI_ALARM
       - Members like RawValue, InternalState are skipped
    
    2. Full path is used for access:
       - Temperature_Sensor_1.Value
       - Pump_Motor_1.SpeedSetpoint
       - Temp_Controller_1.PID.Kp (nested)
    
    3. Config is automatically generated in config.json
    
    4. GUI widgets are automatically created and grouped
    
    5. All alarm limits, units, ranges are preserved from PLC
*)

(*
    USAGE INSTRUCTIONS:
    
    1. Copy these struct definitions to your TwinCAT project
    
    2. Copy the VAR_GLOBAL declarations
    
    3. Compile the TwinCAT project (F7)
       - This generates/updates the PLC.tmc file
    
    4. Set tmc_file path in HMI config.json:
       "tmc_file": "C:\\Path\\To\\Your\\Project\\PLC.tmc"
    
    5. Start the HMI application:
       py main.py
    
    6. Click "Forbind" to connect to PLC
    
    7. Click "Scan PLC" button
       - Application scans for symbols with HMI_STRUCT
       - Expands structs to members
       - Generates configuration
       - Creates GUI widgets
    
    8. Done! All struct members are now available in the HMI
    
    ADVANTAGES:
    
    ✅ Define struct once, use many times
    ✅ Consistent structure across multiple instances
    ✅ Easy to add new sensors/motors
    ✅ No manual HMI configuration needed
    ✅ Type-safe (PLC compiler checks)
    ✅ Automatic GUI grouping
    ✅ All metadata from PLC attributes
    
    BEST PRACTICES:
    
    1. Use descriptive struct names (ST_AnalogInput, ST_Motor)
    2. Add HMI attributes to relevant members only
    3. Use consistent naming (Setpoint, ProcessValue, Error)
    4. Group related functionality in structs
    5. Document struct purpose in comments
    6. Test with one struct before creating many
*)
