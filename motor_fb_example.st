(*
================================================================================
    MOTOR FUNCTION BLOCK WITH HMI INTEGRATION
    
    Description: Complete motor control function block with:
    - Start/Stop control with safety interlocks
    - Speed control with ramping
    - Start frequency monitoring and protection
    - Feedback monitoring with alarms
    - Full HMI integration using structured attributes
    
    Author: TwinCAT HMI Example
    Date: 2025-01-28
================================================================================
*)

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

TYPE ST_MotorCommands :
STRUCT
    {attribute 'HMI_CMD'}
    {attribute 'CmdText' := 'Start Motor'}
    Start : BOOL := FALSE;          // Start command from HMI
    
    {attribute 'HMI_CMD'}
    {attribute 'CmdText' := 'Stop Motor'}
    Stop : BOOL := FALSE;           // Stop command from HMI
    
    {attribute 'HMI_CMD'}
    {attribute 'CmdText' := 'Reset Alarms'}
    Reset : BOOL := FALSE;          // Reset all alarms and errors
    
    {attribute 'HMI_SP'}
    {attribute 'Unit' := '%'}
    {attribute 'Min' := '0'}
    {attribute 'Max' := '100'}
    {attribute 'Decimals' := '1'}
    {attribute 'Step' := '1'}
    SpeedSetpoint : REAL := 0.0;    // Speed setpoint 0-100%
END_STRUCT
END_TYPE

TYPE ST_MotorSettings :
STRUCT
    {attribute 'HMI_SP'}
    {attribute 'Unit' := 'Starts/min'}
    {attribute 'Min' := '1'}
    {attribute 'Max' := '10'}
    {attribute 'Decimals' := '0'}
    {attribute 'Step' := '1'}
    MaxStartsPerMinute : INT := 6;          // Max allowed starts per minute
    
    {attribute 'HMI_SP'}
    {attribute 'Unit' := 's'}
    {attribute 'Min' := '10'}
    {attribute 'Max' := '600'}
    {attribute 'Decimals' := '0'}
    {attribute 'Step' := '10'}
    MaxTimeAtMaxStarts : TIME := T#60S;     // Max time in alarm before shutdown
    
    {attribute 'HMI_SP'}
    {attribute 'Unit' := '%'}
    {attribute 'Min' := '0'}
    {attribute 'Max' := '100'}
    {attribute 'Decimals' := '1'}
    {attribute 'Step' := '5'}
    MaxStartSpeed : REAL := 50.0;           // Max speed during start sequence
    
    {attribute 'HMI_SP'}
    {attribute 'Unit' := 'ms'}
    {attribute 'Min' := '10'}
    {attribute 'Max' := '1000'}
    {attribute 'Decimals' := '0'}
    {attribute 'Step' := '10'}
    RampTimePerPercent : TIME := T#50MS;    // Time per 1% speed change
    
    {attribute 'HMI_SP'}
    {attribute 'Unit' := 's'}
    {attribute 'Min' := '1'}
    {attribute 'Max' := '30'}
    {attribute 'Decimals' := '1'}
    {attribute 'Step' := '0.5'}
    FeedbackTimeout : TIME := T#5S;         // Time to reach target speed
    
    {attribute 'HMI_SP'}
    {attribute 'Unit' := '%'}
    {attribute 'Min' := '1'}
    {attribute 'Max' := '20'}
    {attribute 'Decimals' := '1'}
    {attribute 'Step' := '0.5'}
    FeedbackTolerance : REAL := 5.0;        // Acceptable speed deviation
END_STRUCT
END_TYPE

