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

    #define PORT        # 47120 #

#end

gkVolume   init 1
gkIsActive init 0

gSFile     = ""
gSwav      = ""

gaL init 0
gaR init 0

gihandle OSCinit $PORT

instr   1
    SFile = ""
    kFadeTime init 0
    kVolume   init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/flow/play", "sf", SFile, kFadeTime
if (kk == 0) goto ex
    gSFile = SFile
    printks SFile, 0
    printk 0,kFadeTime
    strset 1, SFile
    event "i", "Play", 0, 0.01, kFadeTime
    event "i", 200, 0.01, 12
    kgoto nxtmsg
ex:
    
    ; kk = 1
    ; until (kk == 0) do
    ;     kk  OSClisten gihandle, "/flow/play", "sf", SFile, kFadeTime
        
    ;     if kk != 0 then
    ;         gSFile = SFile
    ;         prints SFile
    ;         event "i", "Play", 0, 0.01, kFadeTime
    ;     endif
    ; od

    ; kk = 1
    ; until (kk == 0) do
    ;     if kk != 0 then
    ;         kk  OSClisten gihandle, "/flow/set_volume", "d", kVolume
    ;         gkVolume = kVolume   
    ;     endif
    ; od
endin


instr Play    
    iFadeTime = p4

    iIsAkctive = i(gkIsActive) 

    turnoff2 80, 0, iFadeTime 
    if (iIsAkctive == 1) then 
        turnoff2 100.1, 4, 0
        event_i "i", 100.2, 0, -1, iFadeTime
        gkIsActive = 2
    else
        turnoff2 100.2, 4, 0
        event_i "i", 100.1, 0, -1, iFadeTime
        gkIsActive = 1
    endif
    turnoff
endin


instr 80
    idur    = p3
    iFadeTime = p4    
    
    al, ar  diskin2 gSFile, 1
    kenv    linsegr 0, iFadeTime, 1, idur - 2 * iFadeTime, 1, iFadeTime, 0, iFadeTime, 0
    kvol    port gkVolume, 0.05

    gaL  = gaL + kenv * kvol * al
    gaR  = gaR + kenv * kvol * ar
endin

instr 100    
    iFadeTime = p4   
    
    print iFadeTime     
    ilen  filelen gSFile
    km    metro (1 / (ilen - iFadeTime))

    schedwhen km, 80, 0, ilen, iFadeTime
endin

instr 110
    outs gaL, gaR
endin

instr 200
    SFile strget 1
    al, ar  diskin2 SFile, 1
    outs al, ar    
endin

instr 201
    gSwav = "/home/anton/Seashore.wav"
    turnoff
endin

</CsInstruments>
<CsScore>

f0 1000000

i   1 0 -1
i 110 0 -1

e
</CsScore>
</CsoundSynthesizer>
