singlePlayer = true
controller = 1
targetMedal = 21 -- 17 for bronze, 19 for silver, 21 for gold
targetPlayerCol = 6 -- 6 is left, 7 is right
targetPlayerRow = 0

jumpAreas = {
    [0] = { --Dragster
        {1090, 790, 25278, 870}
    },
    [1] = { --Zoom Zoo
        {6650, 2210, 6850, 2280},
        {7100, 1460, 8850, 1530},
        {12500, 3370, 12700, 3460}
    },
    [3] = { --Switcher
        {1700, 420, 2100, 490},
        {3050, 420, 3300, 490},
        {4700, 580, 6250, 650},
        {9250, 420, 12500, 500},
        {13650, 380, 13150, 460},
        {12750, 380, 19500, 870},
        {21350, 170, 22000, 250},
        {22350, 180, 22600, 250},
        {22800, 180, 26500, 280},
        {23600, 300, 23850, 370},
        {25150, 300, 25400, 370},
        {26600, 300, 26850, 370},
        {28000, 190, 28250, 260},
        {29100, 190, 29350, 260},
        {29600, 190, 32250, 260},
        {32700, 190, 32950, 260},
        {33450, 190, 33700, 260},
        {33850, 190, 34400, 260},
        {34750, 190, 35000, 260},
        {35100, 190, 36700, 260},
        {35900, 300, 36150, 370},
        {40600, 640, 40850, 790},
        {41000, 640, 47700, 920},
        {41400, 820, 41650, 890},
        {44850, 820, 45100, 890},
        {48900, 830, 49500, 890},
        {50100, 850, 50350, 920},
        {50600, 830, 53700, 890},
        {54100, 850, 54350, 920},
        {54650, 830, 63062, 890}
    },
    [4] = { --Monster
        {2400, 430, 6250, 520},
        {6300, 2830, 6550, 2900}
    },
    [10] = { --Looper
        {1776, 620, 4096, 1390},
        {0, 620, 231, 1390},
        {0, 1440, 3885, 3610},
        {2800, 3540, 4096, 3940},
        {2725, 3970, 4096, 4630},
        {2900, 5120, 4096, 5960},
        {2680, 6000, 4096, 6700},
        {0, 6700, 4096, 8400},
        {350, 8540, 1670, 9230},
        {0, 9850, 4096, 10500},
        {0, 11360, 2100, 12150},
        {0, 12120, 4096, 16000}
    },
    [11] = { --Megajump
        {14200, 3150, 14400, 3220},
        {7400, 1930, 7940, 2240},
        {4900, 3240, 5700, 3310},
        {7300, 3250, 13400, 3320}
    },
    [13] = { --Flat Fun
        {2192, 40, 9000, 570},
        {9850, 500, 10200, 570},
        {15950, 110, 20500, 890},
        {24050, 110, 25750, 890},
        {29550, 750, 29800, 830},
        {29000, 870, 30450, 1330},
        {26500, 1260, 28050, 1340},
        {21250, 1170, 24050, 1330},
        {19000, 1000, 19900, 1080},
        {18150, 1000, 18400, 1080},
        {17250, 1260, 17850, 1530},
        {13700, 1310, 15700, 1850},
        {5206, 1010, 10750, 1080}
    },
    [14] = { --Infinity
        {1000, 1310, 2700, 1380}
    },
    [20] = { --Dragrace
        {3264, 350, 6000, 420},
        {7100, 600, 10600, 1780},
        {10450, 240, 12900, 490},
        {13400, 420, 13650, 490},
        {13700, 420, 15100, 490},
        {17600, 50, 22850, 1770},
        {23350, 1700, 23600, 1770},
        {23750, 1700, 27200, 1780},
        {24300, 1820, 24550, 1890},
        {26350, 1820, 26600, 1890},
        {27300, 1820, 30547, 1890}
    },
    [21] = { --Pingpong
        {7500, 1900, 11350, 2370},
        {6400, 2670, 6750, 2790},
        {4700, 1670, 5400, 1750},
        {7000, 1170, 9700, 1640},
        {10200, 1570, 10450, 1640}
    },
    [23] = { --Hybrid
        {0, 170, 5050, 1990},
        {13900, 3170, 15900, 3380}
    },
    [24] = { --Short Cut
        {1800, 600, 3350, 1090},
        {5950, 2200, 6050, 2310},
        {4900, 940, 9150, 2040},
        {9650, 1580, 9900, 1650},
        {10250, 1920, 11350, 2170},
        {7800, 2520, 13200, 2630}
    },
    [30] = { --Wario Paint
        {1300, 130, 5500, 50},
        {8650, 490, 8900, 400},
        {9600, 700, 11500, 930},
        {13200, 260, 15200, 180},
        {15820, 360, 16100, 280},
        {17200, 650, 18500, 570},
        {20300, 180, 20450, 100},
        {21800, 60, 22200, 180},
        {23500, 740, 23800, 660},
        {23800, 650, 23550, 570},
        {24900, 590, 25150, 670},
        {25450, 660, 25850, 580},
        {27550, 660, 28400, 580},
        {29300, 490, 29550, 560},
        {30450, 430, 30700, 500},
        {31900, 320, 32150, 390},
        {32475, 300, 35350, 420},
        {38000, 720, 47100, 850}
    },
    [31] = { --Crock
        {7100, 1600, 10400, 1490},
        {13400, 2640, 13150, 2730},
        {11100, 3500, 10450, 3960},
        {9525, 3850, 9000, 4010},
        {8350, 3830, 7950, 3970},
        {9100, 3270, 9350, 3190},
        {8250, 2200, 7250, 2560},
        {5150, 1960, 5650, 1870}
    },
    [33] = { --East
        {6150, 500, 3088, 420},
        {7850, 0, 11350, 890},
        {14400, 230, 14850, 310}, 
        {15950, 40, 17600, 120},
        {21100, 700, 22250, 890},
        {24800, 0, 27200, 310},
        {27650, 230, 27900, 310},
        {32100, 250, 32750, 160},
        {35400, 160, 37500, 250},
        {41575, 370, 41775, 290},
        {45800, 360, 46600, 230},
        {49250, 550, 58100, 880}
    },
    [34] = { --Hairpin Hill
        {7900, 1380, 8150, 1450},
        {8400, 2770, 8650, 2850},
        {9100, 1840, 9350, 1910},
        {7650, 2370, 8050, 2290},
        {9750, 1910, 9600, 1840}
    },
	[5] = { --Wobble
        {2280, 430, 4096, 2014},
        {0, 1040, 2800, 2800},
        {2900, 2810, 0, 3870},
        {4096, 3670, 2750, 4220},
        {2440, 4530, 0, 5600},
        {2180, 5800, 800, 6770},
        {1390, 7920, 2460, 8500},
        {1440, 8920, 2660, 9440},
        {2440, 11700, 0, 13110},
        {0, 13620, 4096, 14670},
	},
    [6] = { --Twinpeak
        {9829, 3198, 10951, 3305},
        {14088, 2523, 14268, 2642},
        {14549, 3515, 15857, 3677},
        {2275, 3810, 3566, 4034},
        {4324, 3662, 7652, 4002},
		{13940, 2814, 14544, 2914},
        {406, 2624, 456, 2901},
       --{7900, 2300, 8050, 2370},
    },
	[8] = { --Loopback
        {622, 1754, 2036, 1858},
        {12070, 844, 12378, 1100},
        {14547, 1630, 17140, 1736},
        {21061, 1134, 21204, 1354},
        {26982, 1455, 29075, 1954},
        {0, 1129, 32184, 1233},
        {0, 999, 1620, 1229},
	},
    [9] = { --Small Cut
        {7900, 2300, 8100, 2370},
        {6775, 2176, 7075, 2278},
        {8938, 3230, 9061, 3361},
        {9140, 2117, 9235, 2309},
        {5378, 2699, 8276, 3255},
    },
	[15] = { --Last One
        {15221, 46, 16087, 146},
        {13615, 465, 14212, 578},
        {11922, 357, 12024, 438},
        {10889, 639, 11043, 954},
        {8356, 1707, 8455, 1831},
        {13409, 3875, 14389, 4061},
        {12725, 3828, 12853, 3944},
        {11539, 3826, 11648, 3945},
        {9233, 3844, 10421, 3970},
        {8222, 3406, 8325, 3510},
        {6475, 3931, 7121, 4034},
        {0, 2894, 5574, 3931},
        {15652, 3831, 16384, 3938},
	},
	[16] = { --Marathon
        {7955, 1341, 8585, 1529},
        {7065, 1248, 7202, 1350},
        {3685, 2670, 4892, 2770},
        {2974, 1610, 3389, 1762},
        {4193, 608, 4373, 740},
	},
    [18] = { --Plinkey
        {700, 30, 950, 100},
        {1350, 990, 1600, 1060},
        {3250, 1520, 3500, 1590},
        {4050, 1520, 4300, 1590},
        {4350, 470, 4600, 580},
        {5700, 910, 5950, 980},
        {1357, 46, 1843, 147},
        {1478, 174, 2052, 370},
        {200, 729, 675, 829},
        {3374, 478, 4141, 583},
        {6562, 843, 7080, 1026},
        {3614, 1198, 4226, 1298},
        {2562, 1529, 3069, 1638},
        {4607, 1489, 5236, 1634},
        {209, 1987, 6717, 2091},
    },
    [19] = { --Jumpover
        {3170, 480, 3500, 550},
        {4836, 944, 5590, 1046},
        {1399, 846, 2010, 962},
        {924, 899, 1274, 962},
        {681, 455, 1527, 594},
    },
	[25] = { --Down+Up
        {753, 1004, 3253, 1106},
        {7494, 4564, 8138, 4669},
        {0, 2001, 1305, 2160},
        {7627, 2060, 8196, 2160},
        {344, 514, 882, 754},
        {6769, 1138, 7488, 1698},
        {0, 1480, 3539, 1698},
        {1287, 1239, 2988, 1347},
	},
    [26] = { --Highroad
        {4700, 1200, 5000, 1270},
        {6110, 1200, 6400, 1270},
        {2962, 598, 3738, 971},
        {5659, 2900, 6231, 3010},
        {1238, 525, 1499, 642},
        {6725, 1212, 7172, 1316},
    },
    [28] = { --Boo!
        {2700, 990, 2950, 1070},
        {6150, 2030, 6400, 2100},
        {190, 40, 1242, 146},
        {1233, 542, 1469, 674},
        {4806, 2046, 5824, 2147},
        {5172, 2255, 6142, 2373},
        {1884, 3092, 3804, 3197},
        {5645, 3389, 6315, 3490},
        {5432, 4177, 5567, 4324},
        {2044, 5780, 2969, 5885},
        {3233, 5790, 5309, 5890},
    },
    [29] = { --Fire Escape
        {2250, 1207, 2486, 1335},
        {1497, 430, 2015, 530},
    },
	[35] = { --Vertical
        {692, 16168, 1620, 16274},
        {1959, 16076, 2356, 16226},
        {3391, 15902, 4096, 16034},
        {0, 15929, 201, 16034},
        {919, 15709, 2379, 15856},
        {3930, 12209, 3997, 12331},
        {484, 12427, 568, 12554},
        {3466, 11771, 4096, 11874},
        {531, 11580, 641, 11683},
        {2211, 11263, 2332, 11390},
        {1244, 8210, 1476, 8322},
        {531, 8091, 710, 8200},
        {1164, 7963, 4039, 8072},
        {0, 7838, 836, 7943},
        {2101, 7830, 4096, 7938},
        {1473, 7703, 0, 7815},
        {4096, 7703, 2697, 7815},
        {0, 7574, 2047, 7686},
        {2781, 7574, 4096, 7686},
        {0, 6926, 1378, 7030},
        {3834, 6926, 4096, 7030},
	},
	[36] = { --Flash
        {7652, 2914, 7939, 3026},
        {3028, 2923, 7040, 3026},
	},
    [38] = { --Fruitbat
        {7050, 930, 7300, 1050},
        {398, 88, 3112, 206},
        {2251, 238, 3205, 594},
        {480, 973, 776, 1090},
        {2806, 1609, 5818, 1826},
        {4054, 1134, 4513, 1239},
        {4030, 942, 6561, 1043},
        {7625, 942, 8926, 1043},
        {8370, 356, 10520, 460},
        {11270, 726, 11403, 892},
        {13872, 1319, 9811, 2178},
        {3863, 2071, 9811, 2178},
    },
	[39] = { --123 Jump
        {11483, 1087, 14600, 2018},
        {9989, 2052, 16051, 2688},
        {9147, 2476, 9353, 2595},
        {8149, 2356, 8340, 2472},
        {7099, 2220, 7318, 2343},
        {4399, 1908, 4986, 2162},
        {1813, 942, 2303, 1042},
	},
	[40] = { --Griller
        {817, 547, 1584, 674},
        {351, 1789, 969, 1980},
        {3112, 3224, 3510, 3352},
        {359, 4829, 1404, 5373},
        {3383, 6135, 3496, 6238},
        {466, 7799, 2586, 7920},
        {5422, 238, 6201, 354},
        {7379, 659, 7854, 795},
        {6863, 907, 6991, 1079},
        {4278, 1896, 4390, 2003},
        {5976, 4359, 6102, 4531},
        {4864, 4937, 4986, 5078},
        {6721, 5966, 6856, 6104},
        {5242, 6606, 5361, 6739},
        {4518, 7738, 7657, 7899},
	},
    [41] = { --Two Loops
        {2271, 1470, 2527, 1576},
        {5197, 1006, 5808, 1111},
        {4316, 539, 4702, 648},
        {2917, 864, 3079, 992},
        {1178, 1529, 1787, 1661},
    },
	[43] = { --Hamster
        {430, 41, 3603, 216},
        {4703, 1134, 4957, 1234},
        {2859, 1325, 4081, 1817},
        {5453, 2274, 6600, 2427},
        {3160, 3966, 4208, 4398},
        {5027, 4707, 6617, 4818},
        {968, 4846, 7127, 6859},
	},
	[44] = { --To and Fro'
        {3984, 2526, 4246, 2643},
        {3994, 2391, 4354, 2553},
        {769, 1978, 1314, 2178},
        {321, 2214, 1363, 2336},
        {1859, 2335, 3056, 2626},
	},
}

