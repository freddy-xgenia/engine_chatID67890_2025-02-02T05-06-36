import random


mod = 2**32


def mix(a, b, c, d, e, f, g, h):
    a ^= 0xFFFFFFFF & b << 11
    d = (d + a) % mod
    b = (b + c) % mod
    b ^= 0x3FFFFFFF & (c >> 2)
    e = (e + b) % mod
    c = (c + d) % mod
    c ^= 0xFFFFFFFF & d << 8
    f = (f + c) % mod
    d = (d + e) % mod
    d ^= e >> 16
    g = (g + d) % mod
    e = (e + f) % mod
    e ^= 0xFFFFFFFF & f << 10
    h = (h + e) % mod
    f = (f + g) % mod
    f ^= 0x0FFFFFFF & (g >> 4)
    a = (a + f) % mod
    g = (g + h) % mod
    g ^= 0xFFFFFFFF & h << 8
    b = (b + g) % mod
    h = (h + a) % mod
    h ^= 0x007FFFFF & (a >> 9)
    c = (c + h) % mod
    a = (a + b) % mod
    return a, b, c, d, e, f, g, h


class Isaac:
    def __init__(
        self,
        state_manager,
        dummy_icon=0,
    ):
        self.state_manager = state_manager
        self.mm = [0] * 256
        self.randrsl = [random.getrandbits(32) for _ in range(256)]
        # self.randrsl = [0] * 256  # FIXME: this is only for testing. Delete this line and uncomment previous line.
        # self.randcnt = 0
        self.aa = 0
        self.bb = 0
        self.cc = 0
        self.blocked_icon = state_manager.get("blocked_icons") 
        self.dummy_icon = dummy_icon

        self.__randinit__(True)

    def rand(self, mod=2**32, reel_idx=0, icon=0):
        # print("state_manager in isaac : ", self.state_manager.get_full_state())
        reel_idx-=1

        if self.randcnt == 256:
            self.__isaac__()
            self.randcnt = 0
        symbol = self.randrsl[self.randcnt] % mod
        self.randcnt += 1

        symbol += 1

        # if (
        #     icon is not None
        #     and icon in self.blocked_icon.values()
        # ):
        #     print("masok")
        #     return self.dummy_icon

        return symbol 

    def __isaac__(self):
        self.cc += 1
        self.bb += self.cc
        self.bb &= 0xFFFFFFFF

        for i in range(256):
            x = self.mm[i]
            switch = i % 4
            xorwith = None
            if switch == 0:
                xorwith = (self.aa << 13) % mod
            elif switch == 1:
                xorwith = self.aa >> 6
            elif switch == 2:
                xorwith = (self.aa << 2) % mod
            elif switch == 3:
                xorwith = self.aa >> 16
            else:
                raise Exception("math is broken")
            self.aa = self.aa ^ xorwith
            self.aa = (self.mm[(i + 128) % 256] + self.aa) % mod
            y = self.mm[i] = (self.mm[(x >> 2) % 256] + self.aa + self.bb) % mod
            self.randrsl[i] = self.bb = (self.mm[(y >> 10) % 256] + x) % mod

    def __randinit__(self, flag):
        a = b = c = d = e = f = g = h = 0x9E3779B9
        self.aa = self.bb = self.cc = 0

        for x in range(4):
            a, b, c, d, e, f, g, h = mix(a, b, c, d, e, f, g, h)

        i = 0
        while i < 256:
            if flag:
                a = (a + self.randrsl[i]) % mod
                b = (b + self.randrsl[i + 1]) % mod
                c = (c + self.randrsl[i + 2]) % mod
                d = (d + self.randrsl[i + 3]) % mod
                e = (e + self.randrsl[i + 4]) % mod
                f = (f + self.randrsl[i + 5]) % mod
                g = (g + self.randrsl[i + 6]) % mod
                h = (h + self.randrsl[i + 7]) % mod

            a, b, c, d, e, f, g, h = mix(a, b, c, d, e, f, g, h)
            self.mm[i : i + 7 + 1] = a, b, c, d, e, f, g, h
            i += 8

        if flag:
            i = 0
            while i < 256:
                a = (a + self.mm[i]) % mod
                b = (b + self.mm[i + 1]) % mod
                c = (c + self.mm[i + 2]) % mod
                d = (d + self.mm[i + 3]) % mod
                e = (e + self.mm[i + 4]) % mod
                f = (f + self.mm[i + 5]) % mod
                g = (g + self.mm[i + 6]) % mod
                h = (h + self.mm[i + 7]) % mod
                a ^= 0xFFFFFFFF & b << 11
                d = (d + a) % mod
                b = (b + c) % mod
                b ^= 0x3FFFFFFF & (c >> 2)
                e = (e + b) % mod
                c = (c + d) % mod
                c ^= 0xFFFFFFFF & d << 8
                f = (f + c) % mod
                d = (d + e) % mod
                d ^= e >> 16
                g = (g + d) % mod
                e = (e + f) % mod
                e ^= 0xFFFFFFFF & f << 10
                h = (h + e) % mod
                f = (f + g) % mod
                f ^= 0x0FFFFFFF & (g >> 4)
                a = (a + f) % mod
                g = (g + h) % mod
                g ^= 0xFFFFFFFF & h << 8
                b = (b + g) % mod
                h = (h + a) % mod
                h ^= 0x007FFFFF & (a >> 9)
                c = (c + h) % mod
                a = (a + b) % mod
                self.mm[i : i + 7 + 1] = a, b, c, d, e, f, g, h
                i += 8
        self.__isaac__()
        self.randcnt = 256
