
from types import SimpleNamespace
from ctypes import (
    c_bool, c_char, c_int, c_long, c_float, c_double,
    c_char_p, c_void_p,
    Structure, POINTER, HRESULT, WINFUNCTYPE,
)
from ctypes.wintypes import BYTE, WORD, DWORD, HANDLE, LPCSTR, HWND


ENUM_T = DWORD
FLT_MAX = 3.402823466e+38
MAX_PATH = 260
c_float_p = POINTER(c_float)


class GUID(Structure):
    _fields_ = [
        ("Data1", DWORD),
        ("Data2", WORD),
        ("Data3", WORD),
        ("Data4", BYTE * 8)
    ]


# 0 "SimConnect.h"
# 0 "<built-in>"
# 0 "<command-line>"
# 1 "SimConnect.h"
# -----------------------------------------------------------------------------
# 
#  Copyright (c) Microsoft Corporation. All Rights Reserved.
# 
# -----------------------------------------------------------------------------




       
# 22 "SimConnect.h"
# 1 "./float.h" 1
# 23 "SimConnect.h" 2

OBJECT_ID = DWORD 

# ----------------------------------------------------------------------------
#         Constants
# ----------------------------------------------------------------------------

UNUSED: DWORD = DWORD(0xFFFFFFFF)  #  special value to indicate unused event, ID
OBJECT_ID_USER: DWORD = DWORD(0)  #  proxy value for User vehicle ObjectID

CAMERA_IGNORE_FIELD: float = FLT_MAX  # Used to tell the Camera API to NOT modify the value in this part of the argument.

CLIENTDATA_MAX_SIZE: DWORD = DWORD(8192)  #  maximum value for SimConnect_CreateClientData dwSize parameter


#  Notification Group priority values
GROUP_PRIORITY_HIGHEST: DWORD = DWORD(1)  #  highest priority
GROUP_PRIORITY_HIGHEST_MASKABLE: DWORD = DWORD(10000000)  #  highest priority that allows events to be masked
GROUP_PRIORITY_STANDARD: DWORD = DWORD(1900000000)  #  standard priority
GROUP_PRIORITY_DEFAULT: DWORD = DWORD(2000000000)  #  default priority
GROUP_PRIORITY_LOWEST: DWORD = DWORD(4000000000)  #  priorities lower than this will be ignored

# Weather observations Metar strings
MAX_METAR_LENGTH: DWORD = DWORD(2000) 

#  Maximum thermal size is 100 km.
MAX_THERMAL_SIZE: float = 100000 
MAX_THERMAL_RATE: float = 1000 

#  SIMCONNECT_DATA_INITPOSITION.Airspeed
INITPOSITION_AIRSPEED_CRUISE: DWORD = DWORD(-1)  #  aircraft's cruise airspeed
INITPOSITION_AIRSPEED_KEEP: DWORD = DWORD(-2)  #  keep current airspeed

#  AddToClientDataDefinition dwSizeOrType parameter type values
CLIENTDATATYPE_INT8: DWORD = DWORD(-1)  #   8-bit integer number
CLIENTDATATYPE_INT16: DWORD = DWORD(-2)  #  16-bit integer number
CLIENTDATATYPE_INT32: DWORD = DWORD(-3)  #  32-bit integer number
CLIENTDATATYPE_INT64: DWORD = DWORD(-4)  #  64-bit integer number
CLIENTDATATYPE_FLOAT32: DWORD = DWORD(-5)  #  32-bit floating-point number (float)
CLIENTDATATYPE_FLOAT64: DWORD = DWORD(-6)  #  64-bit floating-point number (double)

#  AddToClientDataDefinition dwOffset parameter special values
CLIENTDATAOFFSET_AUTO: DWORD = DWORD(-1)  #  automatically compute offset of the ClientData variable

#  Open ConfigIndex parameter special value
OPEN_CONFIGINDEX_LOCAL: DWORD = DWORD(-1)  #  ignore SimConnect.cfg settings, and force local connection

# ----------------------------------------------------------------------------
#         Enum definitions
# ----------------------------------------------------------------------------

# these came from substituteMacros
# 88 "SimConnect.h"
#  Receive data types
RECV_ID = ENUM_T
RECV_ID_NULL = ENUM_T(1) 
RECV_ID_EXCEPTION = ENUM_T(2) 
RECV_ID_OPEN = ENUM_T(3) 
RECV_ID_QUIT = ENUM_T(4) 
RECV_ID_EVENT = ENUM_T(5) 
RECV_ID_EVENT_OBJECT_ADDREMOVE = ENUM_T(6) 
RECV_ID_EVENT_FILENAME = ENUM_T(7) 
RECV_ID_EVENT_FRAME = ENUM_T(8) 
RECV_ID_SIMOBJECT_DATA = ENUM_T(9) 
RECV_ID_SIMOBJECT_DATA_BYTYPE = ENUM_T(10) 
RECV_ID_WEATHER_OBSERVATION = ENUM_T(11) 
RECV_ID_CLOUD_STATE = ENUM_T(12) 
RECV_ID_ASSIGNED_OBJECT_ID = ENUM_T(13) 
RECV_ID_RESERVED_KEY = ENUM_T(14) 
RECV_ID_CUSTOM_ACTION = ENUM_T(15) 
RECV_ID_SYSTEM_STATE = ENUM_T(16) 
RECV_ID_CLIENT_DATA = ENUM_T(17) 
RECV_ID_EVENT_WEATHER_MODE = ENUM_T(18) 
RECV_ID_AIRPORT_LIST = ENUM_T(19) 
RECV_ID_VOR_LIST = ENUM_T(20) 
RECV_ID_NDB_LIST = ENUM_T(21) 
RECV_ID_WAYPOINT_LIST = ENUM_T(22) 
RECV_ID_EVENT_MULTIPLAYER_SERVER_STARTED = ENUM_T(23) 
RECV_ID_EVENT_MULTIPLAYER_CLIENT_STARTED = ENUM_T(24) 
RECV_ID_EVENT_MULTIPLAYER_SESSION_ENDED = ENUM_T(25) 
RECV_ID_EVENT_RACE_END = ENUM_T(26) 
RECV_ID_EVENT_RACE_LAP = ENUM_T(27) 







#  Data data types
DATATYPE = ENUM_T
DATATYPE_INVALID = ENUM_T(1)  #  invalid data type
DATATYPE_INT32 = ENUM_T(2)  #  32-bit integer number
DATATYPE_INT64 = ENUM_T(3)  #  64-bit integer number
DATATYPE_FLOAT32 = ENUM_T(4)  #  32-bit floating-point number (float)
DATATYPE_FLOAT64 = ENUM_T(5)  #  64-bit floating-point number (double)
DATATYPE_STRING8 = ENUM_T(6)  #  8-byte string
DATATYPE_STRING32 = ENUM_T(7)  #  32-byte string
DATATYPE_STRING64 = ENUM_T(8)  #  64-byte string
DATATYPE_STRING128 = ENUM_T(9)  #  128-byte string
DATATYPE_STRING256 = ENUM_T(10)  #  256-byte string
DATATYPE_STRING260 = ENUM_T(11)  #  260-byte string
DATATYPE_STRINGV = ENUM_T(12)  #  variable-length string