brakeAreas = {
    [10] = { --Looper
        {2100, 9510, 2300, 9540}
    },
    [24] = { --Short Cut
        {4500, 920, 4600, 1090}
    },
    [31] = { --Crock
        {12900, 2320, 13200, 2100}
    },
	[15] = { --Last One
	    {12823, 360, 13025, 572},
	},
	[43] = { --Hamster
        {3508, 2715, 3551, 2896},
	},
}

noStuntAreas = {
	[44] = { --To and Fro'
        {4208, 2461, 4395, 2589},
	},
}

RAM = {
	[1] = {
		words = {
			xSpeed = 0x7E04B7,
			ySpeed = 0x7E04BB,
			yPos = 0x7E0415,
			xPos = 0x7E0411,
			countdownTimer = 0x7E11BA,
		},

		bytes = {
			facedDirection = 0x7E0BA1, -- 1 is right, 0 is left
			airValue = 0x7E0547,
			showingArrows = 0x7E0FCE, -- 0 is arrows showing, -1 is not
			arrowDirection = 0x7E0FCD, --0 is right, 1 is left
			currentTrack = 0x7E00CE,
			inRace = 0x7E0313,
			reverseControls = 0x7E132B, -- 2 is reversed, 0 is normal
			pitch = 0x7E04C9,
			tabletops = 0x7E0431,
			airValue = 0x7E0545,
			showingArrows = 0x7E0FCC, -- 0 is arrows showing, -1 is not
			arrowDirection = 0x7E0FCB, --0 is right, 1 is left
			currentTrack = 0x7E00CE,
			inRace = 0x7E0313,
			reverseControls = 0x7E132B, -- 2 is reversed, 0 is normal
			pitch = 0x7E0F49,
			tabletops = 0x7E042F,
			currentMenu = 0x7E009F,
			playerInput = 0x700743, -- 1 is both players, 5 is player one, 3 is player 2
			menuSelectedRow = 0x7E000E,
			menuSelectedCol = 0x7E0C63, -- 6 is left, 7 is right
			selectedOption  = 0x7E009B, -- 0 is 1P, in tours, 0 is crawler, 1 is jumper, etc. 9 is hunter
			crawlerTour = 0x7E0A03,
			shufflerTour = 0x7E0A0B,
			walkerTour = 0x7E0A13,
			hopperTour = 0x7E0A1B,
			jumperTour = 0x7E0A07,
			bounderTour = 0x7E0A0F,
			runnerTour = 0x7E0A17,
			sprinterTour = 0x7E0A1F,
			hunterTour = 0x7E0A23,
		}
	},
	[2] = {
		words = {
			xSpeed = 0x7E04B9,
			ySpeed = 0x7E04BD,
			yPos = 0x7E0417,
			xPos = 0x7E0413,
			countdownTimer = 0x7E11BA,
		},

		bytes = {
			facedDirection = 0x7E0BA3, -- 1 is right, 0 is left
			airValue = 0x7E0547,
			showingArrows = 0x7E0FCE, -- 0 is arrows showing, -1 is not
			arrowDirection = 0x7E0FCD, --0 is right, 1 is left
			currentTrack = 0x7E00CE,
			inRace = 0x7E0313,
			reverseControls = 0x7E132B, -- 2 is reversed, 0 is normal
			pitch = 0x7E04C9,
			tabletops = 0x7E0431,
			currentMenu = 0x7E009F,
			playerInput = 0x700743, -- 1 is both players, 5 is player one, 3 is player 2
			menuSelectedRow = 0x7E000E,
			menuSelectedCol = 0x7E0C63, -- 6 is left, 7 is right
		}
	},
}

