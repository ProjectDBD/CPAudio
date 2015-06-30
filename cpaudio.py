try:
  import threading as _threading
except ImportError:
  import dummy_threading as _threading

import math
import time
import argparse

from cpaudio_lib import *
from CAHALDevice import CAHALDevice
from WAVRecorder import WAVRecorder
from WAVPlayer import WAVPlayer

from SpreadSpectrumTransmitter import SpreadSpectrumTransmitter
from FilterTransmitter import FilterTransmitter
from Transmitter import Transmitter

from EnergyDetector import EnergyDetector
from Receiver import Receiver

parser  = None
args    = None
devices = []

def setup():
  global parser
  global args 
  global devices

  python_cahal_initialize()
  csignal_initialize()

  parser = \
    argparse.ArgumentParser (
      description='Interact with the platform\'s audio hardware'
                            )
  parser.add_argument (               \
    '-l',                             \
    '--list-devices',                 \
    action  = 'store_true',           \
    dest    = 'list_devices',         \
    help    = 'List all audio devices'\
                      )

  parser.add_argument (                       \
    '-li',                                    \
    '--input-devices',                        \
    action  = 'store_true',                   \
    dest    = 'list_input',                   \
    help    = 'List all input audio devices'  \
                      )

  parser.add_argument (                       \
    '-lo',                                    \
    '--output-devices',                       \
    action  = 'store_true',                   \
    dest    = 'list_output',                  \
    help    = 'List all output audio devices' \
                      )

  parser.add_argument (                         \
    '-ld',                                      \
    '--list-device',                            \
    action  = 'store_true',                     \
    dest    = 'list_device',                    \
    help    = 'List the details about a device.'\
                      )

  parser.add_argument (
    '-sc',
    '-synchronizationChips',
    action  = 'store',
    default = 4 * ( 2 ** 7 - 1 ),
    type    = int,
    dest    = 'synchronizationChips',
    help    = 'The number of synchronization chips to transmit.'
                      )

  parser.add_argument (                 \
    '-p',                               \
    '--playback',                       \
    action  = 'store_true',             \
    dest    = 'playback',               \
    help    = 'Playback audio samples.' \
                      )

  parser.add_argument (                                       \
    '-f',                                                     \
    '--file',                                                 \
    action  = 'store',                                        \
    dest    = 'playbackFile',                                 \
    help    = 'Audio file to playback. Required by playback.' \
                      )

  parser.add_argument (
    '-F',
    '--filter',
    action  = 'store_true',
    dest    = 'filter',
    help    = 'Flag indicating to apply a filter.'
                      )

  parser.add_argument (
    '-w',
    '--write-output',
    action  = 'store_true',
    dest    = 'writeOutput',
    help    = 'Flag indicating to save output to file.'
                      )

  parser.add_argument (
    '-t',
    '--transmit',
    action  = 'store_true',
    dest    = 'transmit',
    help    = 'Transmit a message using audio signals.'
                      )

  parser.add_argument (
    '-m',
    '--message',
    action  = 'store',
    dest    = 'message',
    help    = 'The message to transmit. Required for transmit.'
                      )

  parser.add_argument (               \
    '-r',                             \
    '--record',                       \
    action  = 'store_true',           \
    dest    = 'record',               \
    help    = 'Record audio samples'  \
                      )

  parser.add_argument (
    '-nts',
    '--numberOfTrainingSymbols',
    action  = 'store',
    default = 13,
    type    = int,
    dest    = 'numberOfTrainingSymbols',
    help    = 'The number of symbols to use to train the receiver'
                      )

  parser.add_argument (
    '-R',
    '--receive',
    action  = 'store_true',
    dest    = 'receive',
    help    = 'Receive a transmitted signal'
                      )

  parser.add_argument (
    '-i',
    '--deviceName',
    action  = 'store',
    dest    = 'deviceName',
    help    = 'The name of the device to playback/record with.'
                      )

  parser.add_argument (   \
    '-d',                 \
    '--duration',         \
    action  = 'store',    \
    default = 5,          \
    type    = int,        \
    dest    = 'duration', \
    help    = 'Duration to record/playback audio samples for (seconds)' \
                      )

  parser.add_argument (           \
    '-n',                         \
    '--numberOfChannels',         \
    action  = 'store',            \
    default = 1,                  \
    type    = int,                \
    dest    = 'numberOfChannels', \
    help    = 'The number of channels to record on. Required for record.' \
                      )

  parser.add_argument (   \
    '-b',                 \
    '--bitDepth',         \
    action  = 'store',    \
    default = 16,         \
    type    = int,        \
    dest    = 'bitDepth', \
    help    = 'The number of bits per sample represented in the format (i.e., quantization level). Required for record.'  \
                      )

  parser.add_argument (
    '-bps',
    '--bitsPerSymbol',
    action  = 'store',
    default = 1,
    type    = int,
    dest    = 'bitsPerSymbol',
    help    = 'The number of bits per symbol. Constellation size is 2^bitsPerSymbol'
                      ) 

  parser.add_argument (
    '-sps',
    '--samplesPerSymbol',
    action  = 'store',
    default = 100,
    type    = int,
    dest    = 'samplesPerSymbol',
    help    = 'The number of samples per symbol.'
                      )

  parser.add_argument (
    '-c',
    '--carrierFrequency',
    action  = 'store',
    default = 8000.0,
    type    = float,
    dest    = 'carrierFrequency',
    help    = 'The carrier frequency used to modulate symbols'
                      )

  parser.add_argument (
    '-ft',
    '--filterTransmit',
    action  = 'store_true',
    dest    = 'filterTransmit',
    help    = 'Transmit a message using filtered audio signals.'
                      )

  parser.add_argument (
    '-wsb1',
    '--widebandFirstStopband',
    action  = 'store',
    default = 6000.0,
    type    = float,
    dest    = 'widebandFirstStopband',
    help    = 'Frequencies under this frequency should be attenuated.'
                      )

  parser.add_argument (
    '-wpb1',
    '--widebandFirstPassband',
    action  = 'store',
    default = 7000.0,
    type    = float,
    dest    = 'widebandFirstPassband',
    help    = 'Frequencies between this band and widebandSecondPassband should be passed through without attenuation.'
                      )

  parser.add_argument (
    '-wpb2',
    '--widebandSecondPassband',
    action  = 'store',
    default = 9000.0,
    type    = float,
    dest    = 'widebandSecondPassband',
    help    = 'Frequencies between this band and widebandFirstPassband should be passed through without attenuation.'
                      )

  parser.add_argument (
    '-wsb2',
    '--widebandSecondStopband',
    action  = 'store',
    default = 10000.0,
    type    = float,
    dest    = 'widebandSecondStopband',
    help    = 'Frequecies above this frequency should be attenuated.'
                      )

  parser.add_argument (
    '-nsb1',
    '--narrowbandFirstStopband',
    action  = 'store',
    default = 6900.0,
    type    = float,
    dest    = 'narrowbandFirstStopband',
    help    = 'Frequencies under this frequency should be attenuated.'
                      )

  parser.add_argument (
    '-npb1',
    '--narrowbandFirstPassband',
    action  = 'store',
    default = 7900.0,
    type    = float,
    dest    = 'narrowbandFirstPassband',
    help    = 'Frequencies between this band and narrowbandSecondPassband should be passed through without attenuation.'
                      )

  parser.add_argument (
    '-npb2',
    '--narrowbandSecondPassband',
    action  = 'store',
    default = 8100.0,
    type    = float,
    dest    = 'narrowbandSecondPassband',
    help    = 'Frequencies between this band and narrowbandFirstPassband should be passed through without attenuation.'
                      )

  parser.add_argument (
    '-nsb2',
    '--narrowbandSecondStopband',
    action  = 'store',
    default = 9100.0,
    type    = float,
    dest    = 'narrowbandSecondStopband',
    help    = 'Frequecies above this frequency should be attenuated.'
                      )
  parser.add_argument (
    '-pa',
    '--passbandAttenuation',
    action  = 'store',
    default = 0.1,
    type    = float,
    dest    = 'passbandAttenuation',
    help    = 'The allowable attenuation in the passband (amount of ripple)'
                      )

  parser.add_argument (
    '-sa',
    '--stopbandAttenuation',
    action  = 'store',
    default = 80.0,
    type    = float,
    dest    = 'stopbandAttenuation',
    help    = 'The amount to attenuate frequencies in the stopband by.'
                      )

  parser.add_argument (     \
    '-s',                   \
    '--sampleRate',         \
    action  = 'store',      \
    default = 44100.0,      \
    type    = float,        \
    dest    = 'sampleRate', \
    help    = 'The sample rate to record at. Required for record.'  \
                      )

  parser.add_argument (         \
    '-o',                       \
    '--output',                 \
    action  = 'store',          \
    default = 'out.wav',        \
    dest    = 'outputFileName', \
    help    = 'The file to write recorded samples to.'  \
                      )

  parser.add_argument (                                                 \
    '-v',                                                               \
    '--verbosity',                                                      \
    choices = [ 'trace', 'debug', 'info', 'warning', 'error', 'none' ], \
    action  = 'store',                                                  \
    default = 'error',                                                  \
    dest    = 'verbosity',                                              \
    help    = 'Verbosity level'                                         \
                      )

  parser.add_argument (
    '-pd',
    '--polynomialDegree',
    action  = 'store',
    default = 7,
    type    = int,
    dest    = 'polynomialDegree',
    help    = 'The degree of the spreading code generator polynomial.'
                      )
 
  parser.add_argument (
    '-sst',
    '--spreadSpectrumTransmit',
    action  = 'store_true',
    dest    = 'spreadSpectrumTransmit',
    help    = 'Transmit a message using spread spectrum audio signals.'
                      )

  parser.add_argument (
    '-fg',
    '--firstGenerator',
    action  = 'store',
    default = 0x12000000,
    type    = int,
    dest    = 'firstGenerator',
    help    = 'The first generator polynomial to use for gold code spreading.'
                      )

  parser.add_argument (
    '-sg',
    '--secondGenerator',
    action  = 'store',
    default = 0x1E000000,
    type    = int,
    dest    = 'secondGenerator',
    help    = 'The second generator polynomial to use for gold code spreading.'
                      )

  parser.add_argument (
    '-fiv',
    '--firstInitialValue',
    action  = 'store',
    default = 0x4000000,
    type    = int,
    dest    = 'firstInitialValue',
    help    = 'The first initial value to feed into the gold code sequence.'
                      )

  parser.add_argument (
    '-siv',
    '--secondInitialValue',
    action  = 'store',
    default = 0x4000000,
    type    = int,
    dest    = 'secondInitialValue',
    help    = 'The second initial value to feed into the gold code sequence.'
                      )

  parser.add_argument (
    '-spc',
    '--samplesPerChip',
    action  = 'store',
    default = 10,
    type    = int,
    dest    = 'samplesPerChip',
    help    = 'The number of samples per chip.'
                      )

  parser.add_argument (
    '-e',
    '--energyDetector',
    action  = 'store_true',
    dest    = 'energyDetector',
    help    = 'Run the energy detector to detect communications.'
                      )

  parser.add_argument (
    '-oi',
    '--observationInterval',
    action  = 'store',
    default = 0.1,
    type    = float,
    dest    = 'observationInterval',
    help    = 'The observation interval to use while in energy detector mode.'
                      )

  args = parser.parse_args()

