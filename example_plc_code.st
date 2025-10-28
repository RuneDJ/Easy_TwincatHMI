(*
    TwinCAT 3 PLC Example Code
    Example global variables with HMI attributes for alarm system
*)

{attribute 'qualified_only'}
VAR_GLOBAL
    
    // ========================================
    // SETPOINTS (HMI_SP)
    // ========================================
    
    // Temperature setpoint with alarms
    {attribute 'HMI_SP'}
    {attribute 'Unit' := '°C'}
    {attribute 'Min' := '0'}
    {attribute 'Max' := '100'}
    {attribute 'Decimals' := '1'}
    {attribute 'Step' := '0.5'}
    {attribute 'AlarmHighHigh' := '95'}      // Critical high alarm at 95°C
    {attribute 'AlarmHigh' := '85'}           // High alarm at 85°C
    {attribute 'AlarmLow' := '10'}            // Low alarm at 10°C
    {attribute 'AlarmLowLow' := '5'}          // Critical low alarm at 5°C
    {attribute 'AlarmPriority' := '1'}        // Priority 1 = Critical
    TemperaturSetpunkt : REAL := 25.0;
    
    // Pressure setpoint
    {attribute 'HMI_SP'}
    {attribute 'Unit' := 'bar'}
    {attribute 'Min' := '0'}
    {attribute 'Max' := '10'}
    {attribute 'Decimals' := '2'}
    {attribute 'AlarmHigh' := '9.5'}
    TrykSetpunkt : REAL := 5.0;
    
    // Flow setpoint
    {attribute 'HMI_SP'}
    {attribute 'Unit' := 'L/min'}
    {attribute 'Min' := '0'}
    {attribute 'Max' := '200'}
    {attribute 'Decimals' := '1'}
    FlowSetpunkt : REAL := 100.0;
    
    // ========================================
    // PROCESS VALUES (HMI_PV)
    // ========================================
    
    // Temperature process value with alarms
    {attribute 'HMI_PV'}
    {attribute 'Unit' := '°C'}
    {attribute 'Decimals' := '2'}
    {attribute 'AlarmHighHigh' := '98'}       // Critical high at 98°C
    {attribute 'AlarmHigh' := '90'}           // Warning high at 90°C
    {attribute 'AlarmLow' := '5'}             // Warning low at 5°C
    {attribute 'AlarmLowLow' := '2'}          // Critical low at 2°C
    {attribute 'AlarmPriority' := '1'}        // Critical priority
    Temperatur_1 : REAL := 23.5;
    
    // Second temperature sensor
    {attribute 'HMI_PV'}
    {attribute 'Unit' := '°C'}
    {attribute 'Decimals' := '2'}
    {attribute 'AlarmHighHigh' := '95'}
    {attribute 'AlarmHigh' := '85'}
    Temperatur_2 : REAL := 24.0;
    
    // Pressure with high alarm only
    {attribute 'HMI_PV'}
    {attribute 'Unit' := 'bar'}
    {attribute 'Decimals' := '2'}
    {attribute 'AlarmHigh' := '9.5'}
    {attribute 'AlarmPriority' := '2'}        // High priority
    Tryk_1 : REAL := 5.0;
    
    // Flow measurement
    {attribute 'HMI_PV'}
    {attribute 'Unit' := 'L/min'}
    {attribute 'Decimals' := '1'}
    {attribute 'AlarmHigh' := '180'}
    {attribute 'AlarmLow' := '20'}
    Flow_1 : REAL := 100.0;
    
    // Level measurement (no alarms)
    {attribute 'HMI_PV'}
    {attribute 'Unit' := '%'}
    {attribute 'Decimals' := '1'}
    Niveau_1 : REAL := 50.0;
    
    // ========================================
    // SWITCHES (HMI_SWITCH)
    // ========================================
    
    // Operating mode selector
    {attribute 'HMI_SWITCH'}
    {attribute 'Pos0' := 'Stop'}
    {attribute 'Pos1' := 'Auto'}
    {attribute 'Pos2' := 'Manuel'}
    DriftMode : INT := 1;
    
    // Pump selector
    {attribute 'HMI_SWITCH'}
    {attribute 'Pos0' := 'Off'}
    {attribute 'Pos1' := 'Pumpe 1'}
    {attribute 'Pos2' := 'Pumpe 2'}
    {attribute 'Pos3' := 'Begge'}
    PumpeValg : INT := 0;
    
    // Priority selector
    {attribute 'HMI_SWITCH'}
    {attribute 'Pos0' := 'Normal'}
    {attribute 'Pos1' := 'Høj'}
    {attribute 'Pos2' := 'Kritisk'}
    Prioritet : INT := 0;
    
    // ========================================
    // DIGITAL ALARMS (HMI_ALARM)
    // ========================================
    
    // Motor fault alarm
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Motor 1 Fejl'}
    {attribute 'AlarmPriority' := '1'}        // Critical
    Motor1Fejl : BOOL := FALSE;
    
    // Emergency stop
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Nødstop Aktiveret'}
    {attribute 'AlarmPriority' := '1'}        // Critical
    NodStop : BOOL := FALSE;
    
    // Low oil pressure
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Lavt Olietryk'}
    {attribute 'AlarmPriority' := '2'}        // High
    LavtOlieTryk : BOOL := FALSE;
    
    // Filter warning
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Filter Skal Skiftes'}
    {attribute 'AlarmPriority' := '3'}        // Medium
    FilterAdvarsel : BOOL := FALSE;
    
    // Maintenance reminder
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Vedligehold Nødvendigt'}
    {attribute 'AlarmPriority' := '4'}        // Low
    VedligeholdPaamindelse : BOOL := FALSE;
    
    // ========================================
    // STATUS FLAGS (No HMI attributes)
    // ========================================
    
    SystemRunning : BOOL := FALSE;
    ErrorCount : INT := 0;
    LastUpdateTime : TIME := T#0S;
    
END_VAR

(*
    USAGE NOTES:
    
    1. Copy this variable declaration to your TwinCAT project
    2. Compile the project
    3. Run the Python HMI application
    4. The HMI will automatically discover all variables with HMI_ attributes
    
    ATTRIBUTE REFERENCE:
    
    HMI_SP          - Setpoint (writable from HMI)
    HMI_PV          - Process Value (read-only)
    HMI_SWITCH      - Switch/Selector (writable)
    HMI_ALARM       - Digital alarm (BOOL)
    
    Unit            - Display unit
    Min/Max         - Valid range for setpoints
    Decimals        - Number of decimal places
    Step            - Increment step for spinbox
    
    AlarmHighHigh   - Critical high alarm limit
    AlarmHigh       - Warning high alarm limit
    AlarmLow        - Warning low alarm limit
    AlarmLowLow     - Critical low alarm limit
    AlarmPriority   - 1=Critical, 2=High, 3=Medium, 4=Low
    AlarmText       - Text for digital alarms
    
    Pos0, Pos1, etc - Switch position labels
    
    ALARM BEHAVIOR:
    
    - Alarms trigger when value crosses limit
    - Alarms clear with 2% hysteresis (configurable)
    - HighHigh and LowLow are critical (Priority 1)
    - High and Low are warnings (Priority 2)
    - Digital alarms trigger when BOOL = TRUE
    
    EXAMPLE TEST SEQUENCE:
    
    1. Set Temperatur_1 := 92.0  -> High alarm
    2. Set Temperatur_1 := 99.0  -> HighHigh (critical) alarm
    3. Set Motor1Fejl := TRUE    -> Critical digital alarm
    4. Acknowledge alarms in HMI
    5. Reset values to clear alarms
*)
