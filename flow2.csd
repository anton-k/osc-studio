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
gkInstrs[]  init $SIZE

gaL init 0
gaR init 0

gihandle OSCinit $PORT

gkFadeTime init 1

opcode FracInstr, k, ik
    iInstrNum, kChannel xin
    kres = iInstrNum + ((kChannel + 1) / 1000)
    xout kres
endop

opcode TurnOff, 0, k
    kChannel xin
    if (gkInstrs[kChannel] > 0) then
    
    endif

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

instr ResumeMsg
    kChannel  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/resume", "i", kChannel
if (kk == 0 || kChannel >= $SIZE) goto ex
    kSched FracInstr 100, kChannel
    kRun1   FracInstr 81,  kChannel
    kRun2   FracInstr 82,  kChannel
    turnoff2 kSched, 4, 0
    turnoff2 kRun1,  4, gkFadeTime        
    turnoff2 kRun2,  4, gkFadeTime        
    event "i", kSched, 0, -1, kChannel
    kgoto nxtmsg
ex:    
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

instr 81
    print p1
    idur    = p3
    iFadeTime = i(gkFadeTime) 
    iChannel  = p4    
    
    al diskin2 gSFiles[iChannel], 1    
    ar = al

    kenv    linsegr 0, iFadeTime, 1, idur - 2 * iFadeTime, 1, iFadeTime, 0, iFadeTime, 0
    kvol    port gkVolumes[iChannel], 0.05
    
    gaL  = gaL + kenv * kvol * al
    gaR  = gaR + kenv * kvol * ar
endin

instr 82
    print p1
    idur    = p3
    iFadeTime = i(gkFadeTime) 
    iChannel  = p4    
    
    al, ar diskin2 gSFiles[iChannel], 1    
    
    kenv    linsegr 0, iFadeTime, 1, idur - 2 * iFadeTime, 1, iFadeTime, 0, iFadeTime, 0
    kvol    port gkVolumes[iChannel], 0.05
    
    gaL  = gaL + kenv * kvol * al
    gaR  = gaR + kenv * kvol * ar
endin


instr 100   
    iChannel  = p4 
    iFadeTime = i(gkFadeTime)
    ilen  filelen gSFiles[iChannel]
    ichan filenchnls gSFiles[iChannel]

    km    metro (1 / (ilen - iFadeTime))  

    kRun FracInstr (80 + ichan), iChannel
    gkInstrs[iChannel] = kRun
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
        gkInstrs[kCount] = -1
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

i 110 0 -1
e
</CsScore>
</CsoundSynthesizer>