def terminate():
  cahal_terminate()
  csignal_terminate()

def initialize_debug_info():
  global args

  if( args.verbosity == 'trace' ):
    cpc_log_set_log_level( CPC_LOG_LEVEL_TRACE )
  elif( args.verbosity == 'debug' ):
    cpc_log_set_log_level( CPC_LOG_LEVEL_DEBUG )
  elif( args.verbosity == 'info' ):
    cpc_log_set_log_level( CPC_LOG_LEVEL_INFO )
  elif( args.verbosity == 'warning' ):
    cpc_log_set_log_level( CPC_LOG_LEVEL_WARNING )
  elif( args.verbosity == 'error' ):
    cpc_log_set_log_level( CPC_LOG_LEVEL_ERROR )
  elif( args.verbosity == 'none' ):
    cpc_log_set_log_level( CPC_LOG_LEVEL_NO_LOGGING )
  else:
    args.print_usage()

def catalogueDevices():
  global devices

  device_list = cahal_get_device_list()
  index       = 0                                                             
  device      = cahal_device_list_get( device_list, index )       
                                                                                
  while( device ):
    devices.append( CAHALDevice( device ) )
  
    index   += 1                                                              
    device  = cahal_device_list_get( device_list, index )

def listDevices( filter ):
  global devices

  for device in devices:
    if( -1 == filter ):
      device.printMe()
    elif  (
      filter == CAHAL_DEVICE_OUTPUT_STREAM
      and device.doesSupportPlayback()
          ):
      device.printMe()
    elif  (
      filter == CAHAL_DEVICE_INPUT_STREAM
      and device.doesSupportRecording()
          ):
      device.printMe()