direction = {
    up = 1,
    right = 1,
    down = -1,
    left = -1,
    none = 0,
}

menu = {
	demo = 0,
	splash = 132,
	mainMenu = 215,
	onePlayerSelect = 60,
	twoPlayerSelect = 61,
	vsSelect = 62,
	vsChallenger = 63,
	vsChallengeTrack = 90,
	onePlayerTours1 = 109,
	onePlayerTours2 = 16,
	onePlayerTracks = 246,
	onePlayerNowPlaying = 22,
	twoPlayerTours = 16,
	twoPlayerTracksLow = 145,
	twoPlayerTracksHigh = 150,
	raceResults = 153,
	circuitResults = 188,
	stuntResults = 24,
	stuntResultsSumming1 = 47,
	stuntResultsSumming2 = 173,
	stuntResultsSumming3 = 175,
	stuntResultsSumming4 = 179,
	stuntResultsSumming5 = 211,
	stuntResultsSumming6 = 216,
	stuntResultsSumming7 = 237,
	stuntResultsSumming8 = 243,
	ending = 91,
}

decisionState = {
    directionToGo = direction.none,
    rotationDirection = direction.none,
    shouldJump = false,
    shouldBrake = false,
    shouldZee = false,
    tabletopValue = 0,
}

lastMenuInput = {
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
        R = nil,
    }

