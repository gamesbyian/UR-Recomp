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

function GoRight()
    buttonTable = {start=nil, select=nil, up=nil, down=nil, left=nil, right=nil, A=nil, B=nil, X=nil, Y=nil, L=nil, R=nil}
    buttonTable.right = true
    NextFrame()
end

function GoRightJump()
    buttonTable = {start=nil, select=nil, up=nil, down=nil, left=nil, right=nil, A=nil, B=nil, X=nil, Y=nil, L=nil, R=nil}
    buttonTable.right = true
    buttonTable.B = true
    NextFrame()
end

function GoRightJumpRoll()
    buttonTable = {start=nil, select=nil, up=nil, down=nil, left=nil, right=nil, A=nil, B=nil, X=nil, Y=nil, L=nil, R=nil}
    buttonTable.right = true
    buttonTable.B = true
    buttonTable.R = true
    NextFrame()
end

function GoRightJumpRollTwist()
    buttonTable = {start=nil, select=nil, up=nil, down=nil, left=nil, right=nil, A=nil, B=nil, X=nil, Y=nil, L=nil, R=nil}
    buttonTable.right = true
    buttonTable.B = true
    buttonTable.R = true
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
--numbers that jump through for jumpover: 3034r 

for i=3073,2800,-1 do
savestate.load(startSS)        

xPos = i
HitStart()
memory.writeword(RAM.uniXPos, xPos)
DoNothing()
HitStart()
GoRight()
GoRight()
GoRight()
GoRightJump()
GoRightJumpRollTwist()
GoRightJumpRollTwist()
GoRightJumpRollTwist()
GoRightJumpRollTwist()
GoRightJumpRollTwist()
GoRightJumpRollTwist()
GoRightJumpRollTwist()
GoRightJumpRollTwist()
GoRightJumpRollTwist()
GoRightJumpRollTwist()
GoRightJumpRollTwist()
GoRightJumpRollTwist()
GoRightJumpRollTwist()
GoRightJumpRollTwist()
GoRightJumpRollTwist()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
GoRightJumpRoll()
snes9x.pause()
end