def findDevice( deviceName ):
  global devices

  for device in devices:
    if( device.name == deviceName ):
      return( device )

  return( None )

def showDeviceDetails():
  if( args.deviceName ):
    device = findDevice( args.deviceName )

    if( device ):
      device.printMe()
    else:
      print "ERROR: Device %s could not be found." %( args.deviceName )
  else:
    print "ERROR: Device name must be set for list-device command."

def playback():
  if( args.deviceName and args.playbackFile ):
    print "Playback info:"
    print "\tDevice:\t\t%s" %( args.deviceName )
    print "\tFile:\t\t%s" %( args.playbackFile )
    print "\tDuration:\t%d" %( args.duration )

    device = findDevice( args.deviceName )
    player = WAVPlayer( args.playbackFile )

    if( device and player ):
      if( device.doesSupportPlayback() ):
        player.play( device, args.duration )
      else:
        print "ERROR: Device '%s' does not support playback." \
          %( args.deviceName )
    else:
      print "ERROR: Could not find device %s." %( args.deviceName )
  else:
    print "ERROR: Device name and input file must be set for playback."

def spreadSpectrumTransmit():
  if( args.deviceName ):
    print "Transmit info:"
    print "\tDevice:\t\t\t%s" %( args.deviceName )
    print "\tOutput signal:\t\t%s" %( "Yes" if( args.writeOutput ) else "No" )
    print "\nFormat info:"
    print "\tBit depth:\t\t%d" %( args.bitDepth )
    print "\tNumber of channels:\t%d" %( args.numberOfChannels )
    print "\tSample rate:\t\t%.02f" %( args.sampleRate )
    print "\nModulation info:"
    print "\tBits per symbol:\t%d" %( args.bitsPerSymbol )
    print "\tSamples per symbol:\t%d" %( args.samplesPerSymbol )
    print "\tCarrier frequency:\t%.02f" %( args.carrierFrequency )
    print "\tSynchronization chips:\t%d" %( args.synchronizationChips )

    if( args.filter ):
      print "\nFilter info:"
      print "\tFirst stopband:\t\t%.02f" %( args.widebandFirstStopband )
      print "\tFirst passband:\t\t%.02f" %( args.widebandFirstPassband )
      print "\tSecond passband:\t%.02f" %( args.widebandSecondPassband )
      print "\tSecond stopband:\t%.02f" %( args.widebandSecondStopband )
      print "\tPassband attenuation:\t%.02f" %( args.passbandAttenuation )
      print "\tStopband attenuation:\t%.02f" %( args.stopbandAttenuation )

    print "\nSpread spectrum info:"
    print "\tSamples per chip:\t%d" %( args.samplesPerChip )
    print "\tPolynomial degree:\t%d" %( args.polynomialDegree )
    print "\tFirst generator:\t0x%x" %( args.firstGenerator )
    print "\tSecond generator:\t0x%x" %( args.secondGenerator )
    print "\tFirst initial value:\t0x%x" %( args.firstInitialValue )
    print "\tSecond initial value:\t0x%x" %( args.secondInitialValue )

    device = findDevice( args.deviceName )

    if( device ):
      if( device.doesSupportPlayback() ):
        transmitter = \
          SpreadSpectrumTransmitter (
            args.bitDepth,
            args.numberOfChannels,
            args.sampleRate,
            args.bitsPerSymbol,
            args.samplesPerSymbol,
            args.carrierFrequency,
            args.outputFileName,
            args.widebandFirstStopband,
            args.widebandFirstPassband,
            args.widebandSecondPassband,
            args.widebandSecondStopband,
            args.passbandAttenuation,
            args.stopbandAttenuation,
            args.polynomialDegree,
            args.firstGenerator,
            args.secondGenerator,
            args.firstInitialValue,
            args.secondInitialValue,
            args.samplesPerChip,
            args.filter,
            args.writeOutput
                                    )

        mesage = ''

        if( args.synchronizationChips ):
          numChipSamples            = \
            args.synchronizationChips * args.samplesPerChip
          numSynchronizationSymbols = \
            math.ceil( numChipSamples * 1.0 / args.samplesPerSymbol * 1.0 )
          numSymbolsPerByte         = 8 / args.bitsPerSymbol
          numBytes                  = \
            int (
              math.ceil (
                numSynchronizationSymbols * 1.0 / numSymbolsPerByte * 1.0
                        )
                )
        
          print "Chip Sample: %d" %( numChipSamples )
          print "Synchronization symbols: %d" %( numSynchronizationSymbols )
          print "Symbols per Byte: %d" %( numSymbolsPerByte )
          print "Bytes: %d" %( numBytes )

          message = '\x00' * numBytes

        if( args.message ):
          message = message + args.message

        print "\nMessage info:"
        print "\tMessage:\t\t%s" \
          %( args.message if( args.message ) else '(None)' )
        print "\tMessage length:\t\t%d" \
          %( len( args.message ) if( args.message ) else 0 )
        print "\tPadded message length:\t%d" %( len( message ) )

        transmitter.transmit( device, message )
      else:
        print "ERROR: Device %s does not support playback." \
          %( args.deviceName )
    else:
      print "ERROR: Could not find device %s." %( args.deviceName )
  else:
    print "ERROR: Message and device name must be set for transmit."

