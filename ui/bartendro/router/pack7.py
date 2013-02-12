#!/usr/bin/env python

bits = [''.join(['01'[i&(1<<b)>0] for b in xrange(7,-1,-1)]) for i in xrange(256)]

def pack_7bit(data):
    buffer = 0
    bitcount = 0
    out = ""

    while True:
        if bitcount < 7:
            buffer <<= 8
            buffer |= ord(data[0])
            data = data[1:]
            bitcount += 8
        out += chr(buffer >> (bitcount - 7))
        buffer &= (1 << (bitcount - 7)) - 1
        bitcount -= 7

        if len(data) == 0: break

    out += chr(buffer << (7 - bitcount))
    return out

def unpack_7bit(data):
    buffer = 0
    bitcount = 0
    out = ""

    while True:
        if bitcount < 8:
            buffer <<= 7
            buffer |= ord(data[0])
            data = data[1:]
            bitcount += 7

        if bitcount >= 8:
            out += chr(buffer >> (bitcount - 8))
            buffer &= (1 << (bitcount - 8)) - 1
            bitcount -= 8

        if len(data) == 0: break

    return out

