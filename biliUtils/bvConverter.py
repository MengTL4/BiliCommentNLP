class BvConverter:
    def __init__(self):
        self.XOR_CODE = 23442827791579
        self.MASK_CODE = 2251799813685247
        self.MAX_AID = 1 << 51
        self.ALPHABET = "FcwAPNKTMug3GV5Lj7EJnHpWsx4tb8haYeviqBz6rkCy12mUSDQX9RdoZf"
        self.ENCODE_MAP = (8, 7, 0, 5, 1, 3, 2, 4, 6)
        self.DECODE_MAP = tuple(reversed(self.ENCODE_MAP))
        self.BASE = len(self.ALPHABET)
        self.PREFIX = "BV1"
        self.PREFIX_LEN = len(self.PREFIX)
        self.CODE_LEN = len(self.ENCODE_MAP)

    def av2bv(self, aid: int) -> str:
        """AID转BV号"""
        bvid = [""] * 9
        tmp = (self.MAX_AID | aid) ^ self.XOR_CODE
        for i in range(self.CODE_LEN):
            bvid[self.ENCODE_MAP[i]] = self.ALPHABET[tmp % self.BASE]
            tmp //= self.BASE
        return self.PREFIX + "".join(bvid)

    def bv2av(self, bvid: str) -> int:
        """BV号转AID"""
        assert bvid[:self.PREFIX_LEN] == self.PREFIX, "无效的BV号格式"

        bvid_part = bvid[self.PREFIX_LEN:]
        tmp = 0
        for i in range(self.CODE_LEN):
            idx = self.ALPHABET.index(bvid_part[self.DECODE_MAP[i]])
            tmp = tmp * self.BASE + idx
        return (tmp & self.MASK_CODE) ^ self.XOR_CODE


# 使用示例
if __name__ == "__main__":
    bvConverter = BvConverter()
    print(bvConverter.bv2av("BV1BfGqzDE59"))