def filterTransmit():
  if( args.message and args.deviceName ):
    print "Transmit info:"
    print "\tMessage:\t\t'%s'" %( args.message )
    print "\tDevice:\t\t\t%s" %( args.deviceName )
    print "\tOutput signal:\t\t%s" %( "Yes" if( args.writeOutput ) else "No" )
    print "\nFormat info:"
    print "\tBit depth:\t\t%d" %( args.bitDepth )
    print "\tNumber of channels:\t%d" %( args.numberOfChannels )
    print "\tSample rate:\t\t%.02f" %( args.sampleRate )
    print "\nModulation info:"
    print "\tBits per symbol:\t%d" %( args.bitsPerSymbol )
    print "\tSamples per symbol:\t%d" %( args.samplesPerSymbol )
    print "\tCarrier frequency:\t%.02f" %( args.carrierFrequency )
    print "\nFilter info:"
    print "\tFirst stopband:\t\t%.02f" %( args.widebandFirstStopband )
    print "\tFirst passband:\t\t%.02f" %( args.widebandFirstPassband )
    print "\tSecond passband:\t%.02f" %( args.widebandSecondPassband )
    print "\tSecond stopband:\t%.02f" %( args.widebandSecondStopband )
    print "\tPassband attenuation:\t%.02f" %( args.passbandAttenuation )
    print "\tStopband attenuation:\t%.02f" %( args.stopbandAttenuation )

    if( args.filter ):
      print "WARN: Filter flag set for filterTransmit. Redundant option set."

    if( args.writeOutput ):
      print "\nOutput info:"
      print "\tFile name:\t\t%s" %( args.outputFileName )

    device = findDevice( args.deviceName )

    if( device ):
      if( device.doesSupportPlayback() ):
        transmitter = \
          FilterTransmitter (
            args.bitDepth,
            args.numberOfChannels,
            args.sampleRate,
            args.bitsPerSymbol,
            args.samplesPerSymbol,
            args.carrierFrequency,
            args.outputFileName,
            args.widebandFirstStopband,
            args.widebandFirstPassband,
            args.widebandSecondPassband,
            args.widebandSecondStopband,
            args.passbandAttenuation,
            args.stopbandAttenuation,
            args.writeOutput
                      )

        transmitter.transmit( device, args.message )
      else:
        print "ERROR: Device %s does not support playback." \
          %( args.deviceName )
    else:
      print "ERROR: Could not find device %s." %( args.deviceName )
  else:
    print "ERROR: Message and device name must be set for transmit."

