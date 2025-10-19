import os
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register("helloworld", "YourName", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 获取插件目录的路径
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))

    def create_waterlist(self):
        waterlist = []
        try:
            # 使用绝对路径
            id_file_path = os.path.join(self.plugin_dir, 'waterlist_id.txt')
            count_file_path = os.path.join(self.plugin_dir, 'waterlist_count.txt')
            
            logger.info(f"尝试读取文件: {id_file_path}")
            
            with open(id_file_path, 'r', encoding='utf-8') as f:
                line_msg = f.readline()
                while line_msg:
                    if line_msg.strip():  # 跳过空行
                        waterlist.append({"id": int(line_msg.strip()), "count": 0})
                    line_msg = f.readline()
            
            with open(count_file_path, 'r', encoding='utf-8') as f:
                line_msg = f.readline()
                index = 0
                while line_msg and index < len(waterlist):
                    if line_msg.strip():  # 跳过空行
                        waterlist[index]['count'] = int(line_msg.strip())
                        index += 1
                    line_msg = f.readline()
                    
            logger.info(f"成功加载水井数据: {len(waterlist)} 条记录")
        except FileNotFoundError as e:
            logger.error(f"文件未找到: {e}")
            # 可以在这里创建默认文件或返回空列表
            return []
        except Exception as e:
            logger.error(f"读取水井数据出错: {e}")
            return []
            
        return waterlist
    
    def write_water(self,waterlist) :
        
            # 使用绝对路径
        id_file_path = os.path.join(self.plugin_dir, 'waterlist_id.txt')
        count_file_path = os.path.join(self.plugin_dir, 'waterlist_count.txt')
            
        logger.info(f"尝试读取文件: {id_file_path}")
            
        with open(id_file_path, 'w', encoding='utf-8') as f:
            for id in waterlist :
                f.write(f"{id['id']}\n")
            
        with open(count_file_path, 'r', encoding='utf-8') as f:
            for id in waterlist :
                f.write(f"{id['count']}\n")
                    
        logger.info(f"成功写入水井数据: {len(waterlist)} 条记录")


    async def initialize(self):
        """插件初始化时检查文件是否存在"""
        id_file_path = os.path.join(self.plugin_dir, 'waterlist_id.txt')
        count_file_path = os.path.join(self.plugin_dir, 'waterlist_count.txt')
        
        if not os.path.exists(id_file_path):
            logger.warning(f"水井ID文件不存在: {id_file_path}")
        if not os.path.exists(count_file_path):
            logger.warning(f"水井计数文件不存在: {count_file_path}")

    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        """这是一个 hello world 指令"""
        user_name = event.get_sender_name()
        message_str = event.message_str
        message_chain = event.get_messages()
        logger.info(message_chain)
        yield event.plain_result(f"Hello, {user_name}, 你发了 {message_str}!")

    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    async def on_private_message(self, event: AstrMessageEvent):
        message_str = event.message_str
        yield event.plain_result(f"你说的对，但是你为什么要给我私聊发消息，我这个功能还不知道写什么阿巴阿巴（这样吧我告诉你一个命令，你刚才发给我的消息是{message_str}）")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def water_in_group(self, event: AstrMessageEvent):
        """打水功能"""
        message_str = event.message_str.strip()
        group_id = event.get_group_id()
        
        # 修正条件判断
        if message_str == '打水' and group_id == "1012575925":  # 使用正确的群号
            try:
                waterlist = self.create_waterlist()
                if not waterlist:
                    yield event.plain_result("水井数据为空，无法打水")
                    return
                sender_count = 0
                flag = 0
                for user in waterlist :
                    if user['id'] == event.get_sender_id() :
                        user['count']+=1
                        sender_count = user['count']
                        flag = 1
                        break

                if flag == 0:
                    waterlist.append({"id":event.get_sender_id,"count":1})
                    sender_count = 1
                
                logger.info(f"打水成功，群组: {group_id}")
                self.write_water(waterlist)
                yield event.plain_result(f"打水成功！,你总计打水{sender_count}次。")
            except Exception as e:
                logger.error(f"打水操作出错: {e}")
                yield event.plain_result("打水失败，请稍后重试")
        else:
            logger.debug(f"未触发打水命令，消息: '{message_str}'，群组: {group_id}")

    async def terminate(self):
        """插件销毁方法"""