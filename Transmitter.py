try:
  import threading as _threading
except ImportError:
  import dummy_threading as _threading

from cpaudio_lib import *

from BitStream import BitStream
from BitPacker import BitPacker

import WAVRecorder

import calendar
import time
import sys
import socket
import struct
import math
import wave

def playback( in_device, in_buffer_length ):                                    
  data = ''

  if( Transmitter.signal and Transmitter.lock ):
    Transmitter.lock.acquire( True )

    ( numberOfBits, buffer ) = \
      python_bit_stream_get_bits  (
        Transmitter.signal.stream,
        in_buffer_length * 8  
                                  )

    Transmitter.lock.release()

    if( 0 < numberOfBits ):
      data = buffer

  else:
    print "ERROR: Signal is not initialized!"

  return( data )

class Transmitter:
  signal  = None
  lock    = None

  def __init__  (
    self, bitDepth, numberOfChannels, sampleRate, bitsPerSymbol,
    samplesPerSymbol, carrierFrequency, outputFileName, writeOutput
                ):

    self.bitDepth         = bitDepth
    self.numberOfChannels = numberOfChannels
    self.sampleRate       = sampleRate
    self.bitsPerSymbol    = bitsPerSymbol
    self.samplesPerSymbol = samplesPerSymbol
    self.carrierFrequency = carrierFrequency

    self.constellationSize  = 2 ** self.bitsPerSymbol
    self.basebandAmplitude  = 2 ** ( self.bitDepth - 1 ) - 1

    if( writeOutput ):
      self.outputFileName = outputFileName
      self.writeOutput    = writeOutput
    else:
      self.outputFileName = None
      self.writeOutput    = None

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

      symbolTracker = BitStream( message )
      bitPacker     = BitPacker() 

      numSymbols  = symbolTracker.getSize() / self.bitsPerSymbol
      numSamples  = numSymbols * self.samplesPerSymbol
      duration    = math.ceil( numSamples / self.sampleRate )

      numSymbolsToRead =  \
        math.ceil( self.sampleRate / self.samplesPerSymbol * 0.5 )

      print "Symbols to read per iteration is 0x%x." %( numSymbolsToRead )

      hasRemaining = \
        self.bufferSymbols  (
          symbolTracker,
          bitPacker,
          numSymbolsToRead
                            )

      self.sendSignal (
        device,
        symbolTracker,
        bitPacker,
        duration,
        hasRemaining,
        numSymbolsToRead
                      )
    else:
      print "ERROR: Could not find an appropriate stream."

  
  def sendSignal  (
    self, device, symbolTracker, bitPacker, duration,
    hasRemaining, numSymbolsToRead
                  ):
    flags =                                   \
      CAHAL_AUDIO_FORMAT_FLAGISSIGNEDINTEGER  \
      | CAHAL_AUDIO_FORMAT_FLAGISPACKED

    Transmitter.signal  = BitStream( bitPacker )
    Transmitter.lock    = _threading.Lock()

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

      startTime = calendar.timegm( time.gmtime() )

      while( hasRemaining ):
        hasRemaining =  \
          self.bufferSymbols( symbolTracker, bitPacker, numSymbolsToRead )

      endTime = calendar.timegm( time.gmtime() )

      duration -= int( endTime - startTime )

      if( 0 > duration ):
        duation = 0

      duration = struct.unpack( "I", struct.pack( "i", duration ) )[ 0 ]

      cahal_sleep( duration * 1000 )

      if( cahal_stop_playback() ):
        print "Transmit stopped."
      else:
        print "ERROR: Could not stop playback."
    else:
      print "ERROR: Could not start playing."

    Transmitter.lock    = None

  def bufferSymbols( self, symbolTracker, bitPacker, numberOfSymbols ):
    symbol = symbolTracker.read( self.bitsPerSymbol )

    while( symbol != None and numberOfSymbols > 0 ):
      signalComponents = python_modulate_symbol (
        symbol,
        self.constellationSize,
        int( self.sampleRate ),
        self.samplesPerSymbol,
        self.basebandAmplitude,
        self.carrierFrequency
                                               )

      for index in range( len( signalComponents[ 0 ] ) ):
        sampleValue = \
          int (
            signalComponents[ 0 ][ index ]
            - signalComponents[ 1 ][ index ]
              )

        sampleValue = struct.pack( "i", sampleValue )
        sampleValue = struct.unpack( "I", sampleValue )[ 0 ]
        sampleValue = socket.htonl( sampleValue )

        if( 0 > sampleValue ):
          sampleValue = struct.pack( "i", sampleValue )
          sampleValue = struct.unpack( "I", sampleValue )[ 0 ]

        if( Transmitter.lock ):
          Transmitter.lock.acquire( True )

        bitPacker.writeInt( sampleValue, self.bitDepth )

        for _ in range( self.numberOfChannels - 1 ):
          bitPacker.writeInt( 0, self.bitDepth )

        if( Transmitter.lock ):
          Transmitter.lock.release()

      symbol = symbolTracker.read( self.bitsPerSymbol )

      numberOfSymbols -= 1

    if( symbol == None ):
      return( False )
    else:
      return( True )

  def __del__( self ):
    if( self.writeOutput ):
      WAVRecorder.saveSignalToWAV ( 
        Transmitter.signal, self.outputFileName, self.numberOfChannels,
        self.bitDepth, self.sampleRate
                                  )

    Transmitter.signal  = None
