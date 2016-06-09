<CsoundSynthesizer>
<CsOptions>
-odac   -d -+rtaudio=alsa
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
    #define SIZE        # 8 #
#end

#ifndef MEMORY_SIZE
    #define MEMORY_SIZE # 16 #
#end

gkTempo         init 120
gkRatio         init 8
gkTick          init 0

gkId            init 0
gkSpeed         init 1
gkIsPlay        init 0

gkChange        init 0
gkNeedsRewind   init 0

gkNextId        init 0
gkNextIsPlay    init 0
gkNextSpeed     init 1

gkVolume        init 1
giTab1s[]       init $MEMORY_SIZE  ; ftables for wavs
giTab2s[]       init $MEMORY_SIZE  ; ftables for wavs
giLens[]        init $MEMORY_SIZE
giBpms[]        init $MEMORY_SIZE
gkIsActive[]    init $MEMORY_SIZE

; Types
; 0 - empty
; 1 - wav mono
; 2 - wav stereo
; 3 - mp3 stereo
gkTypes[]       init $MEMORY_SIZE

giIsDrums[]     init $MEMORY_SIZE

gkDrumWindowSize    init 512
gkPitchedWindowSize init 2048

#define MONO_WAV    # 1 #  
#define STEREO_WAV  # 2 #
#define MP3         # 3 #

#define $MONO_INSTR #31#
#define $STEREO_INSTR #32#

gaL init 0
gaR init 0

gihandle OSCinit $PORT

gkFadeTime init 0.1

;-----------------------------------------------------------------

;-----------------------------------------------------------------

opcode LpPhsr, a, kkkkk
kloopstart, kloopend, kspeed, kdir, krefdur xin

kstart01   =          kloopstart/krefdur ;start in 0-1 range
kend01     =          kloopend/krefdur ;end in 0-1 range
kfqbas     =          1 / krefdur ;phasor frequency for the whole irefdur range
kfqrel     =          kfqbas / (kend01-kstart01) * kspeed ;phasor frequency for the selected section
andxrel    phasor     kfqrel*kdir ;phasor 0-1 
atimpt     =            andxrel * (kloopend-kloopstart) + kloopstart ;adjusted to start and end

           xout       atimpt  
endop

opcode IsMp3, k, S
    SFile xin
    kLen strlenk SFile
    SExt strsubk SFile, kLen - 4, kLen
    kCmp strcmpk SExt, ".mp3"
    kRes = (kCmp == 0) ? 1 : 0
    xout kRes
endop

;-----------------------------------------------------------------

opcode GetPointer, a, i
    iId xin

    iBpm        init giBpms[iId]
    kSpeed      init i(gkSpeed)    
    kLen        init giLens[iId]
    kLoopStart  init 0
    kLoopEnd    init giLens[iId]
   
    if gkTick == 1 && gkChange == 1 then
        kSpeed = gkNextSpeed
    endif

    aTimpt     LpPhsr     kLoopStart, kLoopEnd, kSpeed * gkTempo / iBpm, 1, kLen
    xout aTimpt
endop

opcode RunMono, aa, ia
    iId, aPointer xin
    iTab1 = giTab1s[iId]
    iIsDrum = giIsDrums[iId]
    if iIsDrum == 1 then
        ifftsize = i(gkDrumWindowSize)
    else
        ifftsize = i(gkPitchedWindowSize)
    endif

    aSnd  mincer     aPointer, 1, 1, iTab1, 1, ifftsize
    xout aSnd, aSnd
endop

opcode RunStereo, aa, ia
    iId, aPointer xin
    iTab1 = giTab1s[iId]
    iTab2 = giTab2s[iId]
    aL  mincer     aPointer, 1, 1, iTab1, 1    
    aR  mincer     aPointer, 1, 1, iTab2, 1    
    xout aL, aR
endop

opcode WriteOut, 0, aa
    aL, aR xin
    kVol    port gkVolume, 0.05
    gaL     = gaL + kVol * aL
    gaR     = gaR + kVol * aR    
endop


opcode GetInstrId, k, k
    kId xin
    if gkTypes[kId] == $MONO_WAV then
        kRes = $MONO_INSTR
    else
        kRes = $STEREO_INSTR
    endif
    xout kRes
endop

;-----------------------------------------------------------------

instr   LoadMsg
    SFile   init ""
    kId     init 0
    kBpm    init 0    
    kIsDrum init 0
    kk      init 0
    Sevt    init ""

nxtmsg:
    kk  OSClisten gihandle, "/load", "isfi", kId, SFile, kBpm, kIsDrum
if (kk == 0 || kId < 0 || kId >= $MEMORY_SIZE || gkIsActive[kId] == 1) goto ex 
    kIsMp3 IsMp3 SFile     
    Sevt sprintfk {{i "LoadInstr" 0 0.01 "%s" %d %f %d %d}} , SFile, kId, kBpm, kIsMp3, kIsDrum
    scoreline Sevt, 1    
    kgoto nxtmsg
ex:    
endin