needNewPlayer = false
	
function Run()
    while(true) do
        local inRace = memory.readbyte(RAM[controller].bytes.inRace)

        if inRace == 1 then
            airValue = memory.readbyte(RAM[controller].bytes.airValue)
            currentTrack = memory.readbyte(RAM[controller].bytes.currentTrack)
            xSpeed = memory.readword(RAM[controller].words.xSpeed)
            xSpeed = MakeWordSigned(xSpeed)

			decisionState.rotationDirection = GetRotationDirection()
            decisionState.shouldJump = ShouldJump()
            decisionState.shouldBrake = ShouldBrake()
            decisionState.shouldZee = ShouldZee()
            decisionState.directionToGo = GetDirectionToGo()

            SendInput()
            emu.frameadvance()
        else
            SendMenuInput()
            emu.frameadvance()
        end
    end
end

function SendMenuInput()
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
        R = nil,
    }

	if singlePlayer then
		controller = 1
		local currentMenu = memory.readbyte(RAM[controller].bytes.currentMenu)
		local framecount = snes9x.framecount()
		
		if currentMenu == menu.mainMenu then
			if memory.readbyte(RAM[controller].bytes.selectedOption) > 0 then
				if lastMenuInput.up == nil then
					buttonTable.up = true
				end
			else
				if lastMenuInput.A == nil then
					buttonTable.A = true
				end
			end
		elseif currentMenu == menu.onePlayerSelect then
			needNewPlayer = true
			if memory.readbyte(RAM[controller].bytes.menuSelectedCol) < targetPlayerCol then
				buttonTable.right = true
			elseif memory.readbyte(RAM[controller].bytes.menuSelectedCol) > targetPlayerCol then
				buttonTable.left = true
			else
				local menuSelectedRow = memory.readbyte(RAM[controller].bytes.menuSelectedRow)
				if menuSelectedRow < targetPlayerRow then
					if lastMenuInput.down == nil then
						buttonTable.down = true
					end
				end
				if menuSelectedRow > targetPlayerRow then
					if lastMenuInput.up == nil then
						buttonTable.up = true
					end
				end
				if menuSelectedRow == targetPlayerRow then
					if lastMenuInput.A == nil then
						buttonTable.A = true
					end
				end
			end
		elseif currentMenu == menu.onePlayerTours1 or currentMenu == menu.onePlayerTours2 then
			local targetTour = -1
			
			if memory.readbyte(RAM[controller].bytes.hunterTour) < targetMedal and targetMedal > 19 then
				targetTour = 9
			end
			if memory.readbyte(RAM[controller].bytes.sprinterTour) < targetMedal and targetMedal > 17 then
				targetTour = 7
			end
			if memory.readbyte(RAM[controller].bytes.runnerTour) < targetMedal and targetMedal > 17 then
				targetTour = 5
			end
			if memory.readbyte(RAM[controller].bytes.bounderTour) < targetMedal then
				targetTour = 3
			end
			if memory.readbyte(RAM[controller].bytes.jumperTour) < targetMedal then
				targetTour = 1
			end
			if memory.readbyte(RAM[controller].bytes.crawlerTour) < targetMedal then
				targetTour = 0
			end
			if memory.readbyte(RAM[controller].bytes.shufflerTour) < targetMedal then
				targetTour = 2
			end
			if memory.readbyte(RAM[controller].bytes.walkerTour) < targetMedal then
				targetTour = 4
			end
			if memory.readbyte(RAM[controller].bytes.hopperTour) < targetMedal then
				targetTour = 6
			end
			if targetTour == -1 then
				--snes9x.pause()
				if needNewPlayer then
					if targetPlayerCol % 2 == 1 then
						targetPlayerCol = ((targetPlayerCol + 1) % 2) + 6
						targetPlayerRow = (targetPlayerRow + 1) % 8					
					else
						targetPlayerCol = ((targetPlayerCol + 1) % 2) + 6
					end
					needNewPlayer = false
				end
				buttonTable.X = true
			end
			
			local targetCol = targetTour % 2
			local targetRow = targetTour - targetCol
			local selectedOption = memory.readbyte(RAM[controller].bytes.selectedOption)
			
			if targetRow < selectedOption - 1 then
				if lastMenuInput.up == nil then
					buttonTable.up = true
				end
			elseif targetRow > selectedOption then
				if lastMenuInput.down == nil then
					buttonTable.down = true
				end
			elseif targetTour % 2 == 0 and selectedOption % 2 == 1 then
				if lastMenuInput.left == nil then
					buttonTable.left = true
				end
			elseif targetTour % 2 == 1 and selectedOption % 2 == 0 then
				if lastMenuInput.right == nil then
					buttonTable.right = true
				end
			else
				if lastMenuInput.A == nil then
					buttonTable.A = true
				end
			end
		elseif currentMenu == menu.onePlayerTracks then
			if lastMenuInput.A == nil then
				buttonTable.A = true
			end
		elseif currentMenu == menu.onePlayerNowPlaying then
			if lastMenuInput.A == nil then
				buttonTable.A = true
			end
		elseif currentMenu == menu.raceResults then
			if math.floor(framecount / 2) % 2 == 0 then
				buttonTable.A = true
			end
		elseif currentMenu == menu.circuitResults then
			if math.floor(framecount / 2) % 2 == 0 then
				buttonTable.A = true
			end
		elseif currentMenu == menu.stuntResults then
			if math.floor(framecount / 2) % 2 == 0 then
				buttonTable.A = true
			end
		elseif currentMenu == menu.ending then
			if math.floor(framecount / 2) % 2 == 0 then
				buttonTable.A = true
			end
		elseif currentMenu == menu.stuntResultsSumming1 then
			buttonTable.start = true
		elseif currentMenu == menu.stuntResultsSumming2 then
			buttonTable.start = true
		elseif currentMenu == menu.stuntResultsSumming3 then
			buttonTable.start = true
		elseif currentMenu == menu.stuntResultsSumming4 then
			buttonTable.start = true
		elseif currentMenu == menu.stuntResultsSumming5 then
			buttonTable.start = true
		elseif currentMenu == menu.stuntResultsSumming6 then
			buttonTable.start = true
		elseif currentMenu == menu.stuntResultsSumming7 then
			buttonTable.start = true
		elseif currentMenu == menu.stuntResultsSumming8 then
			buttonTable.start = true
		end
	else
		local currentMenu = memory.readbyte(RAM[controller].bytes.currentMenu)
		local playerInput = memory.readbyte(RAM[controller].bytes.playerInput)
		
		if (currentMenu == menu.twoPlayerSelect or currentMenu == menu.vsSelect or currentMenu == menu.vsChallenger) and (playerInput == 7 - controller * 2) then
			if memory.readbyte(RAM[controller].bytes.menuSelectedCol) < targetPlayerCol then
				buttonTable.right = true
			elseif memory.readbyte(RAM[controller].bytes.menuSelectedCol) > targetPlayerCol then
				buttonTable.left = true
			else
				local menuSelectedRow = memory.readbyte(RAM[controller].bytes.menuSelectedRow)
				if menuSelectedRow < targetPlayerRow then
					if lastMenuInput.down == nil then
						buttonTable.down = true
					end
				end
				if menuSelectedRow > targetPlayerRow then
					if lastMenuInput.up == nil then
						buttonTable.up = true
					end
				end
				if menuSelectedRow == targetPlayerRow then
					if lastMenuInput.A == true then
						if playerInput == 3 then
							buttonTable.X = true
						end
					else
						buttonTable.A = true
					end
				end
			end
		elseif (playerInput == 7 - controller * 2) then
			if lastMenuInput.A == nil then
				buttonTable.A = true
			end
		end
	end
	
    joypad.set(controller, buttonTable)
	lastMenuInput = buttonTable
