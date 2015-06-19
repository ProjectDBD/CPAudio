try:
  import threading as _threading
except ImportError:
  import dummy_threading as _threading

import argparse

from cpaudio_lib import *
from CAHALDevice import CAHALDevice
from WAVRecorder import WAVRecorder
from WAVPlayer import WAVPlayer

from SpreadSpectrumTransmitter import SpreadSpectrumTransmitter
from FilterTransmitter import FilterTransmitter
from Transmitter import Transmitter

from EnergyDetector import EnergyDetector

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
    '-fsb',
    '--firstStopBand',
    action  = 'store',
    default = 6000.0,
    type    = float,
    dest    = 'firstStopBand',
    help    = 'Frequencies under this frequency should be attenuated.'
                      )

  parser.add_argument (
    '-fpb',
    '--firstPassBand',
    action  = 'store',
    default = 7000.0,
    type    = float,
    dest    = 'firstPassBand',
    help    = 'Frequencies between this band and secondPassBand should be passed through without attenuation.'
                      )


  parser.add_argument (
    '-spb',
    '--secondPassBand',
    action  = 'store',
    default = 9000.0,
    type    = float,
    dest    = 'secondPassBand',
    help    = 'Frequencies between this band and firstPassBand should be passed through without attenuation.'
                      )

  parser.add_argument (
    '-ssb',
    '--secondStopBand',
    action  = 'store',
    default = 10000.0,
    type    = float,
    dest    = 'secondStopBand',
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
  if( args.message and args.deviceName ):
    print "Transmit info:"
    print "\tMessage:\t\t'%s'" %( args.message )
    print "\tDevice:\t\t\t%s" %( args.deviceName )
    print "\nFormat info:"
    print "\tBit depth:\t\t%d" %( args.bitDepth )
    print "\tNumber of channels:\t%d" %( args.numberOfChannels )
    print "\tSample rate:\t\t%.02f" %( args.sampleRate )
    print "\nModulation info:"
    print "\tBits per symbol:\t%d" %( args.bitsPerSymbol )
    print "\tSamples per symbol:\t%d" %( args.samplesPerSymbol )
    print "\tCarrier frequency:\t%.02f" %( args.carrierFrequency )
    print "\nFilter info:"
    print "\tFirst stopband:\t\t%.02f" %( args.firstStopBand )
    print "\tFirst passband:\t\t%.02f" %( args.firstPassBand )
    print "\tSecond passband:\t%.02f" %( args.secondPassBand )
    print "\tSecond stopband:\t%.02f" %( args.secondStopBand )
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
            args.firstStopBand,
            args.firstPassBand,
            args.secondPassBand,
            args.secondStopBand,
            args.passbandAttenuation,
            args.stopbandAttenuation,
            args.polynomialDegree,
            args.firstGenerator,
            args.secondGenerator,
            args.firstInitialValue,
            args.secondInitialValue,
            args.samplesPerChip
                                    )

        transmitter.transmit( device, args.message )
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
    print "\nFormat info:"
    print "\tBit depth:\t\t%d" %( args.bitDepth )
    print "\tNumber of channels:\t%d" %( args.numberOfChannels )
    print "\tSample rate:\t\t%.02f" %( args.sampleRate )
    print "\nModulation info:"
    print "\tBits per symbol:\t%d" %( args.bitsPerSymbol )
    print "\tSamples per symbol:\t%d" %( args.samplesPerSymbol )
    print "\tCarrier frequency:\t%.02f" %( args.carrierFrequency )
    print "\nFilter info:"
    print "\tFirst stopband:\t\t%.02f" %( args.firstStopBand )
    print "\tFirst passband:\t\t%.02f" %( args.firstPassBand )
    print "\tSecond passband:\t%.02f" %( args.secondPassBand )
    print "\tSecond stopband:\t%.02f" %( args.secondStopBand )
    print "\tPassband attenuation:\t%.02f" %( args.passbandAttenuation )
    print "\tStopband attenuation:\t%.02f" %( args.stopbandAttenuation )

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
            args.firstStopBand,
            args.firstPassBand,
            args.secondPassBand,
            args.secondStopBand,
            args.passbandAttenuation,
            args.stopbandAttenuation
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
    print "\nFormat info:"
    print "\tBit depth:\t\t%d" %( args.bitDepth )
    print "\tNumber of channels:\t%d" %( args.numberOfChannels )
    print "\tSample rate:\t\t%.02f" %( args.sampleRate )
    print "\nModulation info:"
    print "\tBits per symbol:\t%d" %( args.bitsPerSymbol )
    print "\tSamples per symbol:\t%d" %( args.samplesPerSymbol )
    print "\tCarrier frequency:\t%.02f" %( args.carrierFrequency )

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
            args.outputFileName
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
    print "Recording info:"
    print "\tDevice:\t\t\t%s" %( args.deviceName )
    print "\tDuration:\t\t%d" %( args.duration )
    print "\tBit depth:\t\t%d" %( args.bitDepth )
    print "\tNumber of channels:\t%d" %( args.numberOfChannels )
    print "\tSample rate:\t\t%.02f" %( args.sampleRate )
    print "\nEnergy detector info:"
    print "\tObservation interval:\t%.02f" %( args.observationInterval )
    print "\nFilter info:"
    print "\tFirst stopband:\t\t%.02f" %( args.firstStopBand )
    print "\tFirst passband:\t\t%.02f" %( args.firstPassBand )
    print "\tSecond passband:\t%.02f" %( args.secondPassBand )
    print "\tSecond stopband:\t%.02f" %( args.secondStopBand )
    print "\tPassband attenuation:\t%.02f" %( args.passbandAttenuation )
    print "\tStopband attenuation:\t%.02f" %( args.stopbandAttenuation )

    device = findDevice( args.deviceName )
    detector =  \
      EnergyDetector  (
        args.bitDepth,
        args.numberOfChannels,
        args.sampleRate,
        args.observationInterval,
        args.firstStopBand,
        args.firstPassBand,
        args.secondPassBand,
        args.secondStopBand,
        args.passbandAttenuation,
        args.stopbandAttenuation,
        args.outputFileName
                      )

    if( device and detector ):
      if( device.doesSupportRecording() ):
        detector.detect( device, args.duration )

        print "Done detecting."
      else:
        print "ERROR: Device '%s' does not support recording."  \
          %( args.deviceName )
    else:
      print "ERROR: Could not find device %s." %( args.deviceName )

  else:
    print "ERROR: Device name must be set for energy detecting."
def main():
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
  else:
    parser.print_help()

  terminate()

main()