instr LoadInstr
    SFile, iId, iBpm, iIsMp3, iIsDrum passign 4

    iTab1 = giTab1s[iId]
    iTab2 = giTab2s[iId]

    if (iIsMp3 == 1) then
        iType = $MP3
        iDummy ftgen iTab1, 0, 0, 49, SFile, 0, 3
        iDummy ftgen iTab2, 0, 0, 49, SFile, 0, 4
        iLen   mp3len SFile
    else
        iChnls filenchnls SFile
        iLen   filelen SFile
        if (iChnls == 1) then
            iType = $MONO_WAV
            iDummy  ftgen iTab1, 0, 0, 1, SFile, 0, 0, 1            
        else
            iType = $STEREO_WAV
            iDummy  ftgen iTab1, 0, 0, 1, SFile, 0, 0, 1            
            iDummy  ftgen iTab2, 0, 0, 1, SFile, 0, 0, 2            
        endif
    endif    

    giIsDrums[iId] = iIsDrum
    giLens[iId] = iLen
    giBpms[iId] = iBpm
    gkTypes[iId] = iType
    turnoff
endin 


instr   PlayMsg
    kId  init 0
    kk   init 0

nxtmsg:
    kk  OSClisten gihandle, "/play", "i", kId
if (kk == 0 || kId < 0 || kId >= $MEMORY_SIZE || (gkIsPlay == 1 && kId == gkId) || gkTypes[kId] == 0) goto ex
    prints "Play"
    gkNextId = kId
    gkNextIsPlay = 1
    gkChange = 1    
    kgoto nxtmsg
ex:    
endin

instr StopMsg
    kDummy  init 0
    kk   init 0

nxtmsg:
    kk  OSClisten gihandle, "/stop", "i", kDummy
if (kk == 0) goto ex
    gkNextIsPlay = 0
    gkChange = 1
    kgoto nxtmsg
ex:    
endin

instr ResumeMsg
    kDummy  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/resume", "i", kDummy
if (kk == 0 || gkTypes[gkId] == 0) goto ex  
    gkNextIsPlay = 1
    gkChange = 1
    kgoto nxtmsg
ex:    
endin

instr SetSpeedMsg
    kSpeed  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/set_speed", "f", kSpeed
if (kk == 0) goto ex  
    gkNextSpeed = kSpeed
    gkChange = 1
    kgoto nxtmsg
ex:    
endin

instr  SetVolMsg
    kVolume   init 0    
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/set_volume", "f", kVolume
if (kk == 0 ) goto ex
    gkVolume = kVolume
    kgoto nxtmsg
ex:    
endin

instr  SetTempoMsg
    kTempo   init 0    
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/set_tempo", "f", kTempo
if (kk == 0 ) goto ex
    gkTempo = kTempo
    kgoto nxtmsg
ex:    
endin


instr $MONO_INSTR
    iId = p4
    aTimpt GetPointer iId
    aL, aR RunMono iId, aTimpt
    WriteOut aL, aR
endin

instr $STEREO_INSTR
    iId = p4
    aTimpt GetPointer iId
    aL, aR RunStereo iId, aTimpt
    WriteOut aL, aR
endin

instr PlayLoop
    if gkTick == 1 && gkChange == 1 then
        gkSpeed = gkNextSpeed

        ; stop scenario 
        if (gkNextIsPlay == 0 && gkIsPlay == 1) then
            kInstrId GetInstrId gkId
            turnoff2 kInstrId, 0, gkFadeTime
        ; play next track scenario        
        elseif (gkNextIsPlay == 1 && (gkNextId != gkId || gkIsPlay == 0)) then
            kInstrId GetInstrId gkId
            kNextInstrId GetInstrId gkNextId
            turnoff2 kInstrId, 0, gkFadeTime
            event "i", kNextInstrId, 0, -1, gkNextId
        endif

        gkId = gkNextId
        gkIsPlay = gkNextIsPlay    

        gkChange = 0
    endif
endin

instr TheHeart
    kCount init 0

    kTempo port gkTempo, 0.05
    kTick metro (kTempo / 60)

    if (kTick == 1) then
        if (kCount == 0) then
            gkTick = 1
        else
            gkTick = 0
        endif
        
        kCount = kCount + 1
        if kCount == gkRatio then
            kCount = 0
        endif
    else
        gkTick = 0
    endif

    outs gaL, gaR
    gaL = 0
    gaR = 0
endin

instr Init
    ii = 0
    iTab1 = 0
    iTab2 = 0

    while ii < $MEMORY_SIZE do
        iTab1 ftgen 0, 0, 4, 7, 0, 4, 0
        iTab2 ftgen 0, 0, 4, 7, 0, 4, 0
        giTab1s[ii] = iTab1
        giTab2s[ii] = iTab2
        print iTab1
        print iTab2
        giBpms[ii] = 0
        giLens[ii] = 0
        gkIsActive[ii] = 0
        gkTypes[ii] = 0
        ii = ii + 1
    od
    turnoff
endin


</CsInstruments>
<CsScore>

f0 1000000

i   "LoadMsg"    0 -1
i   "PlayMsg"    0 -1
i   "StopMsg"    0 -1 
i   "ResumeMsg"  0 -1
i   "SetSpeedMsg"  0 -1
i   "SetVolMsg"  0 -1
i   "SetTempoMsg"  0 -1

i "Init" 0 0.1
i "PlayLoop" 0 -1
i "TheHeart" 0 -1
e
</CsScore>
</CsoundSynthesizer>