TYPE ST_MotorFeedback :
STRUCT
    {attribute 'HMI_PV'}
    Running : BOOL := FALSE;                // Motor is running
    
    {attribute 'HMI_PV'}
    {attribute 'Unit' := '%'}
    {attribute 'Decimals' := '1'}
    ActualSpeed : REAL := 0.0;              // Actual motor speed 0-100%
    
    {attribute 'HMI_PV'}
    ThermalRelay : BOOL := FALSE;           // Thermal relay status (TRUE = OK)
    
    {attribute 'HMI_PV'}
    Thermistor : BOOL := FALSE;             // Thermistor status (TRUE = OK)
    
    {attribute 'HMI_PV'}
    VFD_Ready : BOOL := FALSE;              // VFD ready status
    
    {attribute 'HMI_PV'}
    VFD_Fault : BOOL := FALSE;              // VFD fault status
    
    {attribute 'HMI_PV'}
    {attribute 'Unit' := 'Starts'}
    {attribute 'Decimals' := '0'}
    StartCountLastMinute : INT := 0;        // Start count in last minute
END_STRUCT
END_TYPE

TYPE ST_MotorAlarms :
STRUCT
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'For mange opstart per minut'}
    {attribute 'AlarmPriority' := '2'}
    {attribute 'AlarmActive' := TRUE}
    {attribute 'WarningActive' := FALSE}
    TooManyStarts : BOOL := FALSE;          // Too many starts alarm
    
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Motor stoppet - for mange opstart'}
    {attribute 'AlarmPriority' := '1'}
    {attribute 'AlarmActive' := TRUE}
    {attribute 'WarningActive' := FALSE}
    StartProtectionShutdown : BOOL := FALSE; // Protection shutdown
    
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Hastighedsfeedback fejl'}
    {attribute 'AlarmPriority' := '2'}
    {attribute 'AlarmActive' := TRUE}
    {attribute 'WarningActive' := FALSE}
    SpeedFeedbackFault : BOOL := FALSE;     // Speed not reached in time
    
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Termorelæ udløst'}
    {attribute 'AlarmPriority' := '1'}
    {attribute 'AlarmActive' := TRUE}
    {attribute 'WarningActive' := FALSE}
    ThermalRelayTripped : BOOL := FALSE;    // Thermal protection
    
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'Termistor fejl'}
    {attribute 'AlarmPriority' := '1'}
    {attribute 'AlarmActive' := TRUE}
    {attribute 'WarningActive' := FALSE}
    ThermistorFault : BOOL := FALSE;        // Motor overtemperature
    
    {attribute 'HMI_ALARM'}
    {attribute 'AlarmText' := 'VFD fejl'}
    {attribute 'AlarmPriority' := '1'}
    {attribute 'AlarmActive' := TRUE}
    {attribute 'WarningActive' := FALSE}
    VFD_Fault : BOOL := FALSE;              // Variable frequency drive fault
END_STRUCT
END_TYPE

// ============================================================================
// FUNCTION BLOCK
// ============================================================================

FUNCTION_BLOCK FB_Motor
VAR_INPUT
    // Physical inputs from motor and VFD
    I_ThermalRelay      : BOOL;     // Thermal relay contact (TRUE = OK)
    I_Thermistor        : BOOL;     // Thermistor input (TRUE = OK)
    I_VFD_Ready         : BOOL;     // VFD ready signal
    I_VFD_Fault         : BOOL;     // VFD fault signal
    I_SpeedFeedback     : REAL;     // Speed feedback from VFD (0-100%)
    I_Enable            : BOOL;     // External enable signal
END_VAR

VAR_OUTPUT
    // Physical outputs to motor and VFD
    Q_Start             : BOOL;     // Start output to VFD
    Q_SpeedReference    : REAL;     // Speed reference to VFD (0-100%)
    Q_Fault             : BOOL;     // General fault output
END_VAR

VAR_IN_OUT
    // HMI interface structures
    Commands    : ST_MotorCommands;
    Settings    : ST_MotorSettings;
    Feedback    : ST_MotorFeedback;
    Alarms      : ST_MotorAlarms;
END_VAR

VAR
    // Internal state machine
    State               : INT := 0;
    
    // Ramping control
    CurrentSpeed        : REAL := 0.0;
    TargetSpeed         : REAL := 0.0;
    RampTimer           : TON;
    
    // Start frequency monitoring
    StartTimeStamps     : ARRAY[1..20] OF TIME;
    StartIndex          : INT := 1;
    TooManyStartsTimer  : TON;
    
    // Feedback monitoring
    FeedbackTimer       : TON;
    SpeedReached        : BOOL := FALSE;
    
    // Edge detection
    StartCmd_R_TRIG     : R_TRIG;
    StopCmd_R_TRIG      : R_TRIG;
    ResetCmd_R_TRIG     : R_TRIG;
    
    // Timers
    CurrentTime         : TIME;