def transmit():
  if( args.message and args.deviceName ):
    print "Transmit info:"
    print "\tMessage:\t\t'%s'" %( args.message )
    print "\tDevice:\t\t\t%s" %( args.deviceName )
    print "\tOutput signal:\t\t%s" %( "Yes" if( args.writeOutput ) else "No" )
    print "\nFormat info:"
    print "\tBit depth:\t\t%d" %( args.bitDepth )
    print "\tNumber of channels:\t%d" %( args.numberOfChannels )
    print "\tSample rate:\t\t%.02f" %( args.sampleRate )
    print "\nModulation info:"
    print "\tBits per symbol:\t%d" %( args.bitsPerSymbol )
    print "\tSamples per symbol:\t%d" %( args.samplesPerSymbol )
    print "\tCarrier frequency:\t%.02f" %( args.carrierFrequency )

    if( args.writeOutput ):
      print "\nOutput info:"
      print "\tFile name:\t\t%s" %( args.outputFileName )

    device = findDevice( args.deviceName )

    if( device ):
      if( device.doesSupportPlayback() ):
        transmitter = \
          Transmitter (
            args.bitDepth,
            args.numberOfChannels,
            args.sampleRate,
            args.bitsPerSymbol,
            args.samplesPerSymbol,
            args.carrierFrequency,
            args.outputFileName,
            args.writeOutput
                      )

        transmitter.transmit( device, args.message )
      else:
        print "ERROR: Device %s does not support playback." \
          %( args.deviceName )
    else:
      print "ERROR: Could not find device %s." %( args.deviceName )
  else:
    print "ERROR: Message and device name must be set for transmit."

