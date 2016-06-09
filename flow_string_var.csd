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

gSFile0 init ""
gSFile1 init ""
gSFile2 init ""
gSFile3 init ""

gSFile4 init ""
gSFile5 init ""
gSFile6 init ""
gSFile7 init ""


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

;-----------------------------------------------------------------
; string arr setter / getter

opcode GetFile_i, 0, kS
    kIx, Sres xin
    if kIx == 0 then
        Sres strcpy gSFile0
    elseif kIx == 1 then
        Sres strcpy gSFile1
    elseif kIx == 2 then
        Sres strcpy gSFile2
    elseif kIx == 3 then
        Sres strcpy gSFile3
    elseif kIx == 4 then
        Sres strcpy gSFile4
    elseif kIx == 5 then
        Sres strcpy gSFile5
    elseif kIx == 6 then
        Sres strcpy gSFile6
    elseif kIx == 7 then
        Sres strcpy gSFile7
    else
        Sres = ""
    endif    
endop

opcode GetFile, S, k
    kIx xin
    if kIx == 0 then
        Sres = gSFile0
    elseif kIx == 1 then
        Sres = gSFile1
    elseif kIx == 2 then
        Sres = gSFile2
    elseif kIx == 3 then
        Sres = gSFile3
    elseif kIx == 4 then
        Sres = gSFile4
    elseif kIx == 5 then
        Sres = gSFile5
    elseif kIx == 6 then
        Sres = gSFile6
    elseif kIx == 7 then
        Sres = gSFile7
    else
        Sres = ""
    endif
    xout Sres
endop

opcode SetFile, 0, kS
    kIx, Sfile xin
    if kIx == 0 then
        gSFile0 strcpyk Sfile
    elseif kIx == 1 then
        gSFile1 strcpyk Sfile
    elseif kIx == 2 then
        gSFile2 strcpyk Sfile
    elseif kIx == 3 then
        gSFile3 strcpyk Sfile
    elseif kIx == 4 then
        gSFile4 strcpyk Sfile
    elseif kIx == 5 then
        gSFile5 strcpyk Sfile
    elseif kIx == 6 then
        gSFile6 strcpyk Sfile
    elseif kIx == 7 then
        gSFile7 strcpyk Sfile   
    endif    
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

opcode StopTrig, 0, k
    kChannel xin
    kType = gkFileTypes[kChannel] 
    if (kType != 0) then
        kSched   FracInstr 100, kChannel
        turnoff2 kSched,  4, 0
    endif
endop

opcode StopInstr, 0, k
    kChannel xin
    StopLoop kChannel
    StopTrig kChannel
endop

opcode StartInstr, 0, kk
    kChannel, kIsMp3 xin
    kSched   FracInstr 100, kChannel
    event "i", kSched, 0, -1, kChannel, kIsMp3    
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

;-----------------------------------------------------------------

instr   PlayMsg
    SFile = ""    
    kVolume   init 0
    kChannel  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/play", "is", kChannel, SFile
if (kk == 0 || kChannel >= $SIZE || kChannel < 0) goto ex

    StopInstr kChannel
    SetFile kChannel, SFile
    StartInstr kChannel, 0    

    kgoto nxtmsg
ex:    
endin

instr   PlayMp3Msg
    SFile = ""    
    kVolume   init 0
    kChannel  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/play-mp3", "is", kChannel, SFile
if (kk == 0 || kChannel >= $SIZE || kChannel < 0) goto ex

    StopInstr kChannel
    SetFile kChannel, SFile
    StartInstr kChannel, 1   

    kgoto nxtmsg
ex:    
endin



instr PlayNote
    kChannel init p4
    SFile = p5

    StopInstr kChannel
    SetFile kChannel, SFile
    StartInstr kChannel, 0
    turnoff
endin

instr PlayMp3Note
    kChannel init p4
    SFile = p5

    StopInstr kChannel
    SetFile kChannel, SFile
    StartInstr kChannel, 1
    turnoff
endin


instr StopMsg
    kChannel  init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/stop", "i", kChannel
if (kk == 0 || kChannel >= $SIZE || kChannel < 0) goto ex

    if (gkFileTypes[kChannel] > 0) then
        StopInstr kChannel
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
        StopInstr kChannel   
        kIsMp3 IsMp3 kChannel 
        StartInstr kChannel, kIsMp3
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

opcode PlayLoop, 0, iiaa
    iChannel, idur, al, ar xin 
    iFadeTime = i(gkFadeTime) 
    kenv    linsegr 0, iFadeTime, 1, idur - 2 * iFadeTime, 1, iFadeTime, 0, iFadeTime, 0
    kvol    port gkVolumes[iChannel], 0.05
    gaL  = gaL + kenv * kvol * al
    gaR  = gaR + kenv * kvol * ar
endop

instr 81
    print p1
    idur     = p3
    iChannel = p4 
    SFile init ""
    GetFile_i iChannel, SFile
    aMono diskin2 SFile, 1    
    PlayLoop iChannel, idur, aMono, aMono
endin

instr 82
    print p1
    idur     = p3
    iChannel = p4 
    SFile init ""
    GetFile_i iChannel, SFile
    aLeft, aRight diskin2 SFile, 1    
    PlayLoop iChannel, idur, aLeft, aRight
endin

instr 83    
    idur     = p3
    iChannel = p4
    SFile init ""
    GetFile_i iChannel, SFile
    aLeft, aRight mp3in SFile
    PlayLoop iChannel, idur, aLeft, aRight
endin


instr 100   
    iChannel  = p4
    iIsMp3    = p5
    SFile init ""
    GetFile_i iChannel, SFile

    if (iIsMp3 == 1) then
        gkFileTypes[iChannel] = 3
        ilen mp3len SFile
    else
        iChanSize filenchnls SFile
        gkFileTypes[iChannel] = iChanSize 
        ilen  filelen SFile
    endif

    iFadeTime = i(gkFadeTime)    
    km    metro (1 / (ilen - iFadeTime))  

    kRun GetLoopId iChannel    
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
i   "PlayMp3Msg" 0 -1
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