END_VAR

VAR CONSTANT
    STATE_STOPPED       : INT := 0;
    STATE_STARTING      : INT := 1;
    STATE_RUNNING       : INT := 2;
    STATE_STOPPING      : INT := 3;
    STATE_FAULT         : INT := 4;
END_VAR

(*
================================================================================
    Main Program Logic
================================================================================
*)

// Get current system time
CurrentTime := TIME();

// Edge detection for commands
StartCmd_R_TRIG(CLK := Commands.Start);
StopCmd_R_TRIG(CLK := Commands.Stop);
ResetCmd_R_TRIG(CLK := Commands.Reset);

// Reset command handling
IF ResetCmd_R_TRIG.Q THEN
    // Reset all alarms
    Alarms.TooManyStarts := FALSE;
    Alarms.StartProtectionShutdown := FALSE;
    Alarms.SpeedFeedbackFault := FALSE;
    Alarms.ThermalRelayTripped := FALSE;
    Alarms.ThermistorFault := FALSE;
    Alarms.VFD_Fault := FALSE;
    
    // Reset to stopped state if not in critical fault
    IF State = STATE_FAULT THEN
        State := STATE_STOPPED;
    END_IF;
    
    // Reset command (self-clearing)
    Commands.Reset := FALSE;
END_IF;

// Update feedback from physical inputs
Feedback.ThermalRelay := I_ThermalRelay;
Feedback.Thermistor := I_Thermistor;
Feedback.VFD_Ready := I_VFD_Ready;
Feedback.VFD_Fault := I_VFD_Fault;
Feedback.ActualSpeed := I_SpeedFeedback;

// Check for hardware faults
IF NOT I_ThermalRelay THEN
    Alarms.ThermalRelayTripped := TRUE;
    State := STATE_FAULT;
END_IF;

IF NOT I_Thermistor THEN
    Alarms.ThermistorFault := TRUE;
    State := STATE_FAULT;
END_IF;

IF I_VFD_Fault THEN
    Alarms.VFD_Fault := TRUE;
    State := STATE_FAULT;
END_IF;

// Start frequency protection monitoring
MonitorStartFrequency();

// State machine
CASE State OF
    
    STATE_STOPPED:
        // Stopped state
        CurrentSpeed := 0.0;
        TargetSpeed := 0.0;
        Q_Start := FALSE;
        Q_SpeedReference := 0.0;
        Feedback.Running := FALSE;
        SpeedReached := FALSE;
        
        // Check if start is allowed
        IF StartCmd_R_TRIG.Q AND I_Enable AND I_VFD_Ready AND NOT Alarms.StartProtectionShutdown THEN
            // Log start time
            LogStartTime();
            
            // Limit target speed during start sequence
            IF Commands.SpeedSetpoint > Settings.MaxStartSpeed THEN
                TargetSpeed := Settings.MaxStartSpeed;
            ELSE
                TargetSpeed := Commands.SpeedSetpoint;
            END_IF;
            
            State := STATE_STARTING;
        END_IF;
        
        // Clear start command
        Commands.Start := FALSE;
    
    STATE_STARTING:
        // Starting state
        Q_Start := TRUE;
        
        // Ramp up speed
        IF CurrentSpeed < TargetSpeed THEN
            RampSpeed(TRUE);
        ELSIF CurrentSpeed > TargetSpeed THEN
            RampSpeed(FALSE);
        ELSE
            // Speed reached
            State := STATE_RUNNING;
            SpeedReached := FALSE;
        END_IF;
        
        // Monitor speed feedback
        MonitorSpeedFeedback();
        
        // Check for stop command
        IF StopCmd_R_TRIG.Q OR NOT I_Enable THEN
            State := STATE_STOPPING;
        END_IF;
        
        // Clear stop command
        Commands.Stop := FALSE;
    
    STATE_RUNNING:
        // Running state
        Q_Start := TRUE;
        Feedback.Running := TRUE;
        
        // Update target speed from setpoint
        TargetSpeed := Commands.SpeedSetpoint;
        
        // Ramp to target speed
        IF CurrentSpeed < TargetSpeed THEN
            RampSpeed(TRUE);
        ELSIF CurrentSpeed > TargetSpeed THEN
            RampSpeed(FALSE);
        END_IF;
        
        // Monitor speed feedback
        MonitorSpeedFeedback();
        
        // Check for stop command
        IF StopCmd_R_TRIG.Q OR NOT I_Enable THEN
            State := STATE_STOPPING;
        END_IF;
        
        // Clear stop command
        Commands.Stop := FALSE;
    
    STATE_STOPPING:
        // Stopping state
        Q_Start := FALSE;
        TargetSpeed := 0.0;
        
        // Ramp down speed
        IF CurrentSpeed > 0.0 THEN
            RampSpeed(FALSE);
        ELSE
            // Fully stopped
            State := STATE_STOPPED;
        END_IF;
    
    STATE_FAULT:
        // Fault state - emergency stop
        Q_Start := FALSE;
        CurrentSpeed := 0.0;
        TargetSpeed := 0.0;
        Q_SpeedReference := 0.0;
        Feedback.Running := FALSE;
        Q_Fault := TRUE;
        
        // Can only exit fault state with reset command
        // Reset is handled above
