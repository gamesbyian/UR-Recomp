RAM = {
        uniXPos = 0x7e0411
}

function DoNothing()
    buttonTable = {start=nil, select=nil, up=nil, down=nil, left=nil, right=nil, A=nil, B=nil, X=nil, Y=nil, L=nil, R=nil}
    NextFrame()
end

function HitStart()
    buttonTable = {start=nil, select=nil, up=nil, down=nil, left=nil, right=nil, A=nil, B=nil, X=nil, Y=nil, L=nil, R=nil}
    buttonTable.start = true
    NextFrame()
end

function GoLeft()
    buttonTable = {start=nil, select=nil, up=nil, down=nil, left=nil, right=nil, A=nil, B=nil, X=nil, Y=nil, L=nil, R=nil}
    buttonTable.left = true
    NextFrame()
end

function GoLeftJump()
    buttonTable = {start=nil, select=nil, up=nil, down=nil, left=nil, right=nil, A=nil, B=nil, X=nil, Y=nil, L=nil, R=nil}
    buttonTable.left = true
    buttonTable.B = true
    NextFrame()
end

function GoLeftJumpRoll()
    buttonTable = {start=nil, select=nil, up=nil, down=nil, left=nil, right=nil, A=nil, B=nil, X=nil, Y=nil, L=nil, R=nil}
    buttonTable.left = true
    buttonTable.B = true
    buttonTable.L = true
    NextFrame()
end

function GoLeftJumpRollTwist()
    buttonTable = {start=nil, select=nil, up=nil, down=nil, left=nil, right=nil, A=nil, B=nil, X=nil, Y=nil, L=nil, R=nil}
    buttonTable.left = true
    buttonTable.B = true
    buttonTable.L = true
    buttonTable.A = true
    NextFrame()
end

    
function NextFrame()
    gui.text(0, 40, "xPos : " .. xPos)
    joypad.set(1, buttonTable)
    snes9x.frameadvance()
end

startSS = savestate.create(11)
savestate.save(startSS) 

--numbers that jump through for bowl: 4965r, 4934r
--numbers that jump through for jumpover: 3034r, 3962l

for i=3960,4100,1 do
savestate.load(startSS)        

xPos = i
HitStart()
memory.writeword(RAM.uniXPos, xPos)
DoNothing()
HitStart()
GoLeft()
GoLeft()
GoLeft()
GoLeftJump()
GoLeftJumpRollTwist()
GoLeftJumpRollTwist()
GoLeftJumpRollTwist()
GoLeftJumpRollTwist()
GoLeftJumpRollTwist()
GoLeftJumpRollTwist()
GoLeftJumpRollTwist()
GoLeftJumpRollTwist()
GoLeftJumpRollTwist()
GoLeftJumpRollTwist()
GoLeftJumpRollTwist()
GoLeftJumpRollTwist()
GoLeftJumpRollTwist()
GoLeftJumpRollTwist()
GoLeftJumpRollTwist()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
GoLeftJumpRoll()
snes9x.pause()
end