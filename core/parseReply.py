def extract_comments_data(comments, response):
    # 遍历主评论
    for reply in response.get('replies', []):
        member = reply.get('member', {})
        content = reply.get('content', {})

        # 提取主评论信息
        comments.append({
            "username": member.get('uname', ''),
            "uid": member.get('mid', ''),
            "sex": member.get('sex', ''),
            "comment": content.get('message', '')
        })

        # 遍历子评论（如果有）
        sub_replies = reply.get('replies', []) or []
        for sub_reply in sub_replies:
            sub_member = sub_reply.get('member', {})
            sub_content = sub_reply.get('content', {})

            comments.append({
                "username": sub_member.get('uname', ''),
                "uid": sub_member.get('mid', ''),
                "sex": sub_member.get('sex', ''),
                "comment": sub_content.get('message', '')
            })

    return comments


def extract_comments(comment, replies):
    """
    递归提取评论内容，处理多级评论
    """
    for content in replies:
        # 添加当前评论
        comment.append(content["content"]["message"])
        # 如果有嵌套的子评论，递归提取
        if "replies" in content and content["replies"]:
            extract_comments(comment, content["replies"])
def parse_comment_item(item):
    """解析单条评论"""
    member = item.get('member', {})
    content = item.get('content', {})
    reply_control = item.get('reply_control', {})
    return {
        'uname': member.get('uname', ''),
        'sex': member.get('sex', ''),
        'content': content.get('message', ''),
        'rpid': item.get('rpid', 0),
        'oid': item.get('oid', 0),
        'mid': item.get('mid', 0),
        'parent': item.get('parent', 0),
        'ctime': item.get('ctime', 0),
        'like': item.get('like', 0),
        'following': reply_control.get('following', False),
        'current_level': member.get('level_info', {}).get('current_level', 0),
        'pictures': [pic.get('img_src', '') for pic in content.get('pictures', [])],
        'location': reply_control.get('location', '').replace('IP属地：', ''),
        # 递归解析子评论
        'replies': [parse_comment_item(sub) for sub in item.get('replies', [])] if item.get('replies') else []
    }


def parse_comment_response(json_data):
    """解析评论响应"""
    data = json_data.get('data', {})
    comments = []
    # 解析主评论
    for item in data.get('replies', []):
        comments.append(parse_comment_item(item))
    # 解析置顶评论
    for item in data.get('top_replies', []):
        comments.append(parse_comment_item(item))
    return comments

# 假设已经获取到了评论的 JSON 数据
# with open('comment.json', 'r', encoding='utf-8') as f:
#     json_data = json.load(f)
# comments = parse_comment_response(json_data)
# print(json.dumps(comments, ensure_ascii=False, indent=2))