END_CASE;

// Always output current speed reference
Q_SpeedReference := CurrentSpeed;

// Clear fault output if no active critical alarms
IF NOT (Alarms.ThermalRelayTripped OR Alarms.ThermistorFault OR Alarms.VFD_Fault OR Alarms.StartProtectionShutdown) THEN
    Q_Fault := FALSE;
END_IF;


// ============================================================================
// INTERNAL METHODS
// ============================================================================

(*
    RampSpeed - Ramps speed up or down based on ramp time setting
*)
METHOD PRIVATE RampSpeed
VAR_INPUT
    RampUp : BOOL;      // TRUE = ramp up, FALSE = ramp down
END_VAR

    // Start/restart ramp timer
    RampTimer(IN := TRUE, PT := Settings.RampTimePerPercent);
    
    IF RampTimer.Q THEN
        // Time to increment/decrement speed
        IF RampUp THEN
            CurrentSpeed := CurrentSpeed + 1.0;
            IF CurrentSpeed > TargetSpeed THEN
                CurrentSpeed := TargetSpeed;
            END_IF;
            IF CurrentSpeed > 100.0 THEN
                CurrentSpeed := 100.0;
            END_IF;
        ELSE
            CurrentSpeed := CurrentSpeed - 1.0;
            IF CurrentSpeed < TargetSpeed THEN
                CurrentSpeed := TargetSpeed;
            END_IF;
            IF CurrentSpeed < 0.0 THEN
                CurrentSpeed := 0.0;
            END_IF;
        END_IF;
        
        // Reset timer for next step
        RampTimer(IN := FALSE);
    END_IF;
END_METHOD

(*
    MonitorSpeedFeedback - Monitors if actual speed reaches target
*)
METHOD PRIVATE MonitorSpeedFeedback

VAR
    SpeedError : REAL;
END_VAR

    SpeedError := ABS(TargetSpeed - I_SpeedFeedback);
    
    // Check if speed is within tolerance
    IF SpeedError <= Settings.FeedbackTolerance THEN
        SpeedReached := TRUE;
        FeedbackTimer(IN := FALSE);
        Alarms.SpeedFeedbackFault := FALSE;
    ELSE
        SpeedReached := FALSE;
        
        // Start timeout timer if not already reached
        FeedbackTimer(IN := TRUE, PT := Settings.FeedbackTimeout);
        
        // Check for timeout
        IF FeedbackTimer.Q THEN
            Alarms.SpeedFeedbackFault := TRUE;
        END_IF;
    END_IF;
END_METHOD

