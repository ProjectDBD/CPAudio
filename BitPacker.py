from cpaudio_lib import *

import struct

class BitPacker:
  def __init__( self ):
    self.packer = python_bit_packer_initialize()

  def __del__( self ):
    if( self.packer ):
      bit_packer_destroy( self.packer )

  def writeInt( self, number, numberOfBits ):
    if( 0 > numberOfBits ):
      print "ERROR: Invalid number of bits %d." %( numberOfBits )
    elif( 0 > number ):
      print "ERROR: Invalid unsigned int value %d." %( number )
    else:
      string = struct.pack( "!I", number )

      for byte in string:
        numberOfReadBits = numberOfBits

        if( 8 < numberOfReadBits ):
          numberOfReadBits = 8

        result = \
          bit_packer_add_bits( ord( byte ), numberOfReadBits, self.packer )

        if( CPC_ERROR_CODE_NO_ERROR != result ):
          print "ERROR: Could not write %d bits of byte (%s): 0x%x." \
            %( numberofReadBits, bin( ord( byte ) ), result )

        numberOfBits -= numberOfReadBits

        if( 0 == numberOfBits ):
          break
