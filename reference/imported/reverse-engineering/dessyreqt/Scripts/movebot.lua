jumpAreas = 
{
    [3] = { --Switcher
        {3050, 410, 3300, 480}, 
        {13100, 430, 13350, 500},
        {22350, 180, 22600, 250},
        {23600, 300, 23850, 370}, 
        {25150, 300, 25400, 370}, 
        {26600, 300, 26850, 370},
        {28000, 190, 28250, 260},
        {29100, 190, 29350, 260},
        {32700, 190, 32950, 260},
        {33450, 190, 33700, 260},
        {34750, 190, 35000, 260},
        {35900, 300, 36150, 370}, 
        {40600, 640, 40850, 790},
        {41400, 820, 41650, 890}, 
        {44850, 820, 45100, 890},
        {50100, 850, 50350, 920},
        {54100, 850, 54350, 920}
    },
    [4] = { --Monster
        {6300, 2830, 6550, 2900}
    },
    [13] = { --Flat Fun
        {18150, 1000, 18400, 1080}
    },

    [20] = { --Dragrace
        {13400, 420, 13650, 490},
        {23350, 1700, 23600, 1770},
        {24300, 1820, 24550, 1890},
        {26350, 1820, 26600, 1890}
    },
    [24] = { --Short Cut
        {9650, 1580, 9900, 1650}
    },
    [30] = { --Wario Paint
        {24900, 590, 25150, 660},
        {29300, 490, 29550, 560},
        {30450, 430, 30700, 500},
        {31900, 320, 32150, 390}
    },
    [33] = { --East
        {27650, 230, 27900, 300}
    },
    [34] = { --Hairpin Hill
        {7900, 1380, 8150, 1450},
        {8400, 2770, 8650, 2840},
        {9100, 1840, 9350, 1910}
    },
    [9] = { --Small Cut
        {7900, 2300, 8050, 2370},
        {6900, 2170, 7050, 2240}
    },
    [18] = { --Plinkey
        {700, 30, 950, 100},
        {1350, 990, 1600, 1060},
        {3250, 1520, 3500, 1590},
        {4050, 1520, 4300, 1590},
        {4350, 470, 4600, 580},
        {5700, 910, 5950, 980}
    },
    [19] = { --Jumpover
        {3170, 480, 3500, 550}
    },
    [26] = { --Highroad
        {4750, 1200, 5000, 1270}, 
        {6150, 1200, 6400, 1270}
    },
    [28] = { --Boo!
        {2650, 5770, 2900, 5840},
        {2700, 990, 2950, 1070},
        {6150, 2030, 6400, 2100}
    },
    [29] = { --Fire Escape
        {2150, 1190, 2400, 1280}
    },
    [38] = { --Fruitbat
        {7050, 930, 7300, 1050}
    },
    [41] = { --Two Loops
        {3600, 490, 3888, 590}
    }
}

RAM = {
	words = {
		xSpeed = 0x7E04B7,
        yPos = 0x7E0415,
        xPos = 0x7E0411,
        countdownTimer = 0x7E11BA
	},

    bytes = {
        facedDirection = 0x7E0BA1, -- 1 is right, 0 is left
        minutes = 0x7E0E0F,
        decaseconds = 0x7E0E13,
        seconds = 0x7E0E17,
        deciseconds = 0x7E0E1B,
        centiseconds = 0x7E0E1F,
   		airValue = 0x7E0545,
        showingArrows = 0x7E0FCC, -- 0 is arrows showing, -1 is not
        arrowDirection = 0x7E0FCB, --0 is right, 1 is left
        currentTrack = 0x7E00CE,
        inRace = 0x7E0313,
        reverseControls = 0x7E132B, -- 2 is reversed, 0 is normal
        pitch = 0x7E0F49
    }
}

direction = {
	up = 1,
	right = 1,
	down = -1,
	left = -1,
	none = 0
}

decisionState = {
    directionToGo = direction.none,
    rotationDirection = direction.none,
    shouldJump = false,
    shouldBrake = false
}

function Run()
    while(true) do
        local inRace = memory.readbyte(RAM.bytes.inRace)
        
        if inRace == 1 then
            decisionState.directionToGo = GetDirectionToGo()
            decisionState.rotationDirection = GetRotationDirection()
            decisionState.shouldJump = ShouldJump()
            --decisionState.shouldBrake = ShouldBrake()
                
            SendInput()
            emu.frameadvance()
        else
            gui.register(nil)
            emu.frameadvance()
        end
    end