(*
    LogStartTime - Records timestamp of motor start
*)
METHOD PRIVATE LogStartTime

    // Store current time in circular buffer
    StartTimeStamps[StartIndex] := CurrentTime;
    StartIndex := StartIndex + 1;
    
    // Wrap around buffer
    IF StartIndex > 20 THEN
        StartIndex := 1;
    END_IF;
END_METHOD

(*
    MonitorStartFrequency - Monitors number of starts per minute
*)
METHOD PRIVATE MonitorStartFrequency

VAR
    i : INT;
    StartCount : INT := 0;
    TimeWindow : TIME := T#60S;
END_VAR

    // Count starts within last minute
    FOR i := 1 TO 20 DO
        IF (CurrentTime - StartTimeStamps[i]) <= TimeWindow AND StartTimeStamps[i] > T#0S THEN
            StartCount := StartCount + 1;
        END_IF;
    END_FOR;
    
    // Update feedback
    Feedback.StartCountLastMinute := StartCount;
    
    // Check if too many starts
    IF StartCount >= Settings.MaxStartsPerMinute THEN
        Alarms.TooManyStarts := TRUE;
        
        // Start protection timer
        TooManyStartsTimer(IN := TRUE, PT := Settings.MaxTimeAtMaxStarts);
        
        // Check if timer expired - trigger shutdown
        IF TooManyStartsTimer.Q THEN
            Alarms.StartProtectionShutdown := TRUE;
            State := STATE_FAULT;
            TooManyStartsTimer(IN := FALSE);
        END_IF;
    ELSE
        Alarms.TooManyStarts := FALSE;
        TooManyStartsTimer(IN := FALSE);
    END_IF;
END_METHOD

END_FUNCTION_BLOCK


// ============================================================================
// USAGE EXAMPLE - Global Variable Declaration
// ============================================================================

(*
{attribute 'qualified_only'}
VAR_GLOBAL
    // Motor instance with all structures
    Motor1 : FB_Motor;
    
    // Motor command interface
    {attribute 'HMI_GROUP'}
    Motor1_Commands : ST_MotorCommands;
    
    // Motor settings
    {attribute 'HMI_GROUP'}
    Motor1_Settings : ST_MotorSettings;
    
    // Motor feedback
    {attribute 'HMI_GROUP'}
    Motor1_Feedback : ST_MotorFeedback;
    
    // Motor alarms
    {attribute 'HMI_GROUP'}
    Motor1_Alarms : ST_MotorAlarms;
END_VAR


// ============================================================================
// USAGE EXAMPLE - Main Program
// ============================================================================

PROGRAM MAIN
VAR
    // Physical I/O mappings (example)
    DI_Motor1_ThermalRelay  AT %I* : BOOL;
    DI_Motor1_Thermistor    AT %I* : BOOL;
    DI_Motor1_VFD_Ready     AT %I* : BOOL;
    DI_Motor1_VFD_Fault     AT %I* : BOOL;
    AI_Motor1_SpeedFB       AT %I* : REAL;
    
    DO_Motor1_Start         AT %Q* : BOOL;
    AO_Motor1_SpeedRef      AT %Q* : REAL;
    DO_Motor1_Fault         AT %Q* : BOOL;
    
    EnableMotor1            : BOOL := TRUE;
END_VAR

// Call motor function block
Motor1(
    I_ThermalRelay      := DI_Motor1_ThermalRelay,
    I_Thermistor        := DI_Motor1_Thermistor,
    I_VFD_Ready         := DI_Motor1_VFD_Ready,
    I_VFD_Fault         := DI_Motor1_VFD_Fault,
    I_SpeedFeedback     := AI_Motor1_SpeedFB,
    I_Enable            := EnableMotor1,
    Q_Start             => DO_Motor1_Start,
    Q_SpeedReference    => AO_Motor1_SpeedRef,
    Q_Fault             => DO_Motor1_Fault,
    Commands            := Motor1_Commands,
    Settings            := Motor1_Settings,
    Feedback            := Motor1_Feedback,
    Alarms              := Motor1_Alarms
);

END_PROGRAM
*)
