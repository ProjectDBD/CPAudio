
set( PROJECT_NAME "cpaudio_lib" )

project( ${PROJECT_NAME} )

message( STATUS "Project: ${PROJECT_NAME}" )
message( STATUS "Project directory: ${PROJECT_SOURCE_DIR}" )

set( SOURCE_DIR "${PROJECT_SOURCE_DIR}/src" )
set( INCLUDE_DIR "${SOURCE_DIR}/include" )
set( INSTALL_DIR "${CMAKE_INSTALL_PREFIX}" )

message( STATUS "Source directory: ${SOURCE_DIR}" )
message( STATUS "Include directory: ${INCLUDE_DIR}" )
message( STATUS "Install directory: ${INSTALL_DIR}" )

set( CMAKE_FIND_ROOT_PATH_MODE_PROGRAM BOTH )
set( CMAKE_FIND_ROOT_PATH_MODE_LIBRARY BOTH )
set( CMAKE_FIND_ROOT_PATH_MODE_INCLUDE BOTH )

find_package( SWIG REQUIRED )

set( CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER )
set( CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY )
set( CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY )

include( ${SWIG_USE_FILE} )

set( CMAKE_SWIG_FLAGS "-threads" )

set( CPCOMMON_INCLUDE_DIRECTORY   "${cpcommon_SOURCE_DIR}/src/include"    )
set( CAHAL_INCLUDE_DIRECTORY      "${cahal_SOURCE_DIR}/src/include"       )
set( CAHAL_TEST_INCLUDE_DIRECTORY "${cahal_tests_SOURCE_DIR}/src/include"  )
set( CSIGNAL_INCLUDE_DIRECTORY      "${csignal_SOURCE_DIR}/src/include"       )
set( CSIGNAL_TEST_INCLUDE_DIRECTORY "${csignal_tests_SOURCE_DIR}/src/include"  )

if(
    DEFINED ENV{PYTHON_INCLUDE}
    AND DEFINED ENV{PYTHON_LIB}
    AND DEFINED ENV{PYTHON_BIN}
  )
  set( PYTHON_INCLUDE $ENV{PYTHON_INCLUDE}  )
  set( PYTHON_LIB     $ENV{PYTHON_LIB}      )
  set( PYTHON_BIN     $ENV{PYTHON_BIN}      )
else()
  message (
    FATAL_ERROR
    "Environment variables PYTHON_INCLUDE, PYTHON_LIB, PYTHON_BIN must be set."
          )
endif()

if( "${CMAKE_SYSTEM_NAME}" STREQUAL "Darwin" )
  set (
        PYTHON_LIBRARIES
        "${PYTHON_LIB}/libpython.dylib"
      )
  set (
        PYTHON_BINARY
        "${PYTHON_BIN}/python"
      )
elseif( ${PLATFORM} STREQUAL "Generic" AND ${TARGET} MATCHES "^android" )
  set (
        PYTHON_LIBRARIES
        "${PYTHON_LIB}/libpython.so"
      )
  set (
        PYTHON_BINARY
        "${PYTHON_BIN}/python"
      )
elseif( ${CMAKE_SYSTEM_NAME} STREQUAL "Windows" )
  string( REPLACE "\\" "/" PYTHON_INCLUDE ${PYTHON_INCLUDE} )
  string( REPLACE "\\" "/" PYTHON_LIB ${PYTHON_LIB} )
  string( REPLACE "\\" "/" PYTHON_BIN ${PYTHON_BIN} )

  set (
        PYTHON_LIBRARIES
        "${PYTHON_LIB}/python27.lib"
      )
  set (
        PYTHON_BINARY
        "${PYTHON_BIN}/python.exe"
      )
else()
  message( FATAL_ERROR "Unsupported system: ${CMAKE_SYSTEM_NAME}" )
endif()

include_directories( ${CPCOMMON_INCLUDE_DIRECTORY} )

include_directories( ${CAHAL_INCLUDE_DIRECTORY} )
include_directories( ${CAHAL_TEST_INCLUDE_DIRECTORY} )

include_directories( ${CSIGNAL_INCLUDE_DIRECTORY} )
include_directories( ${CSIGNAL_TEST_INCLUDE_DIRECTORY} )

include_directories( ${PYTHON_INCLUDE} )

include_directories( ${CMAKE_CURRENT_SOURCE_DIR} )

message( STATUS "Python library: ${PYTHON_LIBRARIES}" )
message( STATUS "Python binary: ${PYTHON_BINARY}" )
message( STATUS "Python includes: ${PYTHON_INCLUDE}" )

set( SOURCES "${cahal_tests_SOURCE_DIR}/src/cahal_wrapper.c" )
list( APPEND SOURCES "${csignal_tests_SOURCE_DIR}/src/csignal_wrapper.c" )