DATATYPE_INITPOSITION = ENUM_T(13)  #  see SIMCONNECT_DATA_INITPOSITION
DATATYPE_MARKERSTATE = ENUM_T(14)  #  see SIMCONNECT_DATA_MARKERSTATE
DATATYPE_WAYPOINT = ENUM_T(15)  #  see SIMCONNECT_DATA_WAYPOINT
DATATYPE_LATLONALT = ENUM_T(16)  #  see SIMCONNECT_DATA_LATLONALT
DATATYPE_XYZ = ENUM_T(17)  #  see SIMCONNECT_DATA_XYZ

DATATYPE_MAX = ENUM_T(18) #  enum limit


#  Exception error types
EXCEPTION = ENUM_T
EXCEPTION_NONE = ENUM_T(1) 

EXCEPTION_ERROR = ENUM_T(2) 
EXCEPTION_SIZE_MISMATCH = ENUM_T(3) 
EXCEPTION_UNRECOGNIZED_ID = ENUM_T(4) 
EXCEPTION_UNOPENED = ENUM_T(5) 
EXCEPTION_VERSION_MISMATCH = ENUM_T(6) 
EXCEPTION_TOO_MANY_GROUPS = ENUM_T(7) 
EXCEPTION_NAME_UNRECOGNIZED = ENUM_T(8) 
EXCEPTION_TOO_MANY_EVENT_NAMES = ENUM_T(9) 
EXCEPTION_EVENT_ID_DUPLICATE = ENUM_T(10) 
EXCEPTION_TOO_MANY_MAPS = ENUM_T(11) 
EXCEPTION_TOO_MANY_OBJECTS = ENUM_T(12) 
EXCEPTION_TOO_MANY_REQUESTS = ENUM_T(13) 
EXCEPTION_WEATHER_INVALID_PORT = ENUM_T(14) 
EXCEPTION_WEATHER_INVALID_METAR = ENUM_T(15) 
EXCEPTION_WEATHER_UNABLE_TO_GET_OBSERVATION = ENUM_T(16) 
EXCEPTION_WEATHER_UNABLE_TO_CREATE_STATION = ENUM_T(17) 
EXCEPTION_WEATHER_UNABLE_TO_REMOVE_STATION = ENUM_T(18) 
EXCEPTION_INVALID_DATA_TYPE = ENUM_T(19) 
EXCEPTION_INVALID_DATA_SIZE = ENUM_T(20) 
EXCEPTION_DATA_ERROR = ENUM_T(21) 
EXCEPTION_INVALID_ARRAY = ENUM_T(22) 
EXCEPTION_CREATE_OBJECT_FAILED = ENUM_T(23) 
EXCEPTION_LOAD_FLIGHTPLAN_FAILED = ENUM_T(24) 
EXCEPTION_OPERATION_INVALID_FOR_OBJECT_TYPE = ENUM_T(25) 
EXCEPTION_ILLEGAL_OPERATION = ENUM_T(26) 
EXCEPTION_ALREADY_SUBSCRIBED = ENUM_T(27) 
EXCEPTION_INVALID_ENUM = ENUM_T(28) 
EXCEPTION_DEFINITION_ERROR = ENUM_T(29) 
EXCEPTION_DUPLICATE_ID = ENUM_T(30) 
EXCEPTION_DATUM_ID = ENUM_T(31) 
EXCEPTION_OUT_OF_BOUNDS = ENUM_T(32) 
EXCEPTION_ALREADY_CREATED = ENUM_T(33) 
EXCEPTION_OBJECT_OUTSIDE_REALITY_BUBBLE = ENUM_T(34) 
EXCEPTION_OBJECT_CONTAINER = ENUM_T(35) 
EXCEPTION_OBJECT_AI = ENUM_T(36) 
EXCEPTION_OBJECT_ATC = ENUM_T(37) 
EXCEPTION_OBJECT_SCHEDULE = ENUM_T(38) 


#  Object types
SIMOBJECT_TYPE = ENUM_T
SIMOBJECT_TYPE_USER = ENUM_T(1) 
SIMOBJECT_TYPE_ALL = ENUM_T(2) 
SIMOBJECT_TYPE_AIRCRAFT = ENUM_T(3) 
SIMOBJECT_TYPE_HELICOPTER = ENUM_T(4) 
SIMOBJECT_TYPE_BOAT = ENUM_T(5) 
SIMOBJECT_TYPE_GROUND = ENUM_T(6) 


#  EventState values
STATE = ENUM_T
STATE_OFF = ENUM_T(1) 
STATE_ON = ENUM_T(2) 


#  Object Data Request Period values
PERIOD = ENUM_T
PERIOD_NEVER = ENUM_T(1) 
PERIOD_ONCE = ENUM_T(2) 
PERIOD_VISUAL_FRAME = ENUM_T(3) 
PERIOD_SIM_FRAME = ENUM_T(4) 
PERIOD_SECOND = ENUM_T(5) 



MISSION_END = ENUM_T
MISSION_FAILED = ENUM_T(1) 
MISSION_CRASHED = ENUM_T(2) 
MISSION_SUCCEEDED = ENUM_T(3) 


#  ClientData Request Period values
CLIENT_DATA_PERIOD = ENUM_T
CLIENT_DATA_PERIOD_NEVER = ENUM_T(1) 
CLIENT_DATA_PERIOD_ONCE = ENUM_T(2) 
CLIENT_DATA_PERIOD_VISUAL_FRAME = ENUM_T(3) 
CLIENT_DATA_PERIOD_ON_SET = ENUM_T(4) 
CLIENT_DATA_PERIOD_SECOND = ENUM_T(5) 


TEXT_TYPE = ENUM_T
TEXT_TYPE_SCROLL_BLACK = ENUM_T(1) 
TEXT_TYPE_SCROLL_WHITE = ENUM_T(2) 
TEXT_TYPE_SCROLL_RED = ENUM_T(3) 
TEXT_TYPE_SCROLL_GREEN = ENUM_T(4) 
TEXT_TYPE_SCROLL_BLUE = ENUM_T(5) 
TEXT_TYPE_SCROLL_YELLOW = ENUM_T(6) 
TEXT_TYPE_SCROLL_MAGENTA = ENUM_T(7) 
TEXT_TYPE_SCROLL_CYAN = ENUM_T(8) 
TEXT_TYPE_PRINT_BLACK = ENUM_T(0x0100) 
TEXT_TYPE_PRINT_WHITE = ENUM_T(257) 
TEXT_TYPE_PRINT_RED = ENUM_T(258) 
TEXT_TYPE_PRINT_GREEN = ENUM_T(259) 
TEXT_TYPE_PRINT_BLUE = ENUM_T(260) 
TEXT_TYPE_PRINT_YELLOW = ENUM_T(261) 
TEXT_TYPE_PRINT_MAGENTA = ENUM_T(262) 
TEXT_TYPE_PRINT_CYAN = ENUM_T(263) 
TEXT_TYPE_MENU = ENUM_T(0x0200) 


