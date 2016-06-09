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

gkSize     init 0

gkVolume   init 1
gkGain     init 1
giVolumeScale init 2
gSFiles[]  init $SIZE

; FileTypes
;
; 0 -- no file
; 1 -- mono wav
; 2 -- stereo wav
; 3 -- stereo mp3
gkTypes[]  init $SIZE
gkFadeTime init 0.05

gaL init 0
gaR init 0

garL init 0
garR init 0

gihandle OSCinit $PORT

; -------------------------------------------------------------

opcode IsMp3_i, i, S
    SFile xin
    iLen strlen SFile
    SExt strsub SFile, iLen - 4, iLen
    iCmp strcmp SExt, ".mp3"
    iRes = (iCmp == 0) ? 1 : 0
    xout iRes
endop

opcode AudioFileIn2, aai, S
    SFile xin
    aL init 0
    aR init 0
    iLen = 0

    iIsMp3 IsMp3_i SFile
    if iIsMp3 == 1 then
        aL, aR mp3in SFile
        iLen mp3len SFile
    else
        iChnls filenchnls SFile
        iLen filelen SFile
        if iChnls == 1 then
            aL diskin2 SFile, 1
            aR = aL
        else 
            aL, aR diskin2 SFile, 1
        endif
    endif

    xout aL, aR, iLen
endop

; -------------------------------------------------------------

instr LoadMsg
    kIndex init 0
    SFile init ""
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/load", "is", kIndex, SFile
if (kk == 0 || kIndex < 0 || kIndex >= gkSize) goto ex    
    printks "load %d ", 0, kIndex
    printks  SFile, 0
    printks "\n", 0
    gSFiles[kIndex] strcpyk SFile
    kgoto nxtmsg
ex:       
endin

instr PlayMsg
    kDummy init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/play", "i", kDummy
if (kk == 0) goto ex
    printks "play\n", 0
    kPan  = rnd(1)
    kDist = rnd(1)
    event "i", "Play", 0, 0.1, kPan, (kDist * 0.5)
    kgoto nxtmsg
ex:       
endin

instr PlayAtMsg    
    kPan   init 0
    kDist  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/play_at", "ff", kPan, kDist
if (kk == 0) goto ex
    printks "play_at %f %f\n", 0, kPan, kDist
    event "i", "Play", 0, 0.1, kPan, kDist
    kgoto nxtmsg
ex:       
endin

instr StopMsg
    kDummy init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/stop", "i", kDummy
if (kk == 0) goto ex
    printks "stop\n", 0
    turnoff2 "Play", 0, gkFadeTime    
    kgoto nxtmsg
ex:       
endin

instr SetSizeMsg
    kSize init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/set_size", "i", kSize
if (kk == 0) goto ex
    printks "set_size %d\n", 0, kSize
    gkSize min kSize, $SIZE
    kgoto nxtmsg
ex:       
endin

instr SetVolumeMsg
    kVolume init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/set_volume", "f", kVolume
if (kk == 0) goto ex
    printks "set_volume %f\n", 0, kVolume
    gkVolume = kVolume
    kgoto nxtmsg
ex:       
endin

instr SetGainMsg
    kGain init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/set_gain", "f", kGain
if (kk == 0) goto ex
    printks "set_gain %f\n", 0, kGain
    gkGain = kGain
    kgoto nxtmsg
ex:       
endin

instr ClearMsg
    kDummy init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/clear", "i", kDummy
if (kk == 0) goto ex
    printks "clear\n", 0
    gkSize = 0
    kgoto nxtmsg
ex:       
endin


instr Play  
    iPanRel, iDistRel passign 4

    iMin = 0
    iMax = i(gkSize)
    if iMin == iMax then
        prints "memory is empty"
        turnoff
    endif    
    iIndex = iMin + int(rnd(iMax - iMin))
    iDist  = (1 + 16 * iDistRel)
    iPan   = 360 * abs(iPanRel)
    iRevsend = 0.15

    print iMin, iMax, iIndex    
    aL, aR, iLen AudioFileIn2 gSFiles[iIndex]
    p3 = iLen
    
    iDt = i(gkFadeTime)
    kEnv linseg 0, iDt, 1, iLen - 2 * iDt, 1, iDt, 0

    aL, aR   locsig (aL + aR) * 0.5, iPan, iDist, iRevsend
    arL, arR locsend

    gaL = gaL + aL
    gaR = gaR + aR   

    garL = garL + arL
    garR = garR + arR
endin

instr 110
    kVol  port gkVolume, 0.1
    kGain port gkGain, 0.1

    iWetLevel = 0.2

    arL reverb2 garL, 2.5, .3
    arR reverb2 garR, 2.5, .3

    outs ((1 - iWetLevel) * gaL + iWetLevel * arL) * kVol * kGain * giVolumeScale, ((1 - iWetLevel) * gaR + iWetLevel * arR) * kVol * kGain * giVolumeScale
    gaL = 0
    gaR = 0
    garL = 0
    garR = 0
endin

</CsInstruments>
<CsScore>

f0 1000000

i "LoadMsg" 0 -1
i "PlayMsg" 0 -1
i "PlayAtMsg" 0 -1
i "StopMsg" 0 -1
i "SetSizeMsg" 0 -1
i "SetVolumeMsg" 0 -1
i "SetGainMsg" 0 -1
i "ClearMsg" 0 -1

i 110 0 -1
e
</CsScore>
</CsoundSynthesizer>
