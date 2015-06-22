from cpaudio_lib import *

from Transmitter import Transmitter

import socket
import struct

class FilterTransmitter( Transmitter ):
  def __init__  (
    self, bitDepth, numberOfChannels, sampleRate, bitsPerSymbol,
    samplesPerSymbol, carrierFrequency, outputFileName, firstStopband,
    firstPassband, secondPassband, secondStopband, passbandAttenuation,
    stopbandAttenuation, writeOutput
                ):

    Transmitter.__init__  (
      self, bitDepth, numberOfChannels, sampleRate,
      bitsPerSymbol, samplesPerSymbol, carrierFrequency,
      outputFileName, writeOutput
                          )

    self.firstStopband        = firstStopband
    self.firstPassband        = firstPassband
    self.secondPassband       = secondPassband
    self.secondStopband       = secondStopband
    self.passbandAttenuation  = passbandAttenuation
    self.stopbandAttenuation  = stopbandAttenuation

    self.filter =  \
      python_initialize_kaiser_filter (
        self.firstStopband,
        self.firstPassband,
        self.secondPassband,
        self.secondStopband,
        self.passbandAttenuation,
        self.stopbandAttenuation,
        int( self.sampleRate )
                                      )

  def bufferSymbols( self, symbolTracker, bitPacker, numberOfSymbols ):
    symbol = symbolTracker.read( self.bitsPerSymbol )

    signal = []

    while( symbol != None and numberOfSymbols > 0 ):
      signalComponents = python_modulate_symbol (
        symbol,
        self.constellationSize,
        int( self.sampleRate ),
        self.samplesPerSymbol,
        self.basebandAmplitude,
        self.carrierFrequency
                                               )

      part = []

      for index in range( len( signalComponents[ 0 ] ) ):
        sampleValue = \
          signalComponents[ 0 ][ index ] - signalComponents[ 1 ][ index ]

        part.append( sampleValue )

      signal = signal + part

      symbol = symbolTracker.read( self.bitsPerSymbol )

      numberOfSymbols -= 1

    signal = python_filter_signal( self.filter, signal )

    maxValue = -1

    for sampleValue in signal:
      if( abs( sampleValue ) > maxValue ):
        maxValue = abs( sampleValue )

    signal = map( lambda x: x / maxValue, signal )

    for sampleValue in signal:
      sampleValue = int( sampleValue * self.basebandAmplitude )
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

    if( symbol == None ):
      return( False )
    else:
      return( True )

  def __del__( self ):
    Transmitter.__del__( self )

    if( self.filter ):
      csignal_destroy_passband_filter( self.filter )
