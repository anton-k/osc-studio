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
    #define SIZE        # 16 #
#end

#ifndef MEMORY_SIZE
    #define MEMORY_SIZE # 64 #
#end

#define MONO_WAV    # 1 #  
#define STEREO_WAV  # 2 #
#define MP3         # 3 #

#define MONO_INSTR #31#
#define STEREO_INSTR #32#
#define DELETE_INSTR # 123 #

#define MAX_TIME    # 1000000 #

gkTempo         init 120
gkTick          init 0
gkLocalTicks[]  init $SIZE

gkRatios[]      init $SIZE
gkIds[]         init $SIZE
gkSpeeds[]      init $SIZE
gkIsPlays[]     init $SIZE

gkChanges[]     init $SIZE
gkNeedsRewinds[] init $SIZE

gkNextIds[]     init $SIZE
gkNextIsPlays[] init $SIZE
gkNextSpeeds[]  init $SIZE

gkVolumes[]     init $SIZE
gkMasterVolume  init 1

giTab1s[]       init $MEMORY_SIZE  ; ftables for wavs
giTab2s[]       init $MEMORY_SIZE  ; ftables for wavs
giLens[]        init $MEMORY_SIZE
giBpms[]        init $MEMORY_SIZE
gkIsActive[]    init $MEMORY_SIZE

; TypesgkLocalTicks
; 0 - empty
; 1 - wav mono
; 2 - wav stereo
; 3 - mp3 stereo
gkTypes[]       init $MEMORY_SIZE

giIsDrums[]     init $MEMORY_SIZE

gkDrumWindowSize    init 512
gkPitchedWindowSize init 2048

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

opcode GetPointer, a, ii
    iId, iChannel xin

    iBpm        init giBpms[iId]
    kSpeed      init i(gkSpeeds[iChannel])    
    kLen        init giLens[iId]
    kLoopStart  init 0
    kLoopEnd    init giLens[iId]    

    kSpeed      = gkSpeeds[iChannel]
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

opcode WriteOut, 0, aai
    aL, aR, iChannel xin
    kVol    port gkVolumes[iChannel], 0.05
    gaL     = gaL + kVol * aL
    gaR     = gaR + kVol * aR    
endop


opcode FracInstr, k, kk
    kInstrNum, kChannel xin
    kres = kInstrNum + ((kChannel + 1) / 1000)
    xout kres
endop

opcode GetInstrId, k, ki
    kId, iChannel xin
    if gkTypes[kId] == $MONO_WAV then
        kRes = $MONO_INSTR
    else
        kRes = $STEREO_INSTR
    endif
    kFracRes FracInstr kRes, iChannel
    xout kFracRes
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
if (kk == 0) goto ex 
if (kId < 0 || kId >= $MEMORY_SIZE) goto ex 
if (gkIsActive[kId] != 0) goto ex 
    printks "load", 0
    kIsMp3 IsMp3 SFile     
    Sevt sprintfk {{i "LoadInstr" 0 0.01 "%s" %d %f %d %d}} , SFile, kId, kBpm, kIsMp3, kIsDrum
    scoreline Sevt, 1    
    kgoto nxtmsg
ex:    
endin


instr DeleteMsg    
    kId     init 0
    kk      init 0
    Sevt    init ""

nxtmsg:
    kk  OSClisten gihandle, "/delete", "i", kId
if (kk == 0) goto ex 
if (kId < 0 || kId >= $MEMORY_SIZE) goto ex 
if (gkIsActive[kId] != 0) goto ex 
    printks "delete", 0    
    Sevt sprintfk {{i $DELETE_INSTR 0 0.01 %d}} , kId
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
    kId init iId  

    giIsDrums[iId] = iIsDrum
    giLens[iId] = iLen
    giBpms[iId] = iBpm
    gkTypes[kId] = iType    
    turnoff
endin 

instr $DELETE_INSTR
    iId = p4
    iTab1 = giTab1s[iId]
    iTab2 = giTab2s[iId]
    iType = 0    
    iDummy  ftgen iTab1, 0, 4, 7, 0, 4, 0    
    iDummy  ftgen iTab2, 0, 4, 7, 0, 4, 0

    kId init iId  
    gkTypes[kId] = iType
    turnoff