TEXT_RESULT = ENUM_T
TEXT_RESULT_MENU_SELECT_1 = ENUM_T(1) 
TEXT_RESULT_MENU_SELECT_2 = ENUM_T(2) 
TEXT_RESULT_MENU_SELECT_3 = ENUM_T(3) 
TEXT_RESULT_MENU_SELECT_4 = ENUM_T(4) 
TEXT_RESULT_MENU_SELECT_5 = ENUM_T(5) 
TEXT_RESULT_MENU_SELECT_6 = ENUM_T(6) 
TEXT_RESULT_MENU_SELECT_7 = ENUM_T(7) 
TEXT_RESULT_MENU_SELECT_8 = ENUM_T(8) 
TEXT_RESULT_MENU_SELECT_9 = ENUM_T(9) 
TEXT_RESULT_MENU_SELECT_10 = ENUM_T(10) 
TEXT_RESULT_DISPLAYED = ENUM_T(0x00010000) 
TEXT_RESULT_QUEUED = ENUM_T(65537) 
TEXT_RESULT_REMOVED = ENUM_T(65538) 
TEXT_RESULT_REPLACED = ENUM_T(65539) 
TEXT_RESULT_TIMEOUT = ENUM_T(65540) 


WEATHER_MODE = ENUM_T
WEATHER_MODE_THEME = ENUM_T(1) 
WEATHER_MODE_RWW = ENUM_T(2) 
WEATHER_MODE_CUSTOM = ENUM_T(3) 
WEATHER_MODE_GLOBAL = ENUM_T(4) 


FACILITY_LIST_TYPE = ENUM_T
FACILITY_LIST_TYPE_AIRPORT = ENUM_T(1) 
FACILITY_LIST_TYPE_WAYPOINT = ENUM_T(2) 
FACILITY_LIST_TYPE_NDB = ENUM_T(3) 
FACILITY_LIST_TYPE_VOR = ENUM_T(4) 
FACILITY_LIST_TYPE_COUNT = ENUM_T(5) #  invalid 



VOR_FLAGS = DWORD  #  flags for SIMCONNECT_RECV_ID_VOR_LIST 
RECV_ID_VOR_LIST_HAS_NAV_SIGNAL: DWORD = DWORD(0x00000001)  #  Has Nav signal
RECV_ID_VOR_LIST_HAS_LOCALIZER: DWORD = DWORD(0x00000002)  #  Has localizer
RECV_ID_VOR_LIST_HAS_GLIDE_SLOPE: DWORD = DWORD(0x00000004)  #  Has Nav signal
RECV_ID_VOR_LIST_HAS_DME: DWORD = DWORD(0x00000008)  #  Station has DME



#  bits for the Waypoint Flags field: may be combined
WAYPOINT_FLAGS = DWORD 
WAYPOINT_NONE: DWORD = DWORD(0x00) 
WAYPOINT_SPEED_REQUESTED: DWORD = DWORD(0x04)  #  requested speed at waypoint is valid
WAYPOINT_THROTTLE_REQUESTED: DWORD = DWORD(0x08)  #  request a specific throttle percentage
WAYPOINT_COMPUTE_VERTICAL_SPEED: DWORD = DWORD(0x10)  #  compute vertical to speed to reach waypoint altitude when crossing the waypoint
WAYPOINT_ALTITUDE_IS_AGL: DWORD = DWORD(0x20)  #  AltitudeIsAGL
WAYPOINT_ON_GROUND: DWORD = DWORD(0x00100000)  #  place this waypoint on the ground
WAYPOINT_REVERSE: DWORD = DWORD(0x00200000)  #  Back up to this waypoint. Only valid on first waypoint
WAYPOINT_WRAP_TO_FIRST: DWORD = DWORD(0x00400000)  #  Wrap around back to first waypoint. Only valid on last waypoint.

EVENT_FLAG = DWORD 
EVENT_FLAG_DEFAULT: DWORD = DWORD(0x00000000) 
EVENT_FLAG_FAST_REPEAT_TIMER: DWORD = DWORD(0x00000001)  #  set event repeat timer to simulate fast repeat
EVENT_FLAG_SLOW_REPEAT_TIMER: DWORD = DWORD(0x00000002)  #  set event repeat timer to simulate slow repeat
EVENT_FLAG_GROUPID_IS_PRIORITY: DWORD = DWORD(0x00000010)  #  interpret GroupID parameter as priority value

DATA_REQUEST_FLAG = DWORD 
DATA_REQUEST_FLAG_DEFAULT: DWORD = DWORD(0x00000000) 
DATA_REQUEST_FLAG_CHANGED: DWORD = DWORD(0x00000001)  #  send requested data when value(s) change
DATA_REQUEST_FLAG_TAGGED: DWORD = DWORD(0x00000002)  #  send requested data in tagged format

DATA_SET_FLAG = DWORD 
DATA_SET_FLAG_DEFAULT: DWORD = DWORD(0x00000000) 
DATA_SET_FLAG_TAGGED: DWORD = DWORD(0x00000001)  #  data is in tagged format

CREATE_CLIENT_DATA_FLAG = DWORD 
CREATE_CLIENT_DATA_FLAG_DEFAULT: DWORD = DWORD(0x00000000) 
CREATE_CLIENT_DATA_FLAG_READ_ONLY: DWORD = DWORD(0x00000001)  #  permit only ClientData creator to write into ClientData


CLIENT_DATA_REQUEST_FLAG = DWORD 
CLIENT_DATA_REQUEST_FLAG_DEFAULT: DWORD = DWORD(0x00000000) 
CLIENT_DATA_REQUEST_FLAG_CHANGED: DWORD = DWORD(0x00000001)  #  send requested ClientData when value(s) change
CLIENT_DATA_REQUEST_FLAG_TAGGED: DWORD = DWORD(0x00000002)  #  send requested ClientData in tagged format

CLIENT_DATA_SET_FLAG = DWORD 
CLIENT_DATA_SET_FLAG_DEFAULT: DWORD = DWORD(0x00000000) 
CLIENT_DATA_SET_FLAG_TAGGED: DWORD = DWORD(0x00000001)  #  data is in tagged format


VIEW_SYSTEM_EVENT_DATA = DWORD  #  dwData contains these flags for the "View" System Event
VIEW_SYSTEM_EVENT_DATA_COCKPIT_2D: DWORD = DWORD(0x00000001)  #  2D Panels in cockpit view
VIEW_SYSTEM_EVENT_DATA_COCKPIT_VIRTUAL: DWORD = DWORD(0x00000002)  #  Virtual (3D) panels in cockpit view
VIEW_SYSTEM_EVENT_DATA_ORTHOGONAL: DWORD = DWORD(0x00000004)  #  Orthogonal (Map) view