def record():
  if( args.deviceName ):
    print "Recording info:"
    print "\tDevice:\t\t\t%s" %( args.deviceName )
    print "\tOutput:\t\t\t%s" %( args.outputFileName )
    print "\tDuration:\t\t%d" %( args.duration )
    print "\tBit depth:\t\t%d" %( args.bitDepth )
    print "\tNumber of channels:\t%d" %( args.numberOfChannels )
    print "\tSample rate:\t\t%.02f" %( args.sampleRate )

    device    = findDevice( args.deviceName )
    recorder  =                 \
      WAVRecorder (             \
        args.numberOfChannels,  \
        args.bitDepth,          \
        args.sampleRate         \
                  )

    if( device and recorder ):
      if( device.doesSupportRecording() ):
        recorder.record( device, args.duration, args.outputFileName )

        print "Done recording."
      else:
        print "ERROR: Device '%s' does not support recording."  \
          %( args.deviceName )
    else:
      print "ERROR: Could not find device %s." %( args.deviceName )

  else:
    print "ERROR: Device name must be set for recording."

def energyDetector():
  if( args.deviceName ):
    print "Detector info:"
    print "\tDevice:\t\t\t%s" %( args.deviceName )
    print "\tDuration:\t\t%d" %( args.duration )
    print "\tBit depth:\t\t%d" %( args.bitDepth )
    print "\tNumber of channels:\t%d" %( args.numberOfChannels )
    print "\tSample rate:\t\t%.02f" %( args.sampleRate )
    print "\tOutput signal:\t\t%s" %( "Yes" if( args.writeOutput ) else "No" )
    print "\nEnergy detector info:"
    print "\tObservation interval:\t%.02f" %( args.observationInterval )
    print "\tFilter signal:\t\t%s" %( "Yes" if( args.filter ) else "No" )

    if( args.filter ):
      print "\nFilter info:"
      print "\tFirst stopband:\t\t%.02f" %( args.widebandFirstStopband )
      print "\tFirst passband:\t\t%.02f" %( args.widebandFirstPassband )
      print "\tSecond passband:\t%.02f" %( args.widebandSecondPassband )
      print "\tSecond stopband:\t%.02f" %( args.widebandSecondStopband )
      print "\tPassband attenuation:\t%.02f" %( args.passbandAttenuation )
      print "\tStopband attenuation:\t%.02f" %( args.stopbandAttenuation )

    if( args.writeOutput ):
      print "\nOutput info:"
      print "\tFile name:\t\t%s" %( args.outputFileName )

    device = findDevice( args.deviceName )
    detector =  \
      EnergyDetector  (
        args.bitDepth,
        args.numberOfChannels,
        args.sampleRate,
        args.observationInterval,
        args.widebandFirstStopband,
        args.widebandFirstPassband,
        args.widebandSecondPassband,
        args.widebandSecondStopband,
        args.passbandAttenuation,
        args.stopbandAttenuation,
        args.outputFileName,
        args.filter,
        args.writeOutput,
        args.duration
                     )

    if( device and detector ):
      if( device.doesSupportRecording() ):
        detector.record( device )

        print "Done detecting."
      else:
        print "ERROR: Device '%s' does not support recording."  \
          %( args.deviceName )
    else:
      print "ERROR: Could not find device %s." %( args.deviceName )

  else:
    print "ERROR: Device name must be set for energy detecting."

