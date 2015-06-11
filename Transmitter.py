from cpaudio_lib import *

class Transmitter:
  def __init__  (
    self, bitDepth, numberOfChannels, sampleRate, bitsPerSymbol,
    samplesPerSymbol, carrierFrequency
                ):

    self.bitDepth         = bitDepth
    self.numberOfChannels = numberOfChannels
    self.sampleRate       = sampleRate
    self.bitsPerSymbol    = bitsPerSymbol
    self.samplesPerSymbol = samplesPerSymbol
    self.carrierFrequency = carrierFrequency

  def transmit( self, device, message ):
    if  (                               \
        device.hasAppropriateStream (   \
            CAHAL_DEVICE_OUTPUT_STREAM, \
            self.numberOfChannels,      \
            self.bitDepth,              \
            self.sampleRate             \
                                    )   \
        ):
      print "Preparing signal for message: %s." %( message )

      signal = self.prepareSignal( message )

      if( signal ):
        self.sendSignal( device, signal )
      else:
        print "ERROR: Could not prepare signal."
    else:
      print "ERROR: Could not find an appropriate stream."

  def readSamples( self, in_device, in_buffer_length ):                                    
    print "Reading samples."

    print self.signal

  def sendSignal( self, device, signal ):
    flags =                                   \
      CAHAL_AUDIO_FORMAT_FLAGISSIGNEDINTEGER  \
      | CAHAL_AUDIO_FORMAT_FLAGISPACKED

    self.signal = signal

    if  (
      start_playback  (               \
        device.struct,                \
        CAHAL_AUDIO_FORMAT_LINEARPCM, \
        self.numberOfChannels,        \
        self.sampleRate,              \
        self.bitDepth,                \
        self.readSamples,             \
        flags                         \
                      )               \
        ):
      print "Starting transmit..."

      #cahal_sleep( duration )
    
      cahal_stop_playback()

      print "Stopping transmit..."
    else:
      print "ERROR: Could not start playing."

    del self.signal

  def prepareSignal( self, message ):
    constellationSize = 2 ** self.bitsPerSymbol
    symbolTracker     = python_initialize_symbol_tracker( message )
    symbol            = \
      python_get_symbol( symbolTracker, self.bitsPerSymbol ) 
    basebandAmplitude = 2 ** ( self.bitDepth - 1 ) - 1

    signal = [ [] for index in range( self.numberOfChannels ) ]
  
    while( symbol != None ):
      signalComponents = python_modulate_symbol (
        symbol,
        constellationSize,
        int( self.sampleRate ),
        self.samplesPerSymbol,
        basebandAmplitude,
        self.carrierFrequency
                                                )

      signalPart = []

      for index in range( self.samplesPerSymbol ):
        signalPart.append (
          int (
            signalComponents[ 0 ][ index ]
            - signalComponents[ 1 ][ index ]
              )
                          )

      for index in range( self.numberOfChannels ):
        signal[ index ] = signal[ index ] + signalPart

      symbol = python_get_symbol( symbolTracker, self.bitsPerSymbol ) 

    csignal_destroy_symbol_tracker( symbolTracker )

    return( signal )
