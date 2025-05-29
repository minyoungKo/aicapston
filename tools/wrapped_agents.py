import json
from agents.stock_info_collector_agent import invoke_stock_info_collector as real_invoke_stock_info_collector
from agents.news_agent import invoke_news_analyzer as real_invoke_news_analyzer
from agents.chart_agent import invoke_chart_analyzer as real_invoke_chart_analyzer
from agents.fundamental_agent import invoke_fundamental as real_invoke_fundamental

async def _extract_output(result: str) -> str:
    try:
        parsed = json.loads(result)
        return parsed.get("output", result)
    except json.JSONDecodeError:
        return result

async def invoke_stock_info_collector(user_input: str) -> str:
    return await _extract_output(await real_invoke_stock_info_collector(user_input))

async def invoke_news_analyzer(user_input: str) -> str:
    return await _extract_output(await real_invoke_news_analyzer(user_input))

async def invoke_chart_analyzer(user_input: str) -> str:
    return await _extract_output(await real_invoke_chart_analyzer(user_input))

async def invoke_fundamental(user_input: str) -> str:
    return await _extract_output(await real_invoke_fundamental(user_input))
