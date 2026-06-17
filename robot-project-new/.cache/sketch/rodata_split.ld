/* Auto-generated linker script fragment for LLEXT
 * Separates .rodata sections based on relocation status
 */

SECTIONS
{
    /* Read-only data WITH relocations - will be copied to RAM by LLEXT */
    .rodata : {
        *(.rodata._ZL12arduino_pins)
        *(.rodata._ZN12_GLOBAL__N_1L11arduino_pwmE)
        *(.rodata._ZTV13BridgeMonitorILj512EE)
        *(.rodata._ZTV15SerialTransport)
        *(.rodata._ZTV16Adafruit_MPU6050)
        *(.rodata._ZTV18RpcFunctionWrapperISt8functionIFivEEE)
        *(.rodata._ZTV18RpcFunctionWrapperISt8functionIFviEEE)
        *(.rodata._ZTV18RpcFunctionWrapperISt8functionIFvvEEE)
        *(.rodata._ZTV21Adafruit_MPU6050_Gyro)
        *(.rodata._ZTV21Adafruit_MPU6050_Temp)
        *(.rodata._ZTV30Adafruit_MPU6050_Accelerometer)
        *(.rodata._ZTVN7arduino12ZephyrSerialE)
        *(.rodata._ZTVN7arduino9ZephyrI2CE)
        *(.rodata._ZTVN7arduino9ZephyrSPIE)
    }

    /* Read-only data WITHOUT relocations - kept in flash by LLEXT */
    .llext.rodata.noreloc : {
        *(.rodata._Z10turn_rightv.str1.1)
        *(.rodata._Z11stop_motorsv.str1.1)
        *(.rodata._Z12move_forwardv.str1.1)
        *(.rodata._Z13move_backwardv.str1.1)
        *(.rodata._Z13send_IMU_datav.str1.1)
        *(.rodata._Z13setServoSpeedi.str1.1)
        *(.rodata._Z16turn_left_slowlyv.str1.1)
        *(.rodata._Z17turn_right_slowlyv.str1.1)
        *(.rodata._Z9turn_leftv.str1.1)
        *(.rodata._ZN10RpcDecoderILj1024EE12get_responseIN7arduino7msgpack6object5nil_tEEEbjRT_R8RpcError.str1.1)
        *(.rodata._ZN10RpcDecoderILj1024EE12get_responseIbEEbjRT_R8RpcError.str1.1)
        *(.rodata._ZN11BridgeClass11update_safeEv.str1.1)
        *(.rodata._ZN11BridgeClass5beginEm.str1.1)
        *(.rodata._ZN11BridgeClass7provideIRFivEEEbRKN7arduino6StringEOT_.isra.0.str1.1)
        *(.rodata._ZN12_GLOBAL__N_1L16arduino_pwm_pinsE)
        *(.rodata._ZN13BridgeMonitorILj512EE5_readEj.str1.1)
        *(.rodata._ZN13BridgeMonitorILj512EE5beginEmt.isra.0.str1.1)
        *(.rodata._ZN13BridgeMonitorILj512EE5writeEPKhj.str1.1)
        *(.rodata._ZN13BridgeMonitorILj512EEcvbEv.str1.1)
        *(.rodata._ZN18RpcFunctionWrapperISt8functionIFviEEEclERN7arduino7msgpack8UnpackerERNS5_6PackerE.str1.1)
        *(.rodata._ZN18RpcFunctionWrapperISt8functionIFvvEEEclERN7arduino7msgpack8UnpackerERNS5_6PackerE.str1.1)
        *(.rodata._ZN21Adafruit_MPU6050_Gyro9getSensorEP8sensor_t.str1.1)
        *(.rodata._ZN21Adafruit_MPU6050_Temp9getSensorEP8sensor_t.str1.1)
        *(.rodata._ZN30Adafruit_MPU6050_Accelerometer9getSensorEP8sensor_t.str1.1)
        *(.rodata._ZN7RpcCallIJEE6resultIbEEbRT_.part.0.str1.1)
        *(.rodata._ZN7RpcCallIJEEC2ERKN7arduino6StringEP9RPCClientP7k_mutexS8_.str1.1)
        *(.rodata._ZN7arduino7msgpack6object3extC2EaPKhj.str1.1)
        *(.rodata._ZN8RpcErrorC2Ev.str1.1)
        *(.rodata._ZNSt6vectorIjSaIjEE17_M_realloc_insertIJRjEEEvN9__gnu_cxx17__normal_iteratorIPjS1_EEDpOT_.str1.1)
        *(.rodata.dtostrf.str1.1)
        *(.rodata.loop.str1.1)
        *(.rodata.setup.str1.1)
        *(.rodata.str1.1)
    }

    /* Merge all .rel.rodata.* sections into .rel.rodata */
    .rel.rodata : {
        *(.rel.rodata)
        *(.rel.rodata.*)
    }

    /* Merge all .rela.rodata.* sections into .rela.rodata */
    .rela.rodata : {
        *(.rela.rodata)
        *(.rela.rodata.*)
    }

}
