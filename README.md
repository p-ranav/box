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
