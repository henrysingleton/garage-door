# Garage door opener

Controlling a garage door with a single button input is difficult as its both 
impossible to know the state of the door, or to put it into a known state it
will be entering when pressing the button. 

To work around this, the code herein assumes you've added two hall effect
sensors to the top and bottom of the garage door. Where they are exactly
doesn't matter, they should just be near the top and bottom of the door.

## Diagrams

Open (1,0)
```
 000000000000
|           x| 1
|            | 
|            |
|            |
|            |
|            | 0
```

Closed (0,1)
```
 000000000000
|------------| 0 
|------------| 
|------------|
|------------|
|------------|
|-----------x| 1
```

Opening/Closing (0,0)
```
 000000000000
|------------| 0
|------------|
|-----------x|
|            |
|            |
|            | 0
```

We determine the difference between opening and closing based on the last known
state of the door (opened or closed). While this may be wrong if the 
direction is reversed by external control before it has fully reached either
extent, we can reset the state to a known good once it reaches the 
top or the bottom. e.g.

Closed (0,1) -> Opening (0,0) -> [direction reversed] -> Closed (0,1)

Open (1,0) -> Closing (0,0) -> [direction reversed] -> Open (1,0)
