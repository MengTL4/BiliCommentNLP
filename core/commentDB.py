from pymongo import MongoClient


class MongoDBMix:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client["bilibili"]

    def insert_main_comments(self, rpids_main):
        try:
            # 检查列表是否为空
            if not rpids_main:
                print("主评论列表为空，跳过插入")
                return
                
            result = self.db['main_comments'].insert_many(rpids_main)
            print(f"成功插入 {len(result.inserted_ids)} 条主评论")
        except Exception as e:
            print(f"主评论插入失败: {e}")

    def insert_sub_comments(self, rpids_sub):
        try:
            # 检查列表是否为空
            if not rpids_sub:
                print("子评论列表为空，跳过插入")
                return
                
            result = self.db['sub_comments'].insert_many(rpids_sub)
            print(f"成功插入 {len(result.inserted_ids)} 条子评论")
        except Exception as e:
            print(f"子评论插入失败: {e}")

    def get_main_comments_from_db(self):
        """
        从指定的集合中获取所有 comment 字段的内容
        :return: 包含 comment 字段值的列表
        """
        try:
            collection = self.db["main_comments"]
            comments = [doc.get('content') for doc in collection.find({}, {'content': 1})]
            print(f"成功提取 {len(comments)} 条评论")
            return comments
        except Exception as e:
            print(f"提取评论失败: {e}")
            return []

    def get_sub_comments_from_db(self):
        """
        从指定的集合中获取所有 comment 字段的内容
        :return: 包含 comment 字段值的列表
        """
        try:
            collection = self.db["sub_comments"]
            comments = [doc.get('content') for doc in collection.find({}, {'content': 1})]
            print(f"成功提取 {len(comments)} 条评论")
            return comments
        except Exception as e:
            print(f"提取评论失败: {e}")
            return []

    def update_main_comment_with_result(self, content, result):
        """
        根据 content 字段更新对应文档，添加 result 字段
        :param content: 要匹配的评论内容（对应数据库中的 content 字段）
        :param result: 要添加或更新的 result 字段的值
        :return: 更新结果信息
        """
        if len(result['result'][0]) != 0:
            try:
                collection = self.db['main_comments']  # 如果需要更新 sub_comments，改为 self.db['sub_comments']
                # 更新匹配的第一个文档，添加或更新 result 字段
                update_result = collection.update_one(
                    {'content': content},  # 查询条件
                    {'$set': {
                        'result': result['result'][0]['情感倾向[正向,负向,未提及]'][0]['text'],
                        'probability': result['result'][0]['情感倾向[正向,负向,未提及]'][0]['probability']}}  # 更新操作
                )

                if update_result.matched_count > 0:
                    print(f"成功更新 {update_result.modified_count} 条文档，匹配内容为: '{content}'")
                else:
                    print(f"未找到匹配内容为 '{content}' 的文档")
            except Exception as e:
                print(f"更新评论失败: {e}")
        else:
            print(f"nlp服务未能判断情感倾向")

    def update_sub_comment_with_result(self, content, result):
        """
        根据 content 字段更新对应文档，添加 result 字段
        :param content: 要匹配的评论内容（对应数据库中的 content 字段）
        :param result: 要添加或更新的 result 字段的值
        :return: 更新结果信息
        """
        if len(result['result'][0]) != 0:
            try:
                collection = self.db['sub_comments']  # 如果需要更新 sub_comments，改为 self.db['sub_comments']
                # 更新匹配的第一个文档，添加或更新 result 字段
                update_result = collection.update_one(
                    {'content': content},  # 查询条件
                    {'$set': {
                        'result': result['result'][0]['情感倾向[正向,负向,未提及]'][0]['text'],
                        'probability': result['result'][0]['情感倾向[正向,负向,未提及]'][0]['probability']}}  # 更新操作
                )

                if update_result.matched_count > 0:
                    print(f"成功更新 {update_result.modified_count} 条文档，匹配内容为: '{content}'")
                else:
                    print(f"未找到匹配内容为 '{content}' 的文档")
            except Exception as e:
                print(f"更新评论失败: {e}")
        else:
            print(f"nlp服务未能判断情感倾向")