end

function MakeWordSigned(word)
    if word > 32768 then
        word = word - 65536
    end

    return word
end

function ShouldZee()
	if InNoStuntArea() then
		return false
	end

    if currentTrack == 0 then
        return false
    end

	local tabletops = memory.readbyte(RAM[controller].bytes.tabletops)
    local targetTabletopValue = 3

    if (currentTrack + 3) % 5 == 0 then
        targetTabletopValue = 8
    end

    if airValue < 9 then
        decisionState.tabletopValue = 0
    end

    if (tabletops == 0 or tabletops >= targetTabletopValue) and airValue == 9 then
        if (decisionState.tabletopValue == 0 and (tabletops == 0 or targetTabletopValue == 8)) then
            decisionState.tabletopValue = 3
        elseif (decisionState.tabletopValue == 0 and tabletops >= targetTabletopValue) then
            decisionState.tabletopValue = 9
        end

        decisionState.tabletopValue = decisionState.tabletopValue - 1

        if (decisionState.tabletopValue > 0) then
            return true
        else
            if tabletops > 2 then
                decisionState.tabletopValue = -1
            end

            return false
        end
    end

    return false
end

function ShouldBrake()
    local countdownTimer = memory.readword(RAM[controller].words.countdownTimer)

    if 24832 < countdownTimer and countdownTimer <= 40448 then
        return true
    end

    if (InBrakeArea() and math.abs(xSpeed) >= 300) then
        return true
    end

    return false
