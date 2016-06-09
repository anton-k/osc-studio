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
    #define SIZE        # 8 #
#end

gkVolume   init 1
gSFile     init ""

gSFiles[]   init $SIZE
gkVolumes[] init $SIZE

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

gkFadeTime init 1

opcode FracInstr, k, ik
    iInstrNum, kChannel xin
    kres = iInstrNum + ((kChannel + 1) / 1000)
    xout kres
endop

opcode FracInstr_i, i, ii
    iInstrNum, iChannel xin
    ires = iInstrNum + ((iChannel + 1) / 1000)
    xout ires
endop

instr   PlayMsg
    SFile = ""    
    kVolume   init 0
    kChannel  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/play", "is", kChannel, SFile
if (kk == 0 || kChannel >= $SIZE) goto ex
    
    kSched FracInstr 100, kChannel
    kRun   FracInstr 80,  kChannel

    printk 0,kSched
     printk 0,kRun


    turnoff2 kSched, 4, 0
    turnoff2 kRun,  4, gkFadeTime    
    gSFiles[kChannel] strcpyk SFile
    event "i", kSched, 0, -1, kChannel
    kgoto nxtmsg
ex:    
endin

instr PlayNote
    iChannel = p4
    SFile = p5

    kChannel init iChannel
    kSched FracInstr 100, kChannel
    kRun   FracInstr 80,  kChannel

    turnoff2 kSched, 4, 0
    turnoff2 kRun,  4, gkFadeTime    
    gSFiles[kChannel] strcpyk SFile
    event "i", kSched, 0, -1, kChannel

    turnoff
endin


instr StopMsg
    kChannel  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/stop", "i", kChannel
if (kk == 0 || kChannel >= $SIZE) goto ex
    kSched FracInstr 100, kChannel
    kRun   FracInstr 80,  kChannel    
    turnoff2 kSched, 4, 0
    turnoff2 kRun,  4, gkFadeTime    
    kgoto nxtmsg
ex:    
endin

instr StopNote
    iChannel = p4

    kChannel init iChannel 
    kSched FracInstr 100, kChannel
    kRun   FracInstr 80,  kChannel 
    turnoff2 kSched, 4, 0
    turnoff2 kRun,  4, gkFadeTime

    turnoff
endin

instr ResumeMsg
    kChannel  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/resume", "i", kChannel
if (kk == 0 || kChannel >= $SIZE) goto ex
    kSched FracInstr 100, kChannel
    kRun   FracInstr 80,  kChannel
    turnoff2 kSched, 4, 0
    turnoff2 kRun,  4, gkFadeTime        
    event "i", kSched, 0, -1, kChannel
    kgoto nxtmsg
ex:    
endin


instr ResumeNote
    kChannel init p4

    kSched FracInstr 100, kChannel
    kRun   FracInstr 80,  kChannel
    turnoff2 kSched, 4, 0
    turnoff2 kRun,  4, gkFadeTime        
    event "i", kSched, 0, -1, kChannel
 
    turnoff
endin

instr   SetVolMsg
    kVolume   init 0
    kChannel  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/set_volume", "if", kChannel, kVolume
if (kk == 0 || kChannel >= $SIZE) goto ex
    gkVolumes[kChannel] = kVolume
    kgoto nxtmsg
ex:    
endin

instr SetVolNote
    
    kChannel init p4
    kVolume  init p5

    gkVolumes[kChannel] = kVolume

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

instr 80
    print p1
    idur    = p3
    iFadeTime = i(gkFadeTime) 
    iChannel  = p4    
    ;ichan filenchnls gSFiles[iChannel]    
    ;if (ichan == 1) then
    ;    al diskin2 gSFiles[iChannel], 1    
    ;    ar = al
    ;else
        al, ar diskin2 gSFiles[iChannel], 1
    ;endif
    
    kenv    linsegr 0, iFadeTime, 1, idur - 2 * iFadeTime, 1, iFadeTime, 0, iFadeTime, 0
    kvol    port gkVolumes[iChannel], 0.05
    
    gaL  = gaL + kenv * kvol * al
    gaR  = gaR + kenv * kvol * ar
endin


instr 100   
    iChannel  = p4 
    iFadeTime = i(gkFadeTime)
    ilen  filelen gSFiles[iChannel]
    km    metro (1 / (ilen - iFadeTime))  
    kRun FracInstr 80, iChannel
    if (km == 1)  then
        event "i", kRun, 0, ilen, iChannel
    endif
endin

instr 110
    outs gaL, gaR
    gaL = 0
    gaR = 0
endin

instr Init
    kCount = 0 
    until (kCount == lenarray(gkVolumes)) do
        gkVolumes[kCount] = 1  
        gkFileTypes[kCount] = 0
        kCount = kCount + 1
    od        
endin


</CsInstruments>
<CsScore>

f0 1000000

i "Init" 0 0.01

i   "PlayMsg"    0 -1
i   "SetVolMsg"  0 -1
i   "SetFadeMsg" 0 -1
i   "StopMsg"    0 -1 
i   "ResumeMsg"  0 -1

;i "PlayNote"   4  0.01   0 "/home/anton/hamsadhvani-pad-E.wav"
;i "PlayNote"   8  0.01   1 "/home/anton/Seashore.wav"  
;i "StopNote"   12 0.01   1
;i "SetVolNote" 14 0.01   1 0.25
;i "PlayNote"   16 0.01   1 "/home/anton/Seashore.wav"  
;i "PlayNote"   20 0.01   2 "/home/anton/overtone-major-pad-E.wav"  
;i "StopNote"   24 0.01   0 
;i "ResumeNote" 26 0.01   0
;i "PlayNote"   32 0.01   0 "/home/anton/hamsadhvani-pad-E.wav"



; "overtone-major-pad-E.wav"
; "hamsadhvani-pad-E.wav"

i 110 0 -1
e
</CsScore>
</CsoundSynthesizer>
