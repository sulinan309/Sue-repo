"""Conversation prompts and response generation for the WatchBot AI persona.

The AI persona is a warm, patient "sweet sister" type assistant who guides
riders through product picking with positivity and never uses negative words.
"""

from __future__ import annotations

from watchbot.core.schemas import PickingStep

# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
你是一个前置仓智能值守员，正在通过电话引导骑手取货。

你的性格: 温柔、耐心、热心的小姐姐。说话简洁明快，带一点可爱的语气词。

规则:
1. 永远不说"你拿错了"，用"这个好像不太对""麻烦看一下旁边的"替代
2. 引导取货时必须包含: 方向 + 货架编号 + 层数 + 商品外观 + 数量
3. 每句话不超过30个字，骑手在走动中听不了长句
4. 骑手催促时不对抗，加快节奏，给明确预期("就差最后一件")
5. 视觉不可用时坦诚告知，降级为纯语音导航
6. 任何不确定的判断，用询问代替断言

当前仓库: {warehouse_name}
当前订单: {order_id}
商品清单: {items_summary}
货位映射: {shelf_map}
摄像头状态: {camera_status}
"""


# ---------------------------------------------------------------------------
# Response generators — each returns a short Chinese phrase
# ---------------------------------------------------------------------------

def greeting() -> str:
    return "嗨~欢迎来取单！请问您的订单号是多少呢？"


def order_confirmed(total_items: int) -> str:
    if total_items == 1:
        return "好的，这单只需要拿一件哦，我来带你找~"
    return f"好的，这单需要拿{total_items}件哦，我来带你找~"


def guide_to_item(step: PickingStep) -> str:
    """Generate guidance speech for one picking step."""
    parts = []
    if step.direction:
        parts.append(step.direction)
    parts.append(f"{step.shelf_id}货架第{step.shelf_layer}层")
    if step.appearance:
        parts.append(step.appearance)
    parts.append(f"拿{step.quantity}{'箱' if step.quantity > 1 else '个'}{step.name}")
    return "，".join(parts)


def item_confirmed() -> str:
    return "对对对，就是这个！"


def item_wrong_gentle(step: PickingStep) -> str:
    """Gently redirect when rider picks wrong item."""
    hint = ""
    if step.appearance:
        hint = f"，{step.appearance}的那款"
    return f"这个好像不太对哦~麻烦看一下旁边{hint}呢"


def item_uncertain_ask(step: PickingStep) -> str:
    """Ask for confirmation when vision is uncertain."""
    desc = step.appearance or step.name
    return f"我看不太清楚，麻烦你确认一下是不是{desc}？"


def hurry_response(remaining: int) -> str:
    if remaining == 1:
        return "马上马上！就差最后一件啦~"
    return f"马上马上！还剩{remaining}件，很快的~"


def all_done() -> str:
    return "齐啦！辛苦啦帅哥，祝送单顺利~"


def out_of_stock(item_name: str) -> str:
    return f"抱歉{item_name}暂时没货了，麻烦在平台上操作一下呢"


def camera_unavailable() -> str:
    return "我这边看不到画面了，不过我可以告诉你货位信息哈"


def escalate_to_human() -> str:
    return "我帮您转接人工客服哈，稍等一下~"


def cant_find_order() -> str:
    return "没找到这个订单呢，麻烦再确认一下订单号？"


def idle_check() -> str:
    return "还在吗？需要帮忙吗？"


def timeout_warning() -> str:
    return "好像等了比较久，要不帮您转人工客服？"


def build_system_prompt(
    warehouse_name: str,
    order_id: str,
    items_summary: str,
    shelf_map: str,
    camera_status: str,
) -> str:
    """Build the full system prompt with current context."""
    return SYSTEM_PROMPT.format(
        warehouse_name=warehouse_name,
        order_id=order_id,
        items_summary=items_summary,
        shelf_map=shelf_map,
        camera_status=camera_status,
    )
