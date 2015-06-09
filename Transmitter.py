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
      print "Transmitting: %s." %( message )

      constellationSize = 2 ** self.bitsPerSymbol
      symbolTracker     = python_initialize_symbol_tracker( message )
      symbol            = \
        python_get_symbol( symbolTracker, self.bitsPerSymbol ) 
      basebandAmplitude = 2 ** ( self.bitDepth - 1 ) - 1
  
      while( symbol != None ):
        signal = python_modulate_symbol (
          symbol,
          constellationSize,
          int( self.sampleRate ),
          self.samplesPerSymbol,
          basebandAmplitude,
          self.carrierFrequency
                                        )

        symbol = python_get_symbol( symbolTracker, self.bitsPerSymbol ) 

      csignal_destroy_symbol_tracker( symbolTracker )
    else:
      print "ERROR: Could not find an appropriate stream."
      
