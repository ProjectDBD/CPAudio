from cpaudio_lib import *

from BitStream import BitStream
from BitPacker import BitPacker

import socket
import struct
import math

def playback( in_device, in_buffer_length ):                                    
  data = ''

  if( Transmitter.signal ):
    ( numberOfBits, buffer ) = \
      python_bit_stream_get_bits  (
        Transmitter.signal.stream,
        in_buffer_length * 8  
                                  )

    if( 0 < numberOfBits ):
      print "Buffer is of length 0x%x, requested 0x%x bytes." \
        %( len( buffer ), in_buffer_length )
  
      data = buffer
  else:
    print "ERROR: Signal is not initialized!"

  return( data )

class Transmitter:
  signal = None

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

    self.signal = None

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

  def sendSignal( self, device, signal ):
    flags =                                   \
      CAHAL_AUDIO_FORMAT_FLAGISSIGNEDINTEGER  \
      | CAHAL_AUDIO_FORMAT_FLAGISPACKED

    Transmitter.signal = BitStream( signal )

    frameSize       = self.numberOfChannels * self.bitDepth / 8
    bytesPerSecond  = self.sampleRate * frameSize
    duration        = \
      math.ceil( Transmitter.signal.stream.data_length / bytesPerSecond )

    print "Duration is %d seconds." %( duration )

    if  (
      start_playback  (               \
        device.struct,                \
        CAHAL_AUDIO_FORMAT_LINEARPCM, \
        self.numberOfChannels,        \
        self.sampleRate,              \
        self.bitDepth,                \
        playback,                     \
        flags                         \
                      )               \
        ):

      duration = struct.unpack( "I", struct.pack( "i", duration ) )[ 0 ]

      print "Transmit for %d second(s)..." %( duration )

      python_cahal_sleep( duration )
    
      print "Stopping transmit..."

      if( python_cahal_stop_playback() ):
        print "Transmit stopped."
      else:
        print "ERROR: Could not stop playback."
    else:
      print "ERROR: Could not start playing."

    Transmitter.signal = None

  def prepareSignal( self, message ):
    constellationSize = 2 ** self.bitsPerSymbol
    basebandAmplitude = 2 ** ( self.bitDepth - 1 ) - 1

    symbolTracker     = BitStream( message )
    signal            = BitPacker()
  
    symbol = symbolTracker.read( self.bitsPerSymbol )

    while( symbol != None ):
      signalComponents = python_modulate_symbol (
        symbol,
        constellationSize,
        int( self.sampleRate ),
        self.samplesPerSymbol,
        basebandAmplitude,
        self.carrierFrequency
                                                )

      for index in range( self.samplesPerSymbol ):
        sampleValue = \
          int (
            signalComponents[ 0 ][ index ]
            - signalComponents[ 1 ][ index ]
              )

        sampleValue = struct.pack( "i", sampleValue )
        sampleValue = struct.unpack( "I", sampleValue )[ 0 ]
        sampleValue = socket.htonl( sampleValue )

        signal.writeInt( sampleValue, self.bitDepth )

        for _ in range( self.numberOfChannels - 1 ):
          signal.writeInt( 0, self.bitDepth )

      symbol = symbolTracker.read( self.bitsPerSymbol )

    return( signal )
