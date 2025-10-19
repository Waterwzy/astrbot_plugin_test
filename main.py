from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register("helloworld", "YourName", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    def create_waterlist() :
        waterlist = []
        with open('waterlist_id.txt','r',encoding='utf-8') as f:
            line_msg = f.readline()
            while line_msg:
                waterlist.append({"id":int(line_msg),"count":0})
        with open("waterlist_count.txt",'r',encoding='utf-8') as f :
            line_msg = f.readline()
            index = 0
            while line_msg :
                waterlist[index]['count'] = int(line_msg)
        return waterlist

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
    
    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        """这是一个 hello world 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        yield event.plain_result(f"Hello, {user_name}, 你发了 {message_str}!") # 发送一条纯文本消息

    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    async def on_private_message(self, event: AstrMessageEvent):
        message_str = event.message_str # 获取消息的纯文本内容
        yield event.plain_result(f"你说的对，但是你为什么要给我私聊发消息，我这个功能还不知道写什么阿巴阿巴（这样吧我告诉你一个命令，你刚才发给我的消息是{message_str}）")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def water_in_group(self, event: AstrMessageEvent):
        """这里应该是一个打水的指令"""
        message_str = event.message_str # 获取消息的纯文本内容
        if not message_str == '打水' or event.get_group_id != "小流萤的亲友群" :
            logger.info(f"并没有触发打水的命令，爱来自群组{event.get_group_id}")
            return
        else :
            waterlist = self.create_waterlist()

            yield event.plain_result("打水成功！")

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
