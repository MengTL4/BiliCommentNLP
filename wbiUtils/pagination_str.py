import json


class PaginationOffsetData:
    def __init__(self, pn: int):
        self.pn = pn


class PaginationOffset:
    def __init__(self, type: int, direction: int, pn: int):
        self.type = type
        self.direction = direction
        self.data = PaginationOffsetData(pn)


def encode_pagination_offset(pagination: PaginationOffset = None) -> str:
    """
    将分页对象编码为 pagination_str
    :param pagination: PaginationOffset 对象，如果为 None 则返回空 offset
    :return: pagination_str 字符串，格式为 {"offset": "{"type":1,"direction":1,"data":{"pn":2}}"} 或 {"offset": ""}
    """
    try:
        if pagination is None:
            return json.dumps({"offset": ""})
        # 首先将 PaginationOffset 对象转换为 JSON 字符串
        inner_json = json.dumps(pagination.__dict__, default=lambda o: o.__dict__)
        # 然后将其包装在 {"offset": ...} 结构中
        outer_dict = {"offset": inner_json}
        return json.dumps(outer_dict)
    except Exception as e:
        print(f"Error marshaling pagination: {e}")
        return json.dumps({"offset": ""})


def decode_pagination_offset(pagination_str: str) -> PaginationOffset:
    """
    将 pagination_str 解码为分页对象
    :param pagination_str: pagination_str 字符串，格式为 {"offset": "{"type":1,"direction":1,"data":{"pn":2}}"} 或 {"offset": ""}
    :return: PaginationOffset 对象，如果 offset 为空则返回 None
    """
    try:
        # 首先解析外层 JSON
        outer_data = json.loads(pagination_str)
        # 如果 offset 为空，返回 None
        if not outer_data["offset"]:
            return None
        # 解析内层 JSON
        inner_data = json.loads(outer_data["offset"])
        return PaginationOffset(
            type=inner_data["type"],
            direction=inner_data["direction"],
            pn=inner_data["data"]["pn"],
        )
    except Exception as e:
        print(f"Error unmarshaling pagination: {e}")
        return None


# 使用示例
if __name__ == "__main__":
    # 测试空 offset 的情况
    empty_pagination_str = encode_pagination_offset()
    print(f"Empty pagination_str: {empty_pagination_str}")

    # 测试解码空 offset
    empty_decoded = decode_pagination_offset(empty_pagination_str)
    print(f"Decoded empty pagination: {empty_decoded}")

    # 测试正常情况
    pagination = PaginationOffset(type=1, direction=1, pn=2)
    pagination_str = encode_pagination_offset(pagination)
    print(f"Normal pagination_str: {pagination_str}")

    decoded_pagination = decode_pagination_offset(pagination_str)
    print(f"Decoded normal pagination: {decoded_pagination.__dict__}")
