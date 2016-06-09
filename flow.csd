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

gkVolume   init 1

gSFiles[]   init $SIZE
gkVolumes[] init $SIZE
gkGains[]   init $SIZE

; play types
;
; 1 - play in loop
; 2 - play once
; 3 - play with period
gkPlayTypes[] init $SIZE

#define PLAY_LOOP # 1 #
#define PLAY_ONCE # 2 #
#define PLAY_PERIOD # 3 #

gkPeriods[]   init $SIZE

gkMasterVolume init 1
gkMasterGain   init 1

giVolumeScale  init 2

; FileTypes
;
; 0 -- no file
; 1 -- mono wav
; 2 -- stereo wav
; 3 -- stereo mp3
gkFileTypes[] init $SIZE

gaL init 0
gaR init 0

gihandle OSCinit $PORT

gkFadeTime init 2

;-----------------------------------------------------------------

opcode IsMp3, k, S
    SFile xin
    kLen strlenk SFile
    SExt strsubk SFile, kLen - 4, kLen
    kCmp strcmpk SExt, ".mp3"
    kRes = (kCmp == 0) ? 1 : 0
    xout kRes
endop

;-----------------------------------------------------------------

opcode FracInstr, k, kk
    kInstrNum, kChannel xin
    kres = kInstrNum + ((kChannel + 1) / 1000)
    xout kres
endop

opcode GetLoopId, k, k
    kChannel xin
    kType = gkFileTypes[kChannel]    

    if (kType > 0) then
        kInstrId FracInstr (80 + kType), kChannel
    else
        kInstrId = -1        
    endif

    xout kInstrId
endop

opcode StopLoop, 0, k
    kChannel xin
    kRun   GetLoopId kChannel
    if (kRun > 0) then
        turnoff2 kRun,  4, gkFadeTime    
    endif
endop

opcode StopTrig, 0, kk
    kChannel, kInstrId xin
    kType = gkFileTypes[kChannel] 
    if (kType != 0) then
        kSched   FracInstr kInstrId, kChannel
        turnoff2 kSched,  4, 0
    endif
endop

opcode StopTrigLoop, 0, k
    kChannel xin
    StopTrig kChannel, 100
endop

opcode StopTrigPeriod, 0, k
    kChannel xin
    StopTrig kChannel, 102
endop

opcode StopInstr, 0, k
    kChannel xin
    StopLoop kChannel
    StopTrigLoop kChannel
endop

opcode StopInstrOnce, 0, k
    kChannel xin
    StopLoop kChannel
endop

opcode StopInstrPeriod, 0, k
    kChannel xin
    StopLoop kChannel
    StopTrigPeriod kChannel
endop

opcode StartInstr, 0, kk
    kChannel, kIsMp3 xin
    kSched   FracInstr 100, kChannel
    event "i", kSched, 0, -1, kChannel, kIsMp3    
endop

opcode StartInstrOnce, 0, kk
    kChannel, kIsMp3 xin
    kSched   FracInstr 101, kChannel
    event "i", kSched, 0, -1, kChannel, kIsMp3    
endop

opcode StartInstrWithPeriod, 0, kkk
    kChannel, kIsMp3, kPeriod xin
    kSched   FracInstr 102, kChannel
    event "i", kSched, 0, -1, kChannel, kIsMp3, kPeriod
endop

opcode IsMp3, k, k
    kChannel xin
    if (gkFileTypes[kChannel] == 3) then
        kRes = 1
    else
        kRes = 0
    endif

    xout kRes
endop

opcode SetPlayOnce, 0, i
    iChannel xin    
    gkPlayTypes[iChannel] = $PLAY_ONCE
endop

opcode SetPlayLoop, 0, i
    iChannel xin
    gkPlayTypes[iChannel] = $PLAY_LOOP
endop

opcode SetPlayPeriod, 0, ii
    iChannel, iPeriod xin
    gkPlayTypes[iChannel] = $PLAY_PERIOD
    gkPeriods[iChannel] = iPeriod
endop

;-----------------------------------------------------------------

;-----------------------------------------------------------------

instr   PlayMsg
    SFile init ""    
    kVolume   init 0
    kChannel  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/play", "is", kChannel, SFile
if (kk == 0 || kChannel >= $SIZE || kChannel < 0) goto ex
    printks "play", 0

    kIsMp3 IsMp3 SFile
    StopInstr kChannel
    gSFiles[kChannel] strcpyk SFile    
    StartInstr kChannel, kIsMp3

    kgoto nxtmsg
