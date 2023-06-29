from datetime import datetime, timedelta, timezone

from apis.finance_data import get_kline
from apis.trade import make_order
from config import STRATEGY_NAME
from run_strategy import AccountContext
from utils import abspath
from utils.logger_tools import get_general_logger
from pprint import pprint

logger = get_general_logger(STRATEGY_NAME, path=abspath("logs"))


def main(context: AccountContext):
    # 股票代码
    # symbol = "SZ.000651"   #格力
    symbol= "SH.600519"     #贵州茅台
    # symbol = "300760"      #迈瑞
    # symbol= "SH.601318"       #中国平安
    # symbol= "SH.000001"    #上证指数
    # symbol= "SH.688339"  
    # symbol= "SZ.399001"    

    # 获取近144日K线数据
    kline_end = datetime.now(timezone(timedelta(hours=8)))
    kline_start = kline_end - timedelta(days=145) + timedelta(seconds=1)
    kline = get_kline(
        symbol,
        kline_start.strftime("%Y-%m-%d %H:%M:%S"),
        kline_end.strftime("%Y-%m-%d %H:%M:%S"),
        "1d",  # 天级
    )
    #pprint(kline)
    if len(kline) == 0:
        logger.warning(f"未查询到K线信息，请检查股票代码({symbol})或时间是否正确。若无误，请联系管理员。")
        return

    # 获取当前持仓
    pos_amount = sum(
        pos["amount"]
        for pos in filter(
            lambda pos: symbol == pos["symbol"], context.positions["avaliable"]
        )
    )
    logger.info(f"当前持仓：{pos_amount}")

    # 计算近5日均值
    ma_close = sum([info["close"] / len(kline) for info in kline])
    latest_close = kline[-1]["close"]
    diff_pct = round((latest_close - ma_close) * 100 / ma_close, 2)
    logger.info(f"平均: {ma_close}, 最新: {latest_close}, 差值: {diff_pct}%")

    # 样例策略
    max_pos_amount = 30000  # 最大持仓量

    # 买入
    buy_amount = 100  # 买入量（须为100的倍数）
    if (
        context.cash_avaliable > latest_close * buy_amount  # 现金充足
        and pos_amount + buy_amount <= max_pos_amount  # 交易后不超过最大持仓量
        and latest_close >= ma_close * 1.05  # 现价超过均价至少1%
    ):
        make_order(symbol, "market", "buy", buy_amount)
        logger.info(f"买入策略已执行")
        return

    # 卖出
    if pos_amount > max_pos_amount + 100:  # 实际持仓量大于最大持仓量100股
        sell_amount = (pos_amount - max_pos_amount) // 100 * 100  # 卖出超过阈值的持仓量（须为100的倍数）
        make_order(symbol, "market", "sell", sell_amount)
        logger.info(f"卖出策略已执行")
        return
