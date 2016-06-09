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

gkVolume   init 1
gSFile     init ""

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
    turnoff2 100, 0, 0
    turnoff2 80,  0, kFadeTime    
    gSFile strcpyk SFile
    printks SFile, 0
    printk 0,kFadeTime
    event "i", 100, 0, -1, kFadeTime
    kgoto nxtmsg
ex:   
    
endin


instr 80
    idur    = p3
    iFadeTime = p4 
    ichan filenchnls gSFile
    if (ichan == 1) then
        al diskin2 gSFile, 1    
        ar = al
    else
        al, ar diskin2 gSFile, 1
    endif
    
    kenv    linsegr 0, iFadeTime, 1, idur - 2 * iFadeTime, 1, iFadeTime, 0, iFadeTime, 0
    kvol    port gkVolume, 0.05

    gaL  = gaL + kenv * kvol * al
    gaR  = gaR + kenv * kvol * ar
endin

instr 100    
    iFadeTime = p4 
    ilen  filelen gSFile        
    km    metro (1 / (ilen - iFadeTime))  
    if (km == 1)  then
        event "i", 80, 0, ilen, iFadeTime
    endif
endin

instr 110
    outs gaL, gaR
    gaL = 0
    gaR = 0
endin

</CsInstruments>
<CsScore>

f0 1000000

i   1 0 -1
i 110 0 -1
e
</CsScore>
</CsoundSynthesizer>
