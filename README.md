<p align="center">
  <img height="90" src="https://user-images.githubusercontent.com/8450091/123720914-cb9a5200-d84a-11eb-97d9-830776297b87.PNG"/>  
</p>

`Box` is a text-based visual programming language inspired by Unreal Engine blueprint function graphs.

```console
$ cat factorial.box

 ┌─ƒ(Factorial)───┐                     ┌─[Branch]─────┐                       ┌─[Set]─┐
 │               ►┼─────────────────────┼►       True ►┼───────────────────────┼►     ►┼─────────┐         ┌─[For Loop]───────────┐                   ┌───────┐
 │             n ○┼──┐               ┌──┼○      False ►┼──┐  ┌──────────┐  ┌───┼○      │         └─────────┼►          Loop body ►┼───────────────────┼►      │
 └────────────────┘  │    ┌────────┐ │  │              │  │  │  result ○┼──┘ ┌─┼○      │                   │                      │ ┌──────────┐ ┌────┼○  *=  │
             ┌────┐  └────┼○  >=  ○┼─┘  └──────────────┘  │  └──────────┘    │ └───────┘         ┌────┐    │                      │ │  result ○┼─┘  ┌─┼○      │
             │ 1 ○┼───────┼○       │                      │       ┌────┐     │                   │ 1 ○┼────┼○ start               │ └──────────┘    │ └───────┘
             └────┘       └────────┘                      │       │ 1 ○┼─────┘                   └────┘    │                      │                 │
                                                          │       └────┘                                   │               index ○┼─────────────────┘
                                                          │                        ┌────┐                  │                      │
                                                          │                        │ n ○┼─┐  ┌───────┐     │                      │
                                                          │                        └────┘ └──┼○  +   │     │                      │
                                                          │                        ┌────┐ ┌──┼○     ○┼─────┼○ end                 │
                                                          │                        │ 1 ○┼─┘  └───────┘     │                      │
                                                          │                        └────┘                  │                      │
                                                          │                                      ┌────┐    │                      │
                                                          │   ┌─[Return]─┐                       │ 1 ○┼────┼○ step                │
                                                   ┌────┐ └───┼►         │                       └────┘    │           Completed ►┼────┐
                                                   │ 1 ○┼─────┼○         │                                 └──────────────────────┘    │  ┌─[Return]─┐
                                                   └────┘     └──────────┘                                               ┌─────────┐   └──┼►         │
                                                                                                                         │ result ○┼──────┼○         │
                                                                                                                         └─────────┘      └──────────┘
$ box factorial.box -e 5
120

$ box factorial.box -e 5
87178291200

$ box factorial.box -o factorial.py

$ cat factorial.py
def Factorial(n):
    if (n >= 1):
        result = 1
        for index_8b6ee4f2 in range(1, (n + 1), 1):
            result *= index_8b6ee4f2
        return result
    else:
        return 1
```

### Getting Started

Install the box interpreter with `pip`

```console
pip3 install box
```

Now open your text editor and start drawing your program! Check out existing samples [here](https://github.com/p-ranav/box/tree/main/samples). 

### Anatomy of a Box

A Box has 2 types of ports: control flow ports (`─►┼─`) and data flow ports (`─○┼─`). These ports can additionally be classified as input or output ports. All ports to the left side of a box are input ports and all ports on the right side of the box are output ports. 

Below, you can see a `[For Loop]` box which is a special type of box that the interpreter can parse - It has 1 input control flow port, 3 input data flow ports (start, end, and step), 2 output control flow ports (the loop body and completed control flows), and 1 output data flow port (the index)

```

        ┌─[For Loop]───────────┐     
    ────┼►          Loop body ►┼────
        │                      │
        │                      │
    ────┼○ start               │
        │                      │
        │               index ○┼────
        │                      │
        │                      │
        │                      │
    ────┼○ end                 │
        │                      │
        │                      │
        │                      │
    ────┼○ step                │
        │           Completed ►┼────
        └──────────────────────┘    
```

### Function Graphs

`Box` programs are function graphs. Functions have a single entry point designated by a node with the name of the Function containing a single output control flow port. 

Here's a simple hello world example. This example declares a `Greet()` function that prints the string "Hello, World!" to the console. It calls the built-in print function.

```
 ┌─ƒ(Greet)───┐                            ┌─ƒ(print)──┐
 │           ►┼────────────────────────────┼►          │
 └────────────┘    ┌──────────────────┐    │           │
                   │ "Hello, World!" ○┼────┼○          │
                   └──────────────────┘    └───────────┘
```

Execute the above program with the box interpreter like so:

```console
$ box samples/hello_world.box -e
Hello,World!
```

### Gotchas

* The interpreter will likely fail if you have tabs in your file - replace all tabs with the appropriate number of spaces