def receive():
  if( args.deviceName ):
    print "Receiver info:"
    print "\tDevice:\t\t\t\t%s" %( args.deviceName )
    print "\tDuration:\t\t\t%d" %( args.duration )
    print "\tNumber of training symbols:\t%d" %( args.numberOfTrainingSymbols )
    print "\nFormat info:"
    print "\tBit depth:\t\t\t%d" %( args.bitDepth )
    print "\tNumber of channels:\t\t%d" %( args.numberOfChannels )
    print "\tSample rate:\t\t\t%.02f" %( args.sampleRate )
    print "\nModulation info:"
    print "\tBits per symbol:\t\t%d" %( args.bitsPerSymbol )
    print "\tSamples per symbol:\t\t%d" %( args.samplesPerSymbol )
    print "\tCarrier frequency:\\tt%.02f" %( args.carrierFrequency )
    print "\tSample rate:\t\t\t%.02f" %( args.sampleRate )
    print "\tOutput signal:\t\t\t%s" %( "Yes" if( args.writeOutput ) else "No" )
    print "\nWideband filter info:"
    print "\tFirst stopband:\t\t\t%.02f" %( args.widebandFirstStopband )
    print "\tFirst passband:\t\t\t%.02f" %( args.widebandFirstPassband )
    print "\tSecond passband:\t\t%.02f" %( args.widebandSecondPassband )
    print "\tSecond stopband:\t\t%.02f" %( args.widebandSecondStopband )
    print "\nNarrowband filter info:"
    print "\tFirst stopband:\t\t\t%.02f" %( args.narrowbandFirstStopband )
    print "\tFirst passband:\t\t\t%.02f" %( args.narrowbandFirstPassband )
    print "\tSecond passband:\t\t%.02f" %( args.narrowbandSecondPassband )
    print "\tSecond stopband:\t\t%.02f" %( args.narrowbandSecondStopband )
    print "\nFilter info:"
    print "\tPassband attenuation:\t\t%.02f" %( args.passbandAttenuation )
    print "\tStopband attenuation:\t\t%.02f" %( args.stopbandAttenuation )
    print "\nSpread spectrum info:"
    print "\tSamples per chip:\t\t%d" %( args.samplesPerChip )
    print "\tPolynomial degree:\t\t%d" %( args.polynomialDegree )
    print "\tFirst generator:\t\t0x%x" %( args.firstGenerator )
    print "\tSecond generator:\t\t0x%x" %( args.secondGenerator )
    print "\tFirst initial value:\t\t0x%x" %( args.firstInitialValue )
    print "\tSecond initial value:\t\t0x%x" %( args.secondInitialValue )

    if( args.writeOutput ):
      print "\nOutput info:"
      print "\tFile name:\t\t\t%s" %( args.outputFileName )

    device = findDevice( args.deviceName )
    receiver =  \
      Receiver  (
        args.bitDepth,
        args.numberOfChannels,
        args.sampleRate,
        args.bitsPerSymbol,
        args.samplesPerSymbol,
        args.carrierFrequency,
        args.widebandFirstStopband,
        args.widebandFirstPassband,
        args.widebandSecondPassband,
        args.widebandSecondStopband,
        args.narrowbandFirstStopband,
        args.narrowbandFirstPassband,
        args.narrowbandSecondPassband,
        args.narrowbandSecondStopband,
        args.passbandAttenuation,
        args.stopbandAttenuation,
        args.polynomialDegree,
        args.firstGenerator,
        args.secondGenerator,
        args.firstInitialValue,
        args.secondInitialValue,
        args.samplesPerChip,
        args.numberOfTrainingSymbols,
        args.outputFileName,
        args.writeOutput,
        args.duration
                )

    if( device and receiver ):
      if( device.doesSupportRecording() ):
        receiver.record( device )

        print "Done receiving."
      else:
        print "ERROR: Device '%s' does not support recording."  \
          %( args.deviceName )
    else:
      print "ERROR: Could not find device %s." %( args.deviceName )
  else:
    print "ERROR: Device name must be set for energy detecting."

def main():
  startTime = time.time()

  setup()

  initialize_debug_info()

  devices = catalogueDevices()

  if( args.list_devices ):
    listDevices( -1 )
  elif( args.list_input ):
    listDevices( CAHAL_DEVICE_INPUT_STREAM )
  elif( args.list_output ):
    listDevices( CAHAL_DEVICE_OUTPUT_STREAM )
  elif( args.list_device ):
    showDeviceDetails() 
  elif( args.record ):
    record()
  elif( args.playback ):
    playback()
  elif( args.transmit ):
    transmit()
  elif( args.filterTransmit ):
    filterTransmit()
  elif( args.spreadSpectrumTransmit ):
    spreadSpectrumTransmit()
  elif( args.energyDetector ):
    energyDetector()
  elif( args.receive ):
    receive()
  else:
    parser.print_help()

  terminate()

  duration = time.time() - startTime

  print "Ran for %.04f seconds." %( duration )

main()