ex:    
endin

instr PlayNote
    kChannel init p4
    SFile = p5

    StopInstr kChannel
    gSFiles[kChannel] strcpyk SFile
    StartInstr kChannel, 0
    turnoff
endin

instr PlayOnceMsg
    SFile init ""    
    kVolume   init 0
    kChannel  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/play_once", "is", kChannel, SFile
if (kk == 0 || kChannel >= $SIZE || kChannel < 0) goto ex
    printks "play_once", 0

    kIsMp3 IsMp3 SFile
    StopInstr kChannel
    gSFiles[kChannel] strcpyk SFile    
    StartInstrOnce kChannel, kIsMp3

    kgoto nxtmsg
ex:    
endin

instr   PlayPeriodMsg
    SFile init ""    
    kPeriod   init 0
    kChannel  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/play_period", "isf", kChannel, SFile, kPeriod
if (kk == 0 || kChannel >= $SIZE || kChannel < 0 || kPeriod <= 0) goto ex
    printks "play_period", 0

    kIsMp3 IsMp3 SFile
    StopInstr kChannel
    gSFiles[kChannel] strcpyk SFile    
    StartInstrWithPeriod kChannel, kIsMp3, kPeriod

    kgoto nxtmsg
ex:    
endin


instr StopMsg
    kChannel  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/stop", "i", kChannel
if (kk == 0 || kChannel >= $SIZE || kChannel < 0) goto ex

    if (gkFileTypes[kChannel] > 0) then

        if (gkPlayTypes[kChannel] == $PLAY_LOOP) then
            StopInstr kChannel
        elseif (gkPlayTypes[kChannel] == $PLAY_ONCE) then
            StopInstrOnce kChannel
        elseif (gkPlayTypes[kChannel] == $PLAY_PERIOD) then
            StopInstrPeriod kChannel            
        endif
    endif
    kgoto nxtmsg
ex:    
endin

instr StopNote
    kChannel init p4 
    StopInstr kChannel
    turnoff
endin

instr ResumeMsg
    kChannel  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/resume", "i", kChannel
if (kk == 0 || kChannel >= $SIZE || kChannel < 0) goto ex
    
    if (gkFileTypes[kChannel] > 0) then
        kIsMp3 IsMp3 kChannel 

        if (gkPlayTypes[kChannel] == $PLAY_LOOP) then
            StopInstr kChannel           
            StartInstr kChannel, kIsMp3
        elseif (gkPlayTypes[kChannel] == $PLAY_ONCE) then
            StopInstrOnce kChannel           
            StartInstrOnce kChannel, kIsMp3
        elseif (gkPlayTypes[kChannel] == $PLAY_PERIOD) then
            StopInstrPeriod kChannel       
            StartInstrWithPeriod kChannel, kIsMp3, gkPeriods[kChannel]
        endif
    endif
    kgoto nxtmsg
ex:    
endin

instr ResumeNote
    kChannel init p4
    StopInstr kChannel
    kIsMp3 IsMp3 kChannel
    StartInstr kChannel, kIsMp3
    turnoff
endin

instr  SetVolMsg
    kVolume   init 0
    kChannel  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/set_volume", "if", kChannel, kVolume
if (kk == 0 || kChannel >= $SIZE || kChannel < 0) goto ex
    gkVolumes[kChannel] = kVolume
    kgoto nxtmsg
ex:    
endin

instr  SetGainMsg
    kGain     init 0
    kChannel  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/set_gain", "if", kChannel, kGain
if (kk == 0 || kChannel >= $SIZE || kChannel < 0) goto ex
    gkGains[kChannel] = kGain
    kgoto nxtmsg
ex:    
endin

instr SetVolNote    
    kChannel init p4
    kVolume  init p5

    gkVolumes[kChannel] = kVolume
    turnoff
endin

instr SetGainNote    
    kChannel init p4
    kGain    init p5

    gkGains[kChannel] = kGain
    turnoff
endin

instr   SetFadeMsg
    kFade   init 0    
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/set_fade", "f", kFade
if (kk == 0) goto ex
    gkFadeTime = kFade
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

instr SetMasterGainMsg
    kGain   init 0    
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/set_master_gain", "f", kGain
if (kk == 0 ) goto ex 
    printks "set_tempo", 0
    gkMasterGain = kGain
    kgoto nxtmsg
