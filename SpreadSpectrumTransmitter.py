from cpaudio_lib import *

from Transmitter import Transmitter
from FilterTransmitter import FilterTransmitter

import socket
import struct

class SpreadSpectrumTransmitter( FilterTransmitter ):
  def __init__  (
    self, bitDepth, numberOfChannels, sampleRate, bitsPerSymbol,
    samplesPerSymbol, carrierFrequency, outputFileName, firstStopband,
    firstPassband, secondPassband, secondStopband, passbandAttenuation,
    stopbandAttenuation, polynomialDegree, firstGenerator, secondGenerator,
    firstInitialValue, secondInitialValue, samplesPerChip, filter, writeOutput
                ):

    FilterTransmitter.__init__  (
      self, bitDepth, numberOfChannels, sampleRate,
      bitsPerSymbol, samplesPerSymbol, carrierFrequency,
      outputFileName, firstStopband, firstPassband, secondPassband,
      secondStopband, passbandAttenuation, stopbandAttenuation,
      writeOutput
                          )

    self.polynomialDegree   = polynomialDegree
    self.firstGenerator     = firstGenerator
    self.secondGenerator    = secondGenerator
    self.firstInitialValue  = firstInitialValue
    self.secondInitialValue = secondInitialValue
    self.samplesPerChip     = samplesPerChip

    self.inphaseSpreadingCode = \
      python_initialize_gold_code (
        self.polynomialDegree, self.firstGenerator, self.secondGenerator,
        self.firstInitialValue, self.secondInitialValue
                                  )

    self.quadratureSpreadingCode = \
      python_initialize_gold_code (
        self.polynomialDegree, self.firstGenerator, self.secondGenerator,
        self.firstInitialValue, self.secondInitialValue
                                  )

    self.applyFilter = filter

  def bufferSymbols( self, symbolTracker, bitPacker, numberOfSymbols ):
    symbol = symbolTracker.read( self.bitsPerSymbol )

    signal = []

    print "Number of symbols: %d" %( numberOfSymbols )

    while( symbol != None and numberOfSymbols > 0 ):
      print "Symbol: %d" %( symbol )

      signalComponents =  \
        python_modulate_symbol  (
          symbol,
          self.constellationSize,
          int( self.sampleRate ),
          self.samplesPerSymbol,
          self.basebandAmplitude,
          self.carrierFrequency
                                )

      inphasePart = python_spread_signal  (
          self.inphaseSpreadingCode,
          self.samplesPerChip,
          signalComponents[ 0 ]
                                          )

      quadraturePart = python_spread_signal (
        self.quadratureSpreadingCode,
        self.samplesPerChip,
        signalComponents[ 1 ]
                                            )

      part = []

      for index in range( self.samplesPerSymbol ):
        sampleValue = \
          inphasePart[ index ] - quadraturePart[ index ]

        part.append( sampleValue )

      signal = signal + part

      symbol = symbolTracker.read( self.bitsPerSymbol )

      numberOfSymbols -= 1

    if( 0 < len( signal ) ):
      print "Length is %d." %( len( signal ) )

      if( self.applyFilter ):
        signal = python_filter_signal( self.filter, signal )

        maxValue = -1

        for sampleValue in signal:
          if( abs( sampleValue ) > maxValue ):
            maxValue = abs( sampleValue )
    
        signal = \
          map( lambda x: self.basebandAmplitude * ( x / maxValue ), signal )

      for sampleValue in signal:
        sampleValue = int( sampleValue )
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
    FilterTransmitter.__del__( self )

    csignal_destroy_gold_code( self.inphaseSpreadingCode )
    csignal_destroy_gold_code( self.quadratureSpreadingCode )
