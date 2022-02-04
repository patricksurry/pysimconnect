        err = self.dll.SetDataOnSimObject(
            self.hSimConnect,
            _Request.DATA_DEFINITION_ID.value,
            SIMCONNECT_SIMOBJECT_TYPE.SIMCONNECT_SIMOBJECT_TYPE_USER,
            0,
            0,
            sizeof(ctypes.c_double) * len(pyarr),
            pObjData
        )
