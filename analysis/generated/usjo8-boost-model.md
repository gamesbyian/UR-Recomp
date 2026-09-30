# USJO v8 historical boost model

This is a structured extraction of what the recovered 2008 optimizer assumes.
It is not a claim that these are the game's true boost units until reproduced locally.

| Stunt counter | Condition | Added boost score | Source lines |
|---|---:|---:|---:|
| twists | >= 8 | 200 | 947-948 |
| twists | >= 6 | 176 | 949-950 |
| twists | >= 4 | 152 | 951-952 |
| twists | >= 2 | 128 | 953-954 |
| tabletops | >= 1 | 152 | 956-957 |
| zflips | == 1 | 128 | 959-960 |
| zflips | == 2 | 152 | 961-962 |
| zflips | == 3 | 176 | 963-964 |
| zflips | >= 4 | 200 | 965-966 |
| rolls | == 1 | 128 | 968-969 |
| rolls | == 2 | 152 | 970-971 |
| rolls | == 3 | 176 | 972-973 |
| rolls | >= 4 | 200 | 974-975 |
| flips | == 1 | 176 | 977-978 |
| flips | == 2 | 200 | 979-980 |
| flips | == 3 | 224 | 981-982 |
| flips | >= 4 | 248 | 983-984 |

The optimizer sums the applicable stunt reward contributions, then zeros the derived
boost score if horizontal progress is negative or if the runtime byte it calls
`realboostmeter` is zero. Its candidate score is derived boost plus horizontal speed.
