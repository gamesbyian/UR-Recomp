testAreas = {
    {700, 1390, 420, 800},
    {3010, 1390, 3290, 800}
}

RAM = {
	words = {
		xSpeed = 0x7E04B7,
        ySpeed = 0x7E04BB,
        yPos = 0x7E0415,
        xPos = 0x7E0411,
        countdownTimer = 0x7E11BA,
        boost = 0x7E11CD
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
        pitch = 0x7E0F49,
        tabletops = 0x7E042F,
        messageQueueCurrentIndex = 0x7E0CE1,
        messageQueueFirstNewIndex = 0x7E0CE3,
        messageQueueStart = 0x7E0CBB
    }
}

testValues = {
    beginBoost = 0,
    endBoost = 0,
    beginFrame = 0, 
    endFrame = 0,
    endXSpeed = 0    
}

scores = {}

scoreCount = {}

function MakeWordSigned(word)
    if word > 32768 then
        word = word - 65536
    end
    
    return word
end

function values(t)
    local i = 0
    return function() i = i + 1; return t[i] end
end

function PointInRectangle(xTest, yTest, rectangle)
    local left = math.min(rectangle[1], rectangle[3])
    local right = math.max(rectangle[1], rectangle[3])
    local top = math.min(rectangle[2], rectangle[4])
    local bottom = math.max(rectangle[2], rectangle[4])
    
    if left <= xTest and xTest <= right and top <= yTest and yTest <= bottom then
        return true
    end
    
    return false
end

function Run()
    local testStarted = false

    while(true) do
        local inRace = memory.readbyte(RAM.bytes.inRace)
        
        if inRace == 1 then
            gui.text(0, 90, "boostInQueue = " .. GetBoostInQueue())
            currentTestArea = InTestArea()
            
            if currentTestArea > 0 then
                lastTestArea = currentTestArea
                if not testStarted then
                    testStarted = true
                    SetStartingTestValues()
                end
            else
                if testStarted then
                    testStarted = false
                    SetEndingTestValues()
                    ScoreTest()
                end
            end
            
            if testValues ~= nil then
                gui.text(0, 40, "testValue.beginBoost = " .. testValues.beginBoost)
                gui.text(0, 50, "testValue.endBoost = " .. testValues.endBoost)
                gui.text(0, 60, "testValue.beginFrame = " .. testValues.beginFrame)
                gui.text(0, 70, "testValue.endFrame = " .. testValues.endFrame)
                gui.text(0, 80, "testValue.endXSpeed = " .. testValues.endXSpeed)
            end
            
            WriteScores()
            emu.frameadvance()
        else
            testValues = {
                beginBoost = 0,
                endBoost = 0,
                beginFrame = 0,
                endFrame = 0,
                endXSpeed = 0    
            }
            scores = {}
            scoreCount = {}

            gui.register(nil)
            emu.frameadvance()
        end
    end
end

function InTestArea() 
    local xPos = memory.readword(RAM.words.xPos)
    local yPos = memory.readword(RAM.words.yPos)
    local retVal = 0
    
    for testArea in values(testAreas) do
        retVal = retVal + 1
        if PointInRectangle(xPos, yPos, testArea) then
            return retVal
        end
    end
    
    return 0
end

function SetStartingTestValues()
    testValues.beginBoost = memory.readword(RAM.words.boost) + GetBoostInQueue()
    testValues.beginFrame = emu.framecount()
end

function SetEndingTestValues()
    testValues.endBoost = memory.readword(RAM.words.boost) + GetBoostInQueue()
    testValues.endFrame = emu.framecount()
    testValues.endXSpeed = MakeWordSigned(memory.readword(RAM.words.xSpeed))
end

function ScoreTest()
    if scoreCount[lastTestArea] == nil then
        scoreCount[lastTestArea] = 1
    else
        scoreCount[lastTestArea] = scoreCount[lastTestArea] + 1
    end
    
    local boostGain = testValues.endBoost - testValues.beginBoost
    local frames = testValues.endFrame - testValues.beginFrame
    local xSpeed = testValues.endXSpeed
    
    local score = boostGain - 16.63768 * (frames + math.abs(math.abs(xSpeed) - 512) / 32)
    
    thisScoreCount = scoreCount[lastTestArea]
    
    if (scores[lastTestArea] == nil) then
        scores[lastTestArea] = {}
    end
    
    scores[lastTestArea][thisScoreCount] = score
end

function WriteScores()
    local scoreColumn = 1

    for scoreGroup in values(scores) do
        if scores[scoreColumn] == nil then
            return
        end

        if scoreCount[scoreColumn] ~= nil then
            for i = 1,scoreCount[scoreColumn] do
                gui.text(scoreColumn * 60 - 60, 120 + i * 10, scoreGroup[i])
            end
        end
        
        scoreColumn = scoreColumn + 1
    end
end

function GetBoostInQueue()
    local messageQueueCurrentIndex = memory.readbyte(RAM.bytes.messageQueueCurrentIndex)
    local messageQueueFirstNewIndex = memory.readbyte(RAM.bytes.messageQueueFirstNewIndex)
    local boostInQueue = 0
    
    if messageQueueFirstNewIndex < messageQueueCurrentIndex then
        messageQueueFirstNewIndex = messageQueueFirstNewIndex + 32
    end
    
    currentReadIndex = messageQueueCurrentIndex + 1
    
    while currentReadIndex < messageQueueFirstNewIndex do
        local currentMessage = memory.readbyte(RAM.bytes.messageQueueStart + (currentReadIndex % 32))
        
        if currentMessage == 1 or currentMessage == 9 or currentMessage == 18 then
            boostInQueue = boostInQueue + 128
        elseif currentMessage == 2 or currentMessage == 10 or currentMessage == 17 or currentMessage == 19 then
            boostInQueue = boostInQueue + 152
        elseif currentMessage == 3 or currentMessage == 5 or currentMessage == 11 or currentMessage == 20 then
            boostInQueue = boostInQueue + 176
        elseif currentMessage == 4 or currentMessage == 6 or currentMessage == 12 or currentMessage == 21 then
            boostInQueue = boostInQueue + 200
        elseif currentMessage == 7 then
            boostInQueue = boostInQueue + 224
        elseif currentMessage == 8 then
            boostInQueue = boostInQueue + 248
        end
        
        currentReadIndex = currentReadIndex + 1
    end
    
    return boostInQueue
end

Run()