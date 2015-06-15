try:
  import threading as _threading
except ImportError:
  import dummy_threading as _threading

import argparse

from cpaudio_lib import *
from CAHALDevice import CAHALDevice
from WAVRecorder import WAVRecorder
from WAVPlayer import WAVPlayer
from Transmitter import Transmitter

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

  args = parser.parse_args()

def terminate():
  cahal_terminate()

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
            args.carrierFrequency
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
  else:
    parser.print_help()

  terminate()

main()