set( HEADERS "${CAHAL_TEST_INCLUDE_DIRECTORY}/cahal_wrapper.h" )
list( APPEND HEADERS "${CSIGNAL_TEST_INCLUDE_DIRECTORY}/csignal_wrapper.h" )

message( STATUS "C source files found: ${SOURCES}" )
message( STATUS "C header files found: ${HEADERS}" )

swig_add_module (
  ${PROJECT_NAME}
  python
  "${PROJECT_NAME}.i"
  ${SOURCES}
  ${HEADERS}
                )

swig_link_libraries( ${PROJECT_NAME} ${PYTHON_LIBRARIES} cpcommon cahal csignal )

set( SCRIPTS "${PROJECT_SOURCE_DIR}/cpaudio.py" )
list( APPEND SCRIPTS "${PROJECT_SOURCE_DIR}/CAHALAudioFormatDescription.py" )
list( APPEND SCRIPTS "${PROJECT_SOURCE_DIR}/CAHALDevice.py" )
list( APPEND SCRIPTS "${PROJECT_SOURCE_DIR}/CAHALDeviceStream.py" )
list( APPEND SCRIPTS "${PROJECT_SOURCE_DIR}/WAVPlayer.py" )
list( APPEND SCRIPTS "${PROJECT_SOURCE_DIR}/CAHALSampleRateRange.py" )
list( APPEND SCRIPTS "${PROJECT_SOURCE_DIR}/WAVRecorder.py" )
list( APPEND SCRIPTS "${PROJECT_SOURCE_DIR}/BitStream.py" )
list( APPEND SCRIPTS "${PROJECT_SOURCE_DIR}/BitPacker.py" )
list( APPEND SCRIPTS "${PROJECT_SOURCE_DIR}/Transmitter.py" )
list( APPEND SCRIPTS "${PROJECT_SOURCE_DIR}/FilterTransmitter.py" )
list( APPEND SCRIPTS "${PROJECT_SOURCE_DIR}/SpreadSpectrumTransmitter.py" )
list( APPEND SCRIPTS "${PROJECT_SOURCE_DIR}/EnergyDetector.py" )

set( WRAPPERS "${PROJECT_BINARY_DIR}/${PROJECT_NAME}.py" )

message( STATUS "Copying scripts: ${SCRIPTS}" )
message( STATUS "Copying wrappers: ${WRAPPERS}" )

foreach( FILE_TO_COPY IN ITEMS ${SCRIPTS} )
    message( STATUS "Copying script ${FILE_TO_COPY} to ${PROJECT_BINARY_DIR}" )
    
    add_custom_command( TARGET "_${PROJECT_NAME}" PRE_BUILD
                        COMMAND ${CMAKE_COMMAND} -E copy_if_different
                        "${FILE_TO_COPY}" "${PROJECT_BINARY_DIR}" )
                        
endforeach( FILE_TO_COPY )

install(  TARGETS "_${PROJECT_NAME}" DESTINATION
          "${INSTALL_DIR}/bin/${PROJECT_NAME}" )
install(  PROGRAMS ${SCRIPTS} DESTINATION
          "${INSTALL_DIR}/bin/${PROJECT_NAME}" )
install(  FILES ${WRAPPERS} DESTINATION
          "${INSTALL_DIR}/bin/${PROJECT_NAME}" )

if( "${CMAKE_SYSTEM_NAME}" STREQUAL "Darwin" )
  find_library( CORE_FOUNDATION_FRAMEWORK CoreFoundation )
  find_library( CORE_AUDIO_FRAMEWORK CoreAudio )
  find_library( AUDIO_TOOLBOX_FRAMEWORK AudioToolbox )

  set ( EXTRA_LIBS
        ${CORE_FOUNDATION_FRAMEWORK} ${CORE_AUDIO_FRAMEWORK}
        ${AUDIO_TOOLBOX_FRAMEWORK}
      )

  message( STATUS "Framework libraries: ${EXTRA_LIBS}" )

  swig_link_libraries( ${PROJECT_NAME} ${EXTRA_LIBS} )
elseif( ${PLATFORM} STREQUAL "Generic" AND ${TARGET} MATCHES "^android" )
  find_library  (
                  OPENSLES_LIB
                  OpenSLES
                  HINTS "${CMAKE_FIND_ROOT_PATH}/usr/lib"
                )
  find_library  (
                  MATH_LIB
                  m  
                  HINTS "${CMAKE_FIND_ROOT_PATH}/usr/lib"
                )

  set (
        EXTRA_LIBS
        ${OPENSLES_LIB}
        ${MATH_LIB}
      )

  message( STATUS "Android libraries: ${EXTRA_LIBS}" )

  swig_link_libraries( ${PROJECT_NAME} ${EXTRA_LIBS} )
elseif( ${CMAKE_SYSTEM_NAME} STREQUAL "Windows" )
else()
  message( FATAL_ERROR "Unsupported system: ${CMAKE_SYSTEM_NAME}" )
endif()