SOUND_SYSTEM_EVENT_DATA = DWORD  #  dwData contains these flags for the "Sound" System Event
SOUND_SYSTEM_EVENT_DATA_MASTER: DWORD = DWORD(0x00000001)  #  Sound Master
# 357 "SimConnect.h"
# ----------------------------------------------------------------------------
#         User-defined enums
# ----------------------------------------------------------------------------

NOTIFICATION_GROUP_ID = DWORD  # client-defined notification group ID
INPUT_GROUP_ID = DWORD  # client-defined input group ID
DATA_DEFINITION_ID = DWORD  # client-defined data definition ID
DATA_REQUEST_ID = DWORD  # client-defined request data ID

CLIENT_EVENT_ID = DWORD  # client-defined client event ID
CLIENT_DATA_ID = DWORD  # client-defined client data ID
CLIENT_DATA_DEFINITION_ID = DWORD  # client-defined client data definition ID


# ----------------------------------------------------------------------------
#         Struct definitions
# ----------------------------------------------------------------------------

#pragma pack(push, 1)

class RECV(Structure):
    _fields_ = [
        ("dwSize", DWORD),  #  record size
        ("dwVersion", DWORD),  #  interface version
        ("dwID", DWORD),  #  see SIMCONNECT_RECV_ID
    ]

class RECV_EXCEPTION(RECV):
    UNKNOWN_SENDID: DWORD = DWORD(0) 
    UNKNOWN_INDEX: DWORD = DWORD(0xFFFFFFFF) 
    _fields_ = [
        ("dwException", DWORD),  #  see SIMCONNECT_EXCEPTION
        ("dwSendID", DWORD),  #  see SimConnect_GetLastSentPacketID
        ("dwIndex", DWORD),  #  index of parameter that was source of error
    ]

class RECV_OPEN(RECV):
    _fields_ = [
        ("szApplicationName", c_char * 256), 
        ("dwApplicationVersionMajor", DWORD), 
        ("dwApplicationVersionMinor", DWORD), 
        ("dwApplicationBuildMajor", DWORD), 
        ("dwApplicationBuildMinor", DWORD), 
        ("dwSimConnectVersionMajor", DWORD), 
        ("dwSimConnectVersionMinor", DWORD), 
        ("dwSimConnectBuildMajor", DWORD), 
        ("dwSimConnectBuildMinor", DWORD), 
        ("dwReserved1", DWORD), 
        ("dwReserved2", DWORD), 
    ]

class RECV_QUIT(RECV):
    _fields_ = [
    ]

class RECV_EVENT(RECV):
    UNKNOWN_GROUP: DWORD = DWORD(0xFFFFFFFF) 
    _fields_ = [
        ("uGroupID", DWORD), 
        ("uEventID", DWORD), 
        ("dwData", DWORD),  #  uEventID-dependent context
    ]

class RECV_EVENT_FILENAME(RECV_EVENT):
    _fields_ = [
        ("szFileName", c_char * MAX_PATH),  #  uEventID-dependent context
        ("dwFlags", DWORD), 
    ]

class RECV_EVENT_OBJECT_ADDREMOVE(RECV_EVENT):
    _fields_ = [
        ("eObjType", SIMOBJECT_TYPE), 
    ]

class RECV_EVENT_FRAME(RECV_EVENT):
    _fields_ = [
        ("fFrameRate", c_float), 
        ("fSimSpeed", c_float), 
    ]

class RECV_EVENT_MULTIPLAYER_SERVER_STARTED(RECV_EVENT):
    #  No event specific data, for now
    _fields_ = [
    ]

class RECV_EVENT_MULTIPLAYER_CLIENT_STARTED(RECV_EVENT):
    #  No event specific data, for now
    _fields_ = [
    ]

class RECV_EVENT_MULTIPLAYER_SESSION_ENDED(RECV_EVENT):
    #  No event specific data, for now
    _fields_ = [
    ]

#  SIMCONNECT_DATA_RACE_RESULT
class DATA_RACE_RESULT(Structure):
    _fields_ = [
        ("dwNumberOfRacers", DWORD),  #  The total number of racers
        ("MissionGUID", GUID),  #  The name of the mission to execute, NULL if no mission
        ("szPlayerName", c_char * MAX_PATH),  #  The name of the player
        ("szSessionType", c_char * MAX_PATH),  #  The type of the multiplayer session: "LAN", "GAMESPY")
        ("szAircraft", c_char * MAX_PATH),  #  The aircraft type 
        ("szPlayerRole", c_char * MAX_PATH),  #  The player role in the mission
        ("fTotalTime", c_double),  #  Total time in seconds, 0 means DNF
        ("fPenaltyTime", c_double),  #  Total penalty time in seconds
        ("dwIsDisqualified", DWORD),  #  non 0 - disqualified, 0 - not disqualified
    ]

class RECV_EVENT_RACE_END(RECV_EVENT):
    _fields_ = [
        ("dwRacerNumber", DWORD),  #  The index of the racer the results are for
        ("RacerData", DATA_RACE_RESULT), 
    ]

class RECV_EVENT_RACE_LAP(RECV_EVENT):
    _fields_ = [
        ("dwLapIndex", DWORD),  #  The index of the lap the results are for
        ("RacerData", DATA_RACE_RESULT), 
    ]

class RECV_SIMOBJECT_DATA(RECV):
    _fields_ = [
        ("dwRequestID", DWORD), 
        ("dwObjectID", DWORD), 
        ("dwDefineID", DWORD), 
        ("dwFlags", DWORD),  #  SIMCONNECT_DATA_REQUEST_FLAG
        ("dwentrynumber", DWORD),  #  if multiple objects returned, this is number <entrynumber> out of <outof>.
        ("dwoutof", DWORD),  #  note: starts with 1, not 0.          
        ("dwDefineCount", DWORD),  #  data count (number of datums, *not* byte count)
        ("dwData", DWORD),  #  data begins here, dwDefineCount data items
    ]

class RECV_SIMOBJECT_DATA_BYTYPE(RECV_SIMOBJECT_DATA):
    _fields_ = [
    ]

class RECV_CLIENT_DATA(RECV_SIMOBJECT_DATA):
    _fields_ = [
    ]

class RECV_WEATHER_OBSERVATION(RECV):
    _fields_ = [
        ("dwRequestID", DWORD), 
        ("szMetar", c_char * 1),  #  Variable length string whose maximum size is MAX_METAR_LENGTH
    ]

CLOUD_STATE_ARRAY_WIDTH: int = 64 
CLOUD_STATE_ARRAY_SIZE: int = CLOUD_STATE_ARRAY_WIDTH*CLOUD_STATE_ARRAY_WIDTH 

class RECV_CLOUD_STATE(RECV):
    _fields_ = [
        ("dwRequestID", DWORD), 
        ("dwArraySize", DWORD), 
        ("rgbData", BYTE * 1), 
    ]