ex:    
endin

opcode PlayLoop, 0, iiaa
    iChannel, idur, al, ar xin 
    iFadeTime = i(gkFadeTime) 
    kenv    linsegr 0, iFadeTime, 1, idur - 2 * iFadeTime, 1, iFadeTime, 0, iFadeTime, 0
    kvol    port gkVolumes[iChannel], 0.05
    kgain   port gkGains[iChannel], 0.05
    gaL  = gaL + kenv * kvol * kgain * al
    gaR  = gaR + kenv * kvol * kgain * ar
endop

instr 81
    print p1
    idur     = p3
    iChannel = p4 
    aMono diskin2 gSFiles[iChannel], 1    
    PlayLoop iChannel, idur, aMono, aMono
endin

instr 82
    print p1
    idur     = p3
    iChannel = p4 
    aLeft, aRight diskin2 gSFiles[iChannel], 1    
    PlayLoop iChannel, idur, aLeft, aRight
endin

instr 83    
    idur     = p3
    iChannel = p4
    aLeft, aRight mp3in gSFiles[iChannel]
    PlayLoop iChannel, idur, aLeft, aRight
endin


opcode GetLen, i, ii
    iChannel, iIsMp3 xin

    if (iIsMp3 == 1) then
        ilen mp3len gSFiles[iChannel]
    else
        ilen  filelen gSFiles[iChannel]
    endif
    xout ilen
endop

opcode SetType, 0, ii
    iChannel, iIsMp3 xin

    if (iIsMp3 == 1) then
        gkFileTypes[iChannel] = 3
    else
        iChanSize filenchnls gSFiles[iChannel]
        gkFileTypes[iChannel] = iChanSize 
    endif
endop

; Play loop (with fade in/out)
instr 100   
    iChannel, iIsMp3 passign 4    
    
    SetPlayLoop iChannel
    SetType iChannel, iIsMp3
    ilen GetLen iChannel, iIsMp3
    iFadeTime = i(gkFadeTime)   

    km    metro (1   / (ilen - iFadeTime))  

    kRun GetLoopId iChannel    
    if (km == 1)  then
        event "i", kRun, 0, ilen, iChannel
    endif
endin

; Play once
instr 101
    iChannel, iIsMp3 passign 4    
    
    SetPlayOnce iChannel
    SetType iChannel, iIsMp3
    ilen GetLen iChannel, iIsMp3

    kRun GetLoopId iChannel    
    event "i", kRun, 0, ilen, iChannel
    turnoff
endin

; Play with period
instr 102   
    iChannel, iIsMp3, iPeriod passign 4    

    SetPlayPeriod iChannel, iPeriod    
    SetType iChannel, iIsMp3
    ilen GetLen iChannel, iIsMp3   

    km    metro (1 / iPeriod)  
    kRun GetLoopId iChannel    
    if (km == 1)  then
        event "i", kRun, 0, ilen, iChannel
    endif
endin

opcode Comp, a, a
asig xin
ares dam asig, 0.01, 0.15, 1, 35/1000, 74/1000
xout ares
endop

instr 110
    kVol    port gkMasterVolume, 0.05
    kGain   port gkMasterGain, 1

    aL  = gaL
    aR  = gaR 

    aL = kVol * kGain * aL
    aR = kVol * kGain * aR 

    outs aL * giVolumeScale, aR * giVolumeScale
    gaL = 0
    gaR = 0
endin

instr Init
    iCount = 0 
    until (iCount == $SIZE) do
        gSFiles[iCount] = ""
        iCount = iCount + 1
    od

    kCount = 0 
    until (kCount == $SIZE) do
        gkVolumes[kCount] = 1  
        gkGains[kCount] = 1  
        gkFileTypes[kCount] = 0

        kCount = kCount + 1        
    od        
endin


</CsInstruments>
<CsScore>

f0 1000000

i "Init" 0 0.01

i   "PlayMsg"    0 -1
i   "PlayOnceMsg"    0 -1
i   "PlayPeriodMsg"    0 -1
i   "SetVolMsg"  0 -1
i   "SetGainMsg"  0 -1
i   "SetFadeMsg" 0 -1
i   "SetMasterVolumeMsg" 0 -1
i   "SetMasterGainMsg" 0 -1
i   "StopMsg"    0 -1 
i   "ResumeMsg"  0 -1

i 110 0 -1
e
</CsScore>
</CsoundSynthesizer>