end

function InNoStuntArea()
    if noStuntAreas[currentTrack] ~= nil then
        local xPos = memory.readword(RAM[controller].words.xPos)
        local yPos = memory.readword(RAM[controller].words.yPos)

        for noStuntArea in values(noStuntAreas[currentTrack]) do
            if PointInRectangle(xPos, yPos, noStuntArea) then
                return true
            end
        end
    end

    return false
end


function InBrakeArea()
    if brakeAreas[currentTrack] ~= nil then
        local xPos = memory.readword(RAM[controller].words.xPos)
        local yPos = memory.readword(RAM[controller].words.yPos)

        for brakeArea in values(brakeAreas[currentTrack]) do
            if PointInRectangle(xPos, yPos, brakeArea) then
                return true
            end
        end
    end

    return false
end


function GetRotationDirection()
    local pitch = memory.readbyte(RAM[controller].bytes.pitch)

    if pitch <= 14 or pitch >= 50 then
        return direction.none
    elseif CurrentDirectionFromSpeed() == direction.left and pitch <= 40 then
        return direction.left
	elseif CurrentDirectionFromSpeed() == direction.right and pitch <= 24 then
		return direction.left
	elseif CurrentDirectionFromSpeed() == direction.none and pitch <= 32 then
		return direction.left
    else
        return direction.right
    end