end

function ShouldBrake()
    local countdownTimer = memory.readword(RAM.words.countdownTimer)
    
    if  24832 < countdownTimer and countdownTimer <= 40448 then
        return true
    end
    
    return false
end

function GetRotationDirection()
    local pitch = memory.readbyte(RAM.bytes.pitch)
    
    if pitch <= 14 or pitch >= 50 then
        return direction.none
    elseif pitch <= 32 then
        return direction.left
    else
        return direction.right
    end
    
end

function ShouldJump()
    if memory.readbyte(RAM.bytes.airValue) == 9 then
        return true
    end
    
    if (InJumpArea()) then
        return true
    end
    
    return false
end

function values(t)
    local i = 0
    return function() i = i + 1; return t[i] end
end

function InJumpArea()
    local currentTrack = memory.readbyte(RAM.bytes.currentTrack)
    
    if jumpAreas[currentTrack] ~= nil then
        local xPos = memory.readword(RAM.words.xPos)
        local yPos = memory.readword(RAM.words.yPos)
        
        for jumpArea in values(jumpAreas[currentTrack]) do
            if PointInRectangle(xPos, yPos, jumpArea) then
                return true
            end
        end
    end
    
    return false
end

function PointInRectangle(xTest, yTest, x1, y1, x2, y2)
    local left = math.min(x1, x2)
    local right = math.max(x1, x2)
    local top = math.min(y1, y2)
    local bottom = math.max(y1, y2)
    
    if left <= xTest and xTest <= right and top <= yTest and yTest <= bottom then
        return true
    end
    
    return false
end

function GetDirectionToGo()
    local retVal = CurrentDirectionFromArrows()
    
    if retVal == direction.none then
        retVal = CurrentDirectionFromSpeed()
    end
    
    if retVal == direction.none then
        retVal = CurrentDirectionFromFacing()
    end
    
    return retVal
end

function CurrentDirectionFromArrows()
    local showingArrows = memory.readbyte(RAM.bytes.showingArrows)
    
    if showingArrows ~= 0 then
        return direction.none
    end
    
    local arrowDirection = memory.readbyte(RAM.bytes.arrowDirection)

    if arrowDirection == 0 then
        return direction.right
    elseif arrowDirection == 1 then
        return direction.left
    end
end

function CurrentDirectionFromFacing()
    local facedDirection = memory.readbyte(RAM.bytes.facedDirection)

    if facedDirection == 1 then
        return direction.right
    elseif facedDirection == 0 then
        return direction.left
    end
end

function CurrentDirectionFromSpeed()
    local xSpeed = memory.readword(RAM.words.xSpeed)
    
    if xSpeed > 32768 then -- Until 0.04 of snes9x-lua adds signed version of readword
		xSpeed =  xSpeed - 65536
    end
    
    --correct for very small values of xSpeed, defer to facing instead
    if math.abs(xSpeed) < 2 then
        xSpeed = 0
    end
    
    if xSpeed < 0 then
        return direction.left
    elseif xSpeed > 0 then
        return direction.right
    end
    
    return direction.none
end

function SendInput()
    local buttonTable = {
        start = nil, 
        select = nil, 
        up = nil, 
        down = nil, 
        left = nil, 
        right = nil, 
        A = nil, 
        B = nil, 
        X = nil, 
        Y = nil, 
        L = nil, 
        R = nil
    }
    
    CheckForReverseControls()

    if decisionState.directionToGo == direction.right then
        buttonTable.right = true
    end
    if decisionState.directionToGo == direction.left then
        buttonTable.left = true
    end
    if decisionState.rotationDirection == direction.right then
        buttonTable.R = true
    end
    if decisionState.rotationDirection == direction.left then
        buttonTable.L = true
    end
    buttonTable.B = decisionState.shouldJump
    buttonTable.Y = decisionState.shouldBrake
        
    joypad.set(1, buttonTable)
end

function CheckForReverseControls()
    local reverseControls = memory.readbyte(RAM.bytes.reverseControls)
    
    if reverseControls == 2 then
        decisionState.directionToGo = decisionState.directionToGo * -1
        decisionState.rotationDirection = decisionState.rotationDirection * -1
    end
end

Run()