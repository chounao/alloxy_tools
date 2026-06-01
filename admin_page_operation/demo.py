import curses
import random
import time
import sys


def main(stdscr):
    # 初始化 curses
    curses.curs_set(0)  # 隐藏光标
    stdscr.nodelay(1)   # 非阻塞输入
    stdscr.timeout(50)  # 刷新延迟(毫秒)
    sh, sw = stdscr.getmaxyx()  # 获取屏幕尺寸
    w = curses.newwin(sh, sw, 0, 0)
    w.keypad(1)
    w.nodelay(1)

    # 启用颜色支持
    curses.start_color()
    # 初始化颜色对
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)

    # 要显示的文字，可以自定义
    text_chars = "Python满屏飘字效果ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"

    # 存储字符信息: (x, y, char, speed)
    chars = []

    while True:
        # 随机添加新字符
        if random.random() < 0.2:  # 控制生成频率
            x = random.randint(0, sw - 1)
            char = random.choice(text_chars)
            speed = random.randint(1, 3)  # 下落速度
            chars.append([x, 0, char, speed])

        # 清空屏幕
        w.erase()

        # 更新和绘制所有字符
        i = 0
        while i < len(chars):
            x, y, char, speed = chars[i]
            new_y = y + speed
            # 检查是否超出屏幕
            if new_y >= sh:
                chars.pop(i)
                continue
            chars[i][1] = new_y  # 更新 y 值
            # 边界检查
            if 0 <= new_y < sh and 0 <= x < sw:
                color = random.randint(1, 7)
                w.attron(curses.color_pair(color))
                try:
                    w.addch(new_y, x, char)
                except curses.error:
                    pass  # 忽略绘制错误
                w.attroff(curses.color_pair(color))
            i += 1

        # 处理按键退出
        key = w.getch()
        if key == ord('q'):
            break

        # 刷新屏幕
        w.refresh()
        time.sleep(0.05)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        sys.exit(0)