endin


instr   PlayMsg
    kChannel    init 0
    kId         init 0
    kk          init 0

nxtmsg:
    kk  OSClisten gihandle, "/play", "ii", kChannel, kId

if (kk == 0) goto ex  
if (kId < 0 || kId >= $MEMORY_SIZE) goto ex 
if (kChannel < 0 || kChannel >= $SIZE) goto ex 
;if (gkIsPlays[kChannel] == 1 && kId == gkIds[kChannel]) goto ex 
if (gkTypes[kId] == 0) goto ex
    printks "play", 0
    gkNextIds[kChannel] = kId
    gkNextIsPlays[kChannel] = 1
    gkChanges[kChannel] = 1
    gkIsActive[kChannel] = gkIsActive[kChannel] + 1
    kgoto nxtmsg
ex:    
endin

instr StopMsg
    kChannel    init 0
    kk          init 0

nxtmsg:
    kk  OSClisten gihandle, "/stop", "i", kChannel
if (kk == 0) goto ex
if (kChannel < 0 || kChannel >= $SIZE) goto ex
;if (gkIsPlays[kChannel] == 0) goto ex
if (gkIds[kChannel] < 0) goto ex
    printks "stop", 0

    gkNextIsPlays[kChannel] = 0
    gkChanges[kChannel] = 1
    gkIsActive[kChannel] = gkIsActive[kChannel] - 1
    kgoto nxtmsg
ex:    
endin

instr FadeOutAllMsg
    kFadeTime   init 0
    kk          init 0

    ki init 0

 nxtmsg:
    kk  OSClisten gihandle, "/fade_out_and_stop_all", "f", kFadeTime
if (kk == 0) goto ex
    printks "fade_out all\n", 0
    turnoff2 $MONO_INSTR, 0, kFadeTime
    turnoff2 $STEREO_INSTR, 0, kFadeTime

    ki = 0
    kZero = 0
    while ki < $SIZE do
        gkNextIsPlays[ki] = 0
        gkIsPlays[ki] = 0
        gkIsActive[ki] = 0 ; + gkIsActive[ki]
        ki = ki + 1
    od
    kgoto nxtmsg
ex:
endin

instr ResumeMsg
    kChannel    init 0
    kk          init 0

nxtmsg:
    kk  OSClisten gihandle, "/resume", "i", kChannel
if (kk == 0) goto ex
if (kChannel < 0 || kChannel >= $SIZE) goto ex
if (gkIds[kChannel] < 0) goto ex
if (gkTypes[gkIds[kChannel]] == 0) goto ex
;if (gkIsPlays[kChannel] == 1) goto ex
    printks "resume", 0

    gkNextIsPlays[kChannel] = 1
    gkChanges[kChannel] = 1
    gkIsActive[kChannel] = gkIsActive[kChannel] + 1
    kgoto nxtmsg
ex:    
endin

instr SetSpeedMsg
    kChannel init 0
    kSpeed   init 0
    kk init  0

nxtmsg:
    kk  OSClisten gihandle, "/set_speed", "if", kChannel, kSpeed
if (kk == 0 || kChannel < 0 || kChannel >= $SIZE) goto ex  
    printks "set_speed", 0

    gkNextSpeeds[kChannel] = kSpeed
    gkChanges[kChannel] = 1
    kgoto nxtmsg
ex:    
endin

instr  SetVolMsg
    kChannel init 0
    kVolume  init 0    
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/set_volume", "if", kChannel, kVolume
if (kk == 0) goto ex 
if (kChannel < 0 || kChannel >= $SIZE) goto ex
    printks "set_volume", 0

    gkVolumes[kChannel] = kVolume
    kgoto nxtmsg
ex:    
endin

instr SetTempoMsg
    kTempo   init 0    
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/set_tempo", "f", kTempo
if (kk == 0 ) goto ex
    printks "set_tempo", 0
    gkTempo = kTempo
    kgoto nxtmsg
ex:    
endin

instr SetMasterVolumeMsg
    kVolume   init 0    
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/set_master_volume", "f", kVolume
if (kk == 0 ) goto ex
    printks "set_tempo", 0
    gkMasterVolume = kVolume
    kgoto nxtmsg
