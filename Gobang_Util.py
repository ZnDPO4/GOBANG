# -*- coding: UTF-8 -*-

def simple_situation_analysis(field):
    """局势分析函数 只返回首要状态

    根据盘面状态分析是否有禁手、是否有人获胜
    对于 SimpleChessType 判断的优先级上，长连 > 五连 > 其他禁手
    Args:
        filed: 15*15二维数组 棋盘

    Returns:
        返回一个(ChessColor, ChessType)类型元组
        第一个元素代表触发这个状态的主体（ChessColor）
        第二个元素代表当前最首要的局势（SimpleChessType）

        {'Serak': ('Rigel VII', 'Preparer'),
         'Zim': ('Irk', 'Invader'),
         'Lrrr': ('Omicron Persei 8', 'Emperor')}

        If a key from the keys argument is missing from the dictionary,
        then that row was not found in the table.

    Raises:
        无
    """

    # TODO
    pass

def full_situation_analysis(field):
    # TODO
    pass