class RECV_ASSIGNED_OBJECT_ID(RECV):
    _fields_ = [
        ("dwRequestID", DWORD), 
        ("dwObjectID", DWORD), 
    ]

class RECV_RESERVED_KEY(RECV):
    _fields_ = [
        ("szChoiceReserved", c_char * 30), 
        ("szReservedKey", c_char * 50), 
    ]

class RECV_SYSTEM_STATE(RECV):
    _fields_ = [
        ("dwRequestID", DWORD), 
        ("dwInteger", DWORD), 
        ("fFloat", c_float), 
        ("szString", c_char * MAX_PATH), 
    ]

class RECV_CUSTOM_ACTION(RECV_EVENT):
    _fields_ = [
        ("guidInstanceId", GUID),  #  Instance id of the action that executed
        ("dwWaitForCompletion", DWORD),  #  Wait for completion flag on the action
        ("szPayLoad", c_char * 1),  #  Variable length string payload associated with the mission action.  
    ]

class RECV_EVENT_WEATHER_MODE(RECV_EVENT):
    #  No event specific data - the new weather mode is in the base structure dwData member.
    _fields_ = [
    ]

#  SIMCONNECT_RECV_FACILITIES_LIST
class RECV_FACILITIES_LIST(RECV):
    _fields_ = [
        ("dwRequestID", DWORD), 
        ("dwArraySize", DWORD), 
        ("dwEntryNumber", DWORD),  #  when the array of items is too big for one send, which send this is (0..dwOutOf-1)
        ("dwOutOf", DWORD),  #  total number of transmissions the list is chopped into
    ]

#  SIMCONNECT_DATA_FACILITY_AIRPORT
class DATA_FACILITY_AIRPORT(Structure):
    _fields_ = [
        ("Icao", c_char * 9),  #  ICAO of the object
        ("Latitude", c_double),  #  degrees
        ("Longitude", c_double),  #  degrees
        ("Altitude", c_double),  #  meters   
    ]

#  SIMCONNECT_RECV_AIRPORT_LIST
class RECV_AIRPORT_LIST(RECV_FACILITIES_LIST):
    _fields_ = [
        ("rgData", DATA_FACILITY_AIRPORT * 1), 
    ]


#  SIMCONNECT_DATA_FACILITY_WAYPOINT
class DATA_FACILITY_WAYPOINT(DATA_FACILITY_AIRPORT):
    _fields_ = [
        ("fMagVar", c_float),  #  Magvar in degrees
    ]

#  SIMCONNECT_RECV_WAYPOINT_LIST
class RECV_WAYPOINT_LIST(RECV_FACILITIES_LIST):
    _fields_ = [
        ("rgData", DATA_FACILITY_WAYPOINT * 1), 
    ]

#  SIMCONNECT_DATA_FACILITY_NDB
class DATA_FACILITY_NDB(DATA_FACILITY_WAYPOINT):
    _fields_ = [
        ("fFrequency", DWORD),  #  frequency in Hz
    ]

#  SIMCONNECT_RECV_NDB_LIST
class RECV_NDB_LIST(RECV_FACILITIES_LIST):
    _fields_ = [
        ("rgData", DATA_FACILITY_NDB * 1), 
    ]

#  SIMCONNECT_DATA_FACILITY_VOR
class DATA_FACILITY_VOR(DATA_FACILITY_NDB):
    _fields_ = [
        ("Flags", DWORD),  #  SIMCONNECT_VOR_FLAGS
        ("fLocalizer", c_float),  #  Localizer in degrees
        ("GlideLat", c_double),  #  Glide Slope Location (deg, deg, meters)
        ("GlideLon", c_double), 
        ("GlideAlt", c_double), 
        ("fGlideSlopeAngle", c_float),  #  Glide Slope in degrees
    ]

#  SIMCONNECT_RECV_VOR_LIST
class RECV_VOR_LIST(RECV_FACILITIES_LIST):
    _fields_ = [
        ("rgData", DATA_FACILITY_VOR * 1), 
    ]
# 632 "SimConnect.h"
#  SIMCONNECT_DATATYPE_INITPOSITION
class DATA_INITPOSITION(Structure):
    _fields_ = [
        ("Latitude", c_double),  #  degrees
        ("Longitude", c_double),  #  degrees
        ("Altitude", c_double),  #  feet   
        ("Pitch", c_double),  #  degrees
        ("Bank", c_double),  #  degrees
        ("Heading", c_double),  #  degrees
        ("OnGround", DWORD),  #  1=force to be on the ground
        ("Airspeed", DWORD),  #  knots
    ]


#  SIMCONNECT_DATATYPE_MARKERSTATE
class DATA_MARKERSTATE(Structure):
    _fields_ = [
        ("szMarkerName", c_char * 64), 
        ("dwMarkerState", DWORD), 
    ]

#  SIMCONNECT_DATATYPE_WAYPOINT
class DATA_WAYPOINT(Structure):
    _fields_ = [
        ("Latitude", c_double),  #  degrees
        ("Longitude", c_double),  #  degrees
        ("Altitude", c_double),  #  feet   
        ("Flags", c_long), 
        ("ktsSpeed", c_double),  #  knots
        ("percentThrottle", c_double), 
    ]

#  SIMCONNECT_DATA_LATLONALT
class DATA_LATLONALT(Structure):
    _fields_ = [
        ("Latitude", c_double), 
        ("Longitude", c_double), 
        ("Altitude", c_double), 
    ]

#  SIMCONNECT_DATA_XYZ
class DATA_XYZ(Structure):
    _fields_ = [
        ("x", c_double), 
        ("y", c_double), 
        ("z", c_double), 
    ]

#pragma pack(pop)

# ----------------------------------------------------------------------------
#         End of Struct definitions
# ----------------------------------------------------------------------------

# typedef void (CALLBACK *DispatchProc)(SIMCONNECT_RECV* pData, DWORD cbData, void* pContext);
DispatchProc = WINFUNCTYPE(None, POINTER(RECV), DWORD, c_void_p)
# 703 "SimConnect.h"

