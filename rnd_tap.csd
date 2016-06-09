<CsoundSynthesizer>
<CsOptions>
-odac   -d 
</CsOptions>
<CsInstruments>

sr = 44100
ksmps = 64
nchnls = 2
0dbfs  = 1

#ifndef PORT
    #define PORT        # 7700 #
#end

#ifndef SIZE
    #define SIZE        # 32 #
#end

gkSize     init $SIZE
gkLen      init 0
gkIndex    init 0

gkVolume   init 1
gSFiles[]  init $SIZE
gkFadeTime init 0.05

gaL init 0
gaR init 0

gihandle OSCinit $PORT


instr LoadMsg
    SFile = ""
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/load", "s", SFile
if (kk == 0) goto ex
    printk 0, gkLen
    gSFiles[gkIndex] strcpyk SFile
    gkLen min (gkLen + 1), gkSize
    gkIndex = gkIndex + 1
    if gkIndex == gkSize then
        gkIndex = 0
    endif    
    kgoto nxtmsg
ex:       
endin

instr PlayMsg
    kDummy init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/play", "i", kDummy
if (kk == 0) goto ex
    event "i", "Play", 0, 0.1
    kgoto nxtmsg
ex:       
endin

instr SetSizeMsg
    kSize init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/set_size", "i", kSize
if (kk == 0) goto ex
    gkSize min kSize, $SIZE
    gkIndex = 0
    gkLen min gkLen, kSize    
    kgoto nxtmsg
ex:       
endin

instr SetVolumeMsg
    kVolume init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/set_volume", "f", kVolume
if (kk == 0) goto ex
    gkVolume = kVolume
    kgoto nxtmsg
ex:       
endin

instr ClearMsg
    kDummy init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/clear", "i", kDummy
if (kk == 0) goto ex
    gkLen = 0
    kgoto nxtmsg
ex:       
endin


instr Play    
    iMin = 0
    iMax = i(gkLen)
    iIndex random iMin, iMax
    print iMin, iMax, iIndex
    SFile strcpy gSFiles[int(iIndex)]
    iLen filelen SFile
    xtratim iLen
    iDt = i(gkFadeTime)
    kEnv linseg 0, iDt, 1, iLen - 2 * iDt, 1, iDt, 0

    kMax init iMax
    if (kMax == 0) then
        turnoff2 "Play", 0, 0
    endif
    aL, aR diskin2 SFile, 1
    gaL = gaL + aL
    gaR = gaR + aR

   
endin

instr 110
    kVol port gkVolume, 0.1
    outs gaL * kVol, gaR * kVol
    gaL = 0
    gaR = 0
endin

</CsInstruments>
<CsScore>

f0 1000000

i "LoadMsg" 0 -1
i "PlayMsg" 0 -1
i "SetSizeMsg" 0 -1
i "SetVolumeMsg" 0 -1
i "ClearMsg" 0 -1

i 110 0 -1
e
</CsScore>
</CsoundSynthesizer>