ex:    
endin


instr $MONO_INSTR
    print p1
    iId = p4
    iChannel = p5
    aTimpt GetPointer iId, iChannel
    aL, aR RunMono iId, aTimpt
    WriteOut aL, aR, iChannel
endin

instr $STEREO_INSTR
    print p1, p4, p5
    iId = p4
    iChannel = p5
    aTimpt GetPointer iId, iChannel
    aL, aR RunStereo iId, aTimpt
    WriteOut aL, aR, iChannel
endin

instr PlayLoop    
    iChannel = p4
    kCount  init 0
    kLocalTick init 0
    kChannel init iChannel    
    kLocalTick init 0

    kLocalTick = 0

    if gkTick == 1 then   
        if (kCount == 0) then
            kLocalTick = 1            
        endif

        kCount = kCount + 1
        if kCount == gkRatios[kChannel] then
            kCount = 0
        endif
    endif
    gkLocalTicks[kChannel] = kLocalTick

    if kLocalTick == 1 && gkChanges[kChannel] == 1 then
        printks "Hit\n", 0
        gkSpeeds[kChannel] = gkNextSpeeds[kChannel]       

        ; stop scenario 
        if (gkNextIsPlays[kChannel] == 0 && gkIsPlays[kChannel] == 1) then          
            kInstrId GetInstrId gkIds[kChannel], iChannel
            printks "Stop %f\n", 0, kInstrId
            turnoff2 kInstrId, 4, gkFadeTime
        ; play next track scenario        
        elseif (gkNextIsPlays[kChannel] == 1 && (gkNextIds[kChannel] != gkIds[kChannel] || gkIsPlays[kChannel] == 0)) then
            printks "Start\n", 0

            kInstrId GetInstrId gkIds[kChannel], iChannel
            kNextInstrId GetInstrId gkNextIds[kChannel], iChannel
            turnoff2 kInstrId, 4, gkFadeTime
            event "i", kNextInstrId, 0, -1, gkNextIds[kChannel], iChannel

            printks "Start %f\n", 0, kNextInstrId
        endif

        gkIds[iChannel] = gkNextIds[iChannel]
        gkIsPlays[iChannel] = gkNextIsPlays[iChannel]
        gkSpeeds[iChannel] = gkNextSpeeds[iChannel]

        gkChanges[iChannel] = 0
    endif
endin

instr TheHeart
    kTempo port gkTempo, 0.05
    gkTick metro (kTempo / 60)   
    kVol    port gkMasterVolume, 0.05

    outs kVol * gaL, kVol * gaR
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
        ii = ii + 1        
    od

    ki = 0
    while ki < $MEMORY_SIZE do
        gkIsActive[ii] = 0
        gkTypes[ii] = 0        
        ki = ki + 1        
    od    

    ii = 0
    while ii < $SIZE do
        event_i "i", "PlayLoop", 0, $MAX_TIME, ii
        ii = ii + 1        
    od

    ki = 0
    while ki < $SIZE do
        gkRatios[ki] = 8
        gkLocalTicks[ki] = 0
        gkIds[ki]    = -1
        gkSpeeds[ki] = 1
        gkIsPlays[ki]= 0

        gkChanges[ki]= 0
        gkNeedsRewinds[ki] = 0

        gkNextIds[ki] = 0
        gkNextIsPlays[ki] = -1
        gkNextSpeeds[ki] = 1
        gkVolumes[ki] = 1

        ki = ki + 1        
    od

    turnoff
endin


</CsInstruments>
<CsScore>

#define MAX_TIME    # 1000000 #

f0 $MAX_TIME

i   "LoadMsg"    0 -1
i   "DeleteMsg"    0 -1
i   "PlayMsg"    0 -1
i   "StopMsg"    0 -1 
i   "ResumeMsg"  0 -1
i   "SetSpeedMsg"  0 -1
i   "SetVolMsg"  0 -1
i   "SetTempoMsg"  0 -1
;i   "SetMasterVolumeMsg" 0 -1
;i   "FadeOutAllMsg" 0 -1

i "Init" 0 0.1
i "TheHeart" 0 -1
e
</CsScore>
</CsoundSynthesizer>