def _decls(dll):
    _ = dict()
    f = dll.SimConnect_MapClientEventToSimEvent
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        CLIENT_EVENT_ID, # SIMCONNECT_CLIENT_EVENT_ID EventID 
        c_char_p, # const char * EventName default {dflt}
    ]
    _['MapClientEventToSimEvent'] = f
    f = dll.SimConnect_TransmitClientEvent
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        OBJECT_ID, # SIMCONNECT_OBJECT_ID ObjectID 
        CLIENT_EVENT_ID, # SIMCONNECT_CLIENT_EVENT_ID EventID 
        DWORD, # DWORD dwData 
        NOTIFICATION_GROUP_ID, # SIMCONNECT_NOTIFICATION_GROUP_ID GroupID 
        EVENT_FLAG, # SIMCONNECT_EVENT_FLAG Flags 
    ]
    _['TransmitClientEvent'] = f
    f = dll.SimConnect_SetSystemEventState
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        CLIENT_EVENT_ID, # SIMCONNECT_CLIENT_EVENT_ID EventID 
        STATE, # SIMCONNECT_STATE dwState 
    ]
    _['SetSystemEventState'] = f
    f = dll.SimConnect_AddClientEventToNotificationGroup
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        NOTIFICATION_GROUP_ID, # SIMCONNECT_NOTIFICATION_GROUP_ID GroupID 
        CLIENT_EVENT_ID, # SIMCONNECT_CLIENT_EVENT_ID EventID 
        c_bool, # BOOL bMaskable default {dflt}
    ]
    _['AddClientEventToNotificationGroup'] = f
    f = dll.SimConnect_RemoveClientEvent
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        NOTIFICATION_GROUP_ID, # SIMCONNECT_NOTIFICATION_GROUP_ID GroupID 
        CLIENT_EVENT_ID, # SIMCONNECT_CLIENT_EVENT_ID EventID 
    ]
    _['RemoveClientEvent'] = f
    f = dll.SimConnect_SetNotificationGroupPriority
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        NOTIFICATION_GROUP_ID, # SIMCONNECT_NOTIFICATION_GROUP_ID GroupID 
        DWORD, # DWORD uPriority 
    ]
    _['SetNotificationGroupPriority'] = f
    f = dll.SimConnect_ClearNotificationGroup
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        NOTIFICATION_GROUP_ID, # SIMCONNECT_NOTIFICATION_GROUP_ID GroupID 
    ]
    _['ClearNotificationGroup'] = f
    f = dll.SimConnect_RequestNotificationGroup
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        NOTIFICATION_GROUP_ID, # SIMCONNECT_NOTIFICATION_GROUP_ID GroupID 
        DWORD, # DWORD dwReserved default {dflt}
        DWORD, # DWORD Flags default {dflt}
    ]
    _['RequestNotificationGroup'] = f
    f = dll.SimConnect_AddToDataDefinition
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DATA_DEFINITION_ID, # SIMCONNECT_DATA_DEFINITION_ID DefineID 
        c_char_p, # const char * DatumName 
        c_char_p, # const char * UnitsName 
        DATATYPE, # SIMCONNECT_DATATYPE DatumType default {dflt}
        c_float, # float fEpsilon default {dflt}
        DWORD, # DWORD DatumID default {dflt}
    ]
    _['AddToDataDefinition'] = f
    f = dll.SimConnect_ClearDataDefinition
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DATA_DEFINITION_ID, # SIMCONNECT_DATA_DEFINITION_ID DefineID 
    ]
    _['ClearDataDefinition'] = f
    f = dll.SimConnect_RequestDataOnSimObject
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
        DATA_DEFINITION_ID, # SIMCONNECT_DATA_DEFINITION_ID DefineID 
        OBJECT_ID, # SIMCONNECT_OBJECT_ID ObjectID 
        PERIOD, # SIMCONNECT_PERIOD Period 
        DATA_REQUEST_FLAG, # SIMCONNECT_DATA_REQUEST_FLAG Flags default {dflt}
        DWORD, # DWORD origin default {dflt}
        DWORD, # DWORD interval default {dflt}
        DWORD, # DWORD limit default {dflt}
    ]
    _['RequestDataOnSimObject'] = f
    f = dll.SimConnect_RequestDataOnSimObjectType
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
        DATA_DEFINITION_ID, # SIMCONNECT_DATA_DEFINITION_ID DefineID 
        DWORD, # DWORD dwRadiusMeters 
        SIMOBJECT_TYPE, # SIMCONNECT_SIMOBJECT_TYPE type 
    ]
    _['RequestDataOnSimObjectType'] = f
    f = dll.SimConnect_SetDataOnSimObject
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DATA_DEFINITION_ID, # SIMCONNECT_DATA_DEFINITION_ID DefineID 
        OBJECT_ID, # SIMCONNECT_OBJECT_ID ObjectID 
        DATA_SET_FLAG, # SIMCONNECT_DATA_SET_FLAG Flags 
        DWORD, # DWORD ArrayCount 
        DWORD, # DWORD cbUnitSize 
        c_void_p, # void * pDataSet 
    ]
    _['SetDataOnSimObject'] = f
    f = dll.SimConnect_MapInputEventToClientEvent
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        INPUT_GROUP_ID, # SIMCONNECT_INPUT_GROUP_ID GroupID 
        c_char_p, # const char * szInputDefinition 
        CLIENT_EVENT_ID, # SIMCONNECT_CLIENT_EVENT_ID DownEventID 
        DWORD, # DWORD DownValue default {dflt}
        CLIENT_EVENT_ID, # SIMCONNECT_CLIENT_EVENT_ID UpEventID default {dflt}
    ]
    _['MapInputEventToClientEvent'] = f
    f = dll.SimConnect_SetInputGroupPriority
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        INPUT_GROUP_ID, # SIMCONNECT_INPUT_GROUP_ID GroupID 
        DWORD, # DWORD uPriority 
    ]
    _['SetInputGroupPriority'] = f
    f = dll.SimConnect_RemoveInputEvent
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        INPUT_GROUP_ID, # SIMCONNECT_INPUT_GROUP_ID GroupID 
        c_char_p, # const char * szInputDefinition 
    ]
    _['RemoveInputEvent'] = f
    f = dll.SimConnect_ClearInputGroup
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        INPUT_GROUP_ID, # SIMCONNECT_INPUT_GROUP_ID GroupID 
    ]
    _['ClearInputGroup'] = f
    f = dll.SimConnect_SetInputGroupState
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        INPUT_GROUP_ID, # SIMCONNECT_INPUT_GROUP_ID GroupID 
        DWORD, # DWORD dwState 
    ]
    _['SetInputGroupState'] = f
    f = dll.SimConnect_RequestReservedKey
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        CLIENT_EVENT_ID, # SIMCONNECT_CLIENT_EVENT_ID EventID 
        c_char_p, # const char * szKeyChoice1 default {dflt}
        c_char_p, # const char * szKeyChoice2 default {dflt}
        c_char_p, # const char * szKeyChoice3 default {dflt}
    ]
    _['RequestReservedKey'] = f
    f = dll.SimConnect_SubscribeToSystemEvent
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        CLIENT_EVENT_ID, # SIMCONNECT_CLIENT_EVENT_ID EventID 
        c_char_p, # const char * SystemEventName 
    ]
    _['SubscribeToSystemEvent'] = f
    f = dll.SimConnect_UnsubscribeFromSystemEvent
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        CLIENT_EVENT_ID, # SIMCONNECT_CLIENT_EVENT_ID EventID 
    ]
    _['UnsubscribeFromSystemEvent'] = f
    f = dll.SimConnect_WeatherRequestInterpolatedObservation
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
        c_float, # float lat 
        c_float, # float lon 
        c_float, # float alt 
    ]
    _['WeatherRequestInterpolatedObservation'] = f
    f = dll.SimConnect_WeatherRequestObservationAtStation
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
        c_char_p, # const char * szICAO 
    ]
    _['WeatherRequestObservationAtStation'] = f
    f = dll.SimConnect_WeatherRequestObservationAtNearestStation
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
        c_float, # float lat 
        c_float, # float lon 
    ]
    _['WeatherRequestObservationAtNearestStation'] = f
    f = dll.SimConnect_WeatherCreateStation
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
        c_char_p, # const char * szICAO 
        c_char_p, # const char * szName 
        c_float, # float lat 
        c_float, # float lon 
        c_float, # float alt 
    ]
    _['WeatherCreateStation'] = f
    f = dll.SimConnect_WeatherRemoveStation
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
        c_char_p, # const char * szICAO 
    ]
    _['WeatherRemoveStation'] = f
    f = dll.SimConnect_WeatherSetObservation
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DWORD, # DWORD Seconds 
        c_char_p, # const char * szMETAR 
    ]
    _['WeatherSetObservation'] = f
    f = dll.SimConnect_WeatherSetModeServer
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DWORD, # DWORD dwPort 
        DWORD, # DWORD dwSeconds 
    ]
    _['WeatherSetModeServer'] = f
    f = dll.SimConnect_WeatherSetModeTheme
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        c_char_p, # const char * szThemeName 
    ]
    _['WeatherSetModeTheme'] = f
    f = dll.SimConnect_WeatherSetModeGlobal
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
    ]
    _['WeatherSetModeGlobal'] = f
    f = dll.SimConnect_WeatherSetModeCustom
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
    ]
    _['WeatherSetModeCustom'] = f
    f = dll.SimConnect_WeatherSetDynamicUpdateRate
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DWORD, # DWORD dwRate 
    ]
    _['WeatherSetDynamicUpdateRate'] = f
    f = dll.SimConnect_WeatherRequestCloudState
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
        c_float, # float minLat 
        c_float, # float minLon 
        c_float, # float minAlt 
        c_float, # float maxLat 
        c_float, # float maxLon 
        c_float, # float maxAlt 
        DWORD, # DWORD dwFlags default {dflt}
    ]
    _['WeatherRequestCloudState'] = f
    f = dll.SimConnect_WeatherCreateThermal
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
        c_float, # float lat 
        c_float, # float lon 
        c_float, # float alt 
        c_float, # float radius 
        c_float, # float height 
        c_float, # float coreRate default {dflt}
        c_float, # float coreTurbulence default {dflt}
        c_float, # float sinkRate default {dflt}
        c_float, # float sinkTurbulence default {dflt}
        c_float, # float coreSize default {dflt}
        c_float, # float coreTransitionSize default {dflt}
        c_float, # float sinkLayerSize default {dflt}
        c_float, # float sinkTransitionSize default {dflt}
    ]
    _['WeatherCreateThermal'] = f
    f = dll.SimConnect_WeatherRemoveThermal
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        OBJECT_ID, # SIMCONNECT_OBJECT_ID ObjectID 
    ]
    _['WeatherRemoveThermal'] = f
    f = dll.SimConnect_AICreateParkedATCAircraft
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        c_char_p, # const char * szContainerTitle 
        c_char_p, # const char * szTailNumber 
        c_char_p, # const char * szAirportID 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
    ]
    _['AICreateParkedATCAircraft'] = f
    f = dll.SimConnect_AICreateEnrouteATCAircraft
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        c_char_p, # const char * szContainerTitle 
        c_char_p, # const char * szTailNumber 
        c_int, # int iFlightNumber 
        c_char_p, # const char * szFlightPlanPath 
        c_double, # double dFlightPlanPosition 
        c_bool, # BOOL bTouchAndGo 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
    ]
    _['AICreateEnrouteATCAircraft'] = f
    f = dll.SimConnect_AICreateNonATCAircraft
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        c_char_p, # const char * szContainerTitle 
        c_char_p, # const char * szTailNumber 
        DATA_INITPOSITION, # SIMCONNECT_DATA_INITPOSITION InitPos 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
    ]
    _['AICreateNonATCAircraft'] = f
    f = dll.SimConnect_AICreateSimulatedObject
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        c_char_p, # const char * szContainerTitle 
        DATA_INITPOSITION, # SIMCONNECT_DATA_INITPOSITION InitPos 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
    ]
    _['AICreateSimulatedObject'] = f
    f = dll.SimConnect_AIReleaseControl
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        OBJECT_ID, # SIMCONNECT_OBJECT_ID ObjectID 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
    ]
    _['AIReleaseControl'] = f
    f = dll.SimConnect_AIRemoveObject
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        OBJECT_ID, # SIMCONNECT_OBJECT_ID ObjectID 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
    ]
    _['AIRemoveObject'] = f
    f = dll.SimConnect_AISetAircraftFlightPlan
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        OBJECT_ID, # SIMCONNECT_OBJECT_ID ObjectID 
        c_char_p, # const char * szFlightPlanPath 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
    ]
    _['AISetAircraftFlightPlan'] = f
    f = dll.SimConnect_ExecuteMissionAction
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        GUID, # const GUID guidInstanceId 
    ]
    _['ExecuteMissionAction'] = f
    f = dll.SimConnect_CompleteCustomMissionAction
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        GUID, # const GUID guidInstanceId 
    ]
    _['CompleteCustomMissionAction'] = f
    f = dll.SimConnect_Close
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
    ]
    _['Close'] = f
    f = dll.SimConnect_RetrieveString
    f.restype = HRESULT
    f.argtypes = [
        POINTER(RECV), # SIMCONNECT_RECV * pData 
        DWORD, # DWORD cbData 
        c_void_p, # void * pStringV 
        POINTER(c_char_p), # char ** pszString 
        POINTER(DWORD), # DWORD * pcbString 
    ]
    _['RetrieveString'] = f
    f = dll.SimConnect_GetLastSentPacketID
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        POINTER(DWORD), # DWORD * pdwError 
    ]
    _['GetLastSentPacketID'] = f
    f = dll.SimConnect_Open
    f.restype = HRESULT
    f.argtypes = [
        POINTER(HANDLE), # HANDLE * phSimConnect 
        LPCSTR, # LPCSTR szName 
        HWND, # HWND hWnd 
        DWORD, # DWORD UserEventWin32 
        HANDLE, # HANDLE hEventHandle 
        DWORD, # DWORD ConfigIndex 
    ]
    _['Open'] = f
    f = dll.SimConnect_CallDispatch
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DispatchProc, # DispatchProc pfcnDispatch 
        c_void_p, # void * pContext 
    ]
    _['CallDispatch'] = f
    f = dll.SimConnect_GetNextDispatch
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        POINTER(POINTER(RECV)), # SIMCONNECT_RECV ** ppData 
        POINTER(DWORD), # DWORD * pcbData 
    ]
    _['GetNextDispatch'] = f
    f = dll.SimConnect_RequestResponseTimes
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DWORD, # DWORD nCount 
        c_float_p, # float * fElapsedSeconds 
    ]
    _['RequestResponseTimes'] = f
    f = dll.SimConnect_InsertString
    f.restype = HRESULT
    f.argtypes = [
        c_char_p, # char * pDest 
        DWORD, # DWORD cbDest 
        POINTER(c_void_p), # void ** ppEnd 
        POINTER(DWORD), # DWORD * pcbStringV 
        c_char_p, # const char * pSource 
    ]
    _['InsertString'] = f
    f = dll.SimConnect_CameraSetRelative6DOF
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        c_float, # float fDeltaX 
        c_float, # float fDeltaY 
        c_float, # float fDeltaZ 
        c_float, # float fPitchDeg 
        c_float, # float fBankDeg 
        c_float, # float fHeadingDeg 
    ]
    _['CameraSetRelative6DOF'] = f
    f = dll.SimConnect_MenuAddItem
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        c_char_p, # const char * szMenuItem 
        CLIENT_EVENT_ID, # SIMCONNECT_CLIENT_EVENT_ID MenuEventID 
        DWORD, # DWORD dwData 
    ]
    _['MenuAddItem'] = f
    f = dll.SimConnect_MenuDeleteItem
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        CLIENT_EVENT_ID, # SIMCONNECT_CLIENT_EVENT_ID MenuEventID 
    ]
    _['MenuDeleteItem'] = f
    f = dll.SimConnect_MenuAddSubItem
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        CLIENT_EVENT_ID, # SIMCONNECT_CLIENT_EVENT_ID MenuEventID 
        c_char_p, # const char * szMenuItem 
        CLIENT_EVENT_ID, # SIMCONNECT_CLIENT_EVENT_ID SubMenuEventID 
        DWORD, # DWORD dwData 
    ]
    _['MenuAddSubItem'] = f
    f = dll.SimConnect_MenuDeleteSubItem
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        CLIENT_EVENT_ID, # SIMCONNECT_CLIENT_EVENT_ID MenuEventID 
        CLIENT_EVENT_ID, # const SIMCONNECT_CLIENT_EVENT_ID SubMenuEventID 
    ]
    _['MenuDeleteSubItem'] = f
    f = dll.SimConnect_RequestSystemState
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
        c_char_p, # const char * szState 
    ]
    _['RequestSystemState'] = f
    f = dll.SimConnect_SetSystemState
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        c_char_p, # const char * szState 
        DWORD, # DWORD dwInteger 
        c_float, # float fFloat 
        c_char_p, # const char * szString 
    ]
    _['SetSystemState'] = f
    f = dll.SimConnect_MapClientDataNameToID
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        c_char_p, # const char * szClientDataName 
        CLIENT_DATA_ID, # SIMCONNECT_CLIENT_DATA_ID ClientDataID 
    ]
    _['MapClientDataNameToID'] = f
    f = dll.SimConnect_CreateClientData
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        CLIENT_DATA_ID, # SIMCONNECT_CLIENT_DATA_ID ClientDataID 
        DWORD, # DWORD dwSize 
        CREATE_CLIENT_DATA_FLAG, # SIMCONNECT_CREATE_CLIENT_DATA_FLAG Flags 
    ]
    _['CreateClientData'] = f
    f = dll.SimConnect_AddToClientDataDefinition
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        CLIENT_DATA_DEFINITION_ID, # SIMCONNECT_CLIENT_DATA_DEFINITION_ID DefineID 
        DWORD, # DWORD dwOffset 
        DWORD, # DWORD dwSizeOrType 
        c_float, # float fEpsilon default {dflt}
        DWORD, # DWORD DatumID default {dflt}
    ]
    _['AddToClientDataDefinition'] = f
    f = dll.SimConnect_ClearClientDataDefinition
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        CLIENT_DATA_DEFINITION_ID, # SIMCONNECT_CLIENT_DATA_DEFINITION_ID DefineID 
    ]
    _['ClearClientDataDefinition'] = f
    f = dll.SimConnect_RequestClientData
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        CLIENT_DATA_ID, # SIMCONNECT_CLIENT_DATA_ID ClientDataID 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
        CLIENT_DATA_DEFINITION_ID, # SIMCONNECT_CLIENT_DATA_DEFINITION_ID DefineID 
        CLIENT_DATA_PERIOD, # SIMCONNECT_CLIENT_DATA_PERIOD Period default {dflt}
        CLIENT_DATA_REQUEST_FLAG, # SIMCONNECT_CLIENT_DATA_REQUEST_FLAG Flags default {dflt}
        DWORD, # DWORD origin default {dflt}
        DWORD, # DWORD interval default {dflt}
        DWORD, # DWORD limit default {dflt}
    ]
    _['RequestClientData'] = f
    f = dll.SimConnect_SetClientData
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        CLIENT_DATA_ID, # SIMCONNECT_CLIENT_DATA_ID ClientDataID 
        CLIENT_DATA_DEFINITION_ID, # SIMCONNECT_CLIENT_DATA_DEFINITION_ID DefineID 
        CLIENT_DATA_SET_FLAG, # SIMCONNECT_CLIENT_DATA_SET_FLAG Flags 
        DWORD, # DWORD dwReserved 
        DWORD, # DWORD cbUnitSize 
        c_void_p, # void * pDataSet 
    ]
    _['SetClientData'] = f
    f = dll.SimConnect_FlightLoad
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        c_char_p, # const char * szFileName 
    ]
    _['FlightLoad'] = f
    f = dll.SimConnect_FlightSave
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        c_char_p, # const char * szFileName 
        c_char_p, # const char * szTitle 
        c_char_p, # const char * szDescription 
        DWORD, # DWORD Flags 
    ]
    _['FlightSave'] = f
    f = dll.SimConnect_FlightPlanLoad
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        c_char_p, # const char * szFileName 
    ]
    _['FlightPlanLoad'] = f
    f = dll.SimConnect_Text
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        TEXT_TYPE, # SIMCONNECT_TEXT_TYPE type 
        c_float, # float fTimeSeconds 
        CLIENT_EVENT_ID, # SIMCONNECT_CLIENT_EVENT_ID EventID 
        DWORD, # DWORD cbUnitSize 
        c_void_p, # void * pDataSet 
    ]
    _['Text'] = f
    f = dll.SimConnect_SubscribeToFacilities
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        FACILITY_LIST_TYPE, # SIMCONNECT_FACILITY_LIST_TYPE type 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
    ]
    _['SubscribeToFacilities'] = f
    f = dll.SimConnect_UnsubscribeToFacilities
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        FACILITY_LIST_TYPE, # SIMCONNECT_FACILITY_LIST_TYPE type 
    ]
    _['UnsubscribeToFacilities'] = f
    f = dll.SimConnect_RequestFacilitiesList
    f.restype = HRESULT
    f.argtypes = [
        HANDLE, # HANDLE hSimConnect 
        FACILITY_LIST_TYPE, # SIMCONNECT_FACILITY_LIST_TYPE type 
        DATA_REQUEST_ID, # SIMCONNECT_DATA_REQUEST_ID RequestID 
    ]
    _['RequestFacilitiesList'] = f
    return _