end

function ShouldJump()
    local ySpeed = memory.readword(RAM[controller].words.ySpeed)

    ySpeed = MakeWordSigned(ySpeed)

    if ySpeed > 0 and airValue > 0 then
        return false
    end

    if (currentTrack + 3) % 5 == 0 then
        return true
    end

    if airValue == 9 then
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
    local currentTrack = memory.readbyte(RAM[controller].bytes.currentTrack)

    if jumpAreas[currentTrack] ~= nil then
        local xPos = memory.readword(RAM[controller].words.xPos)
        local yPos = memory.readword(RAM[controller].words.yPos)

        for jumpArea in values(jumpAreas[currentTrack]) do
            if PointInRectangle(xPos, yPos, jumpArea) then
                return true
            end
        end
    end

    return false
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

function GetDirectionToGo()
    if (currentTrack + 3) % 5 == 0 then
		return direction.none
    end

    local retVal = CurrentDirectionFromArrows()

    if retVal == direction.none then
        retVal = CurrentDirectionFromSpeed()
    end

    if retVal == direction.none then
        retVal = CurrentDirectionFromFacing()
    end

    if currentTrack == 0 and decisionState.shouldJump and airValue == 0 then
        retVal = direction.left
    end

    return retVal
end

function CurrentDirectionFromArrows()
    local showingArrows = memory.readbyte(RAM[controller].bytes.showingArrows)

    if showingArrows ~= 0 then
        return direction.none
    end

    local arrowDirection = memory.readbyte(RAM[controller].bytes.arrowDirection)

    if arrowDirection == 0 then
        return direction.right
    elseif arrowDirection == 1 then
        return direction.left
    end
end

function CurrentDirectionFromFacing()
    local facedDirection = memory.readbyte(RAM[controller].bytes.facedDirection)

    if facedDirection == 1 then
        return direction.right
    elseif facedDirection == 0 then
        return direction.left
    end
end

function CurrentDirectionFromSpeed()
    --for very small values of xSpeed, defer to facing instead
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
    if decisionState.rotationDirection == direction.right or currentTrack == 0 then
        buttonTable.R = true
    end
    if decisionState.rotationDirection == direction.left and currentTrack ~= 0 then
        buttonTable.L = true
    end
    buttonTable.B = decisionState.shouldJump
    buttonTable.Y = decisionState.shouldBrake
    buttonTable.X = decisionState.shouldZee

    joypad.set(controller, buttonTable)
end

function CheckForReverseControls()
    local reverseControls = memory.readbyte(RAM[controller].bytes.reverseControls)

    if reverseControls == 2 then
        decisionState.directionToGo = decisionState.directionToGo * -1
        decisionState.rotationDirection = decisionState.rotationDirection * -1
    end
end

--snes9x.speedmode("nothrottle")
Run()
