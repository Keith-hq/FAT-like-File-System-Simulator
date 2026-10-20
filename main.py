"""
文件系统模拟器 —— 入口
======================
启动方式:
    python main.py              → 启动 GUI
    python main.py --cli        → 启动命令行模式
"""

import sys
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description='FAT 文件系统模拟器')
    parser.add_argument('--cli', action='store_true', help='命令行模式')
    parser.add_argument('--load', type=str, default='filesystem.img', help='加载磁盘映像')
    args = parser.parse_args()

    if args.cli:
        run_cli(args.load)
    else:
        from fs_gui import run_gui
        run_gui()


def _safe_print(*args, **kwargs) -> None:
    """安全打印，处理 Windows 控制台编码问题"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 降级：替换非 ASCII 字符
        text = ' '.join(str(a) for a in args)
        text = text.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8', errors='replace')
        print(text, **{k: v for k, v in kwargs.items() if k != 'file'})


def run_cli(load_file: str) -> None:
    """命令行交互模式"""
    # 尝试设置 UTF-8 编码
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    from fs_core import FileSystem
    from fs_commands import CommandParser

    fs = FileSystem()
    loaded = False
    try:
        loaded = fs.load(load_file)
    except OSError as e:
        _safe_print(f'[!] {e}')
    if not loaded:
        _safe_print('[!] 未找到磁盘映像，正在格式化新文件系统...')
        fs.format()
        _safe_print('[OK] 格式化完成。')

    cmd = CommandParser(fs)

    _safe_print(r"""
+======================================================================+
|         FAT 文件系统模拟器  (命令行模式)                              |
|         输入 help 查看命令列表，输入 exit 退出                        |
+======================================================================+
""")
    _safe_print(f'{fs.pwd()} $ ', end='', flush=True)

    try:
        for line in sys.stdin:
            line = line.strip()
            if line.lower() in ('exit', 'quit', 'q'):
                break
            output = cmd.execute(line)
            if output == '__CLEAR__':
                import os
                os.system('cls' if sys.platform == 'win32' else 'clear')
            elif output:
                _safe_print(output)
            _safe_print(f'{fs.pwd()} $ ', end='', flush=True)
    except (KeyboardInterrupt, EOFError):
        _safe_print('')

    fs.save(load_file)
    _safe_print(f'[OK] 文件系统已保存到 {load_file}。再见！')


if __name__ == '__main__':
    main()
