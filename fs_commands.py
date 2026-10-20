"""
命令解析与执行模块
==================
提供面向文本终端的命令解析、执行与友好的错误提示。
"""

from __future__ import annotations

import shlex
import unicodedata
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

from fs_core import FileSystem, FAT_EOF


class CommandParser:
    """将用户输入映射到 FileSystem 方法"""

    def __init__(self, fs: FileSystem) -> None:
        self.fs = fs
        self._commands: Dict[str, Tuple[Callable, str, str]] = self._build_table()

    # ---- 帮助文本 -----------------------------------------------
    HELP = """
╔══════════════════════════════════════════════════════════════╗
║              文件系统模拟器 —— 命令帮助                       ║
╠══════════════════════════════════════════════════════════════╣
║  pwd                    显示当前工作目录                      ║
║  ls [-l]                列出目录内容（-l 详细信息）           ║
║  cd <path>              切换当前目录                          ║
║  mkdir <name>           创建目录                              ║
║  rmdir <name>           删除空目录                            ║
║  create <name> [size]   创建文件（size 单位：字节）           ║
║  delete <name>          删除文件                              ║
║  open <name>            打开文件                              ║
║  close <name>           关闭文件                              ║
║  write <name> <text>    向文件写入文本                        ║
║  read <name> [off] [n]  读取文件内容                          ║
║  stat <name>            显示文件详细信息                      ║
║  cp <src> <dst>         复制文件                              ║
║  mv <old> <new>         移动 / 重命名                         ║
║  find <pattern>         按名称搜索文件                        ║
║  tree                   显示目录树                            ║
║  df                     显示磁盘使用情况                      ║
║  format                 格式化文件系统（警告：清空所有数据）   ║
║  save [filename]        保存到磁盘映像                        ║
║  load [filename]        从磁盘映像恢复                        ║
║  help                   显示本帮助                            ║
║  clear                  清屏                                  ║
╚════════════════════════════════════════════════════════════════╝
"""

    # ====================== 命令注册 ============================

    def _build_table(self) -> Dict[str, Tuple[Callable, str, str]]:
        return {
            'pwd':    (self._pwd,    'pwd',                  '显示当前工作目录'),
            'ls':     (self._ls,     'ls [-l]',              '列出目录内容'),
            'cd':     (self._cd,     'cd <path>',            '切换目录'),
            'mkdir':  (self._mkdir,  'mkdir <dirname>',      '创建目录'),
            'rmdir':  (self._rmdir,  'rmdir <dirname>',      '删除空目录'),
            'create': (self._create, 'create <name> [size]', '创建文件'),
            'delete': (self._delete, 'delete <name>',        '删除文件'),
            'open':   (self._open,   'open <name>',          '打开文件'),
            'close':  (self._close,  'close <name>',         '关闭文件'),
            'write':  (self._write,  'write <name> <text>',  '写文件'),
            'read':   (self._read,   'read <name> [off] [n]','读文件'),
            'stat':   (self._stat,   'stat <name>',          '文件信息'),
            'cp':     (self._cp,     'cp <src> <dst>',       '复制文件'),
            'mv':     (self._mv,     'mv <src> <dst>',       '移动/重命名'),
            'find':   (self._find,   'find <pattern>',       '搜索文件'),
            'tree':   (self._tree,   'tree',                 '目录树'),
            'df':     (self._df,     'df',                   '磁盘使用'),
            'format': (self._format, 'format',               '格式化'),
            'save':   (self._save,   'save [filename]',      '保存'),
            'load':   (self._load,   'load [filename]',      '加载'),
            'help':   (self._help,   'help',                 '帮助'),
            'clear':  (self._clear,  'clear',                '清屏'),
        }

    # ====================== 公共入口 ============================

    def execute(self, line: str) -> str:
        """执行一行命令，返回输出字符串"""
        line = line.strip()
        if not line:
            return ''
        try:
            parts = shlex.split(line)
        except ValueError:
            return '❌ 命令解析错误：引号不匹配'
        cmd, *args = parts
        if cmd not in self._commands:
            return f'❌ 未知命令: {cmd}\n输入 "help" 查看可用命令。'
        try:
            return self._commands[cmd][0](args) or ''
        except FileNotFoundError as e:
            return f'❌ 未找到: {e}'
        except FileExistsError as e:
            return f'❌ 已存在: {e}'
        except IsADirectoryError as e:
            return f'❌ {e}'
        except NotADirectoryError as e:
            return f'❌ {e}'
        except OSError as e:
            return f'❌ {e}'
        except ValueError as e:
            return f'❌ 参数错误: {e}'
        except Exception as e:
            return f'❌ 错误: {type(e).__name__}: {e}'

    def get_commands(self) -> List[str]:
        return list(self._commands.keys())

    # ====================== 命令实现 ============================

    def _pwd(self, _: List[str]) -> str:
        return self.fs.pwd()

    @staticmethod
    def _disp_width(text: str) -> int:
        """按终端显示宽度计算长度：中文与 emoji 记 2 格"""
        width = 0
        for ch in text:
            if ch == '\ufe0f':          # 变体选择符不占位
                continue
            width += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
        return width

    @classmethod
    def _pad(cls, text: str, width: int, right: bool = False) -> str:
        """按显示宽度补齐空格"""
        gap = max(0, width - cls._disp_width(text))
        return (' ' * gap + text) if right else (text + ' ' * gap)

    def _ls(self, args: List[str]) -> str:
        detailed = '-l' in args
        path = next((a for a in args if not a.startswith('-')), '.')
        entries = self.fs.list_dir(path)

        if not entries:
            return '(空目录)'

        if not detailed:
            return '\n'.join(
                f"  {'📁' if e.is_dir else '📄'} {e.name}" for e in entries
            )

        rows = [('类型', '大小', '修改时间', '名称')]
        for e in entries:
            # 类型值用中文与表头保持一致：同字符集宽度才可预测，混用 ASCII 会错位
            t = '目录' if e.is_dir else '文件'
            sz = self.fs._fmt_size(e.size) if e.is_file else '-'
            mt = datetime.fromtimestamp(e.modify_time).strftime('%Y-%m-%d %H:%M:%S')
            rows.append((t, sz, mt, e.name))

        widths = [max(self._disp_width(r[i]) for r in rows) for i in range(4)]
        lines = []
        for idx, r in enumerate(rows):
            # 统一左对齐：中文表头与 ASCII 数据的实际像素宽不等，右对齐会让列边缘错位
            lines.append(
                f"{self._pad(r[0], widths[0])}  "
                f"{self._pad(r[1], widths[1])}  "
                f"{self._pad(r[2], widths[2])}  {r[3]}"
            )
            if idx == 0:
                lines.append('-' * (sum(widths) + 6))
        return '\n'.join(lines)

    def _cd(self, args: List[str]) -> str:
        if not args:
            return self.fs.pwd()
        path = args[0]
        new_path = self.fs.change_dir(path)
        return f'当前目录 → {new_path}'

    def _mkdir(self, args: List[str]) -> str:
        if not args:
            return '用法: mkdir <dirname>'
        self.fs.make_dir(args[0])
        return f'✅ 目录已创建: {args[0]}'

    def _rmdir(self, args: List[str]) -> str:
        if not args:
            return '用法: rmdir <dirname>'
        self.fs.remove_dir(args[0])
        return f'✅ 目录已删除: {args[0]}'

    def _create(self, args: List[str]) -> str:
        if not args:
            return '用法: create <filename> [size_bytes]'
        name = args[0]
        size = int(args[1]) if len(args) > 1 else 0
        self.fs.create_file(name, size)
        return f'✅ 文件已创建: {name}' + (f' ({self.fs._fmt_size(size)})' if size > 0 else ' (空文件)')

    def _delete(self, args: List[str]) -> str:
        if not args:
            return '用法: delete <filename>'
        self.fs.delete_file(args[0])
        return f'✅ 文件已删除: {args[0]}'

    def _open(self, args: List[str]) -> str:
        if not args:
            return '用法: open <filename>'
        self.fs.open_file(args[0])
        return f'✅ 文件已打开: {args[0]}'

    def _close(self, args: List[str]) -> str:
        if not args:
            return '用法: close <filename>'
        self.fs.close_file(args[0])
        return f'✅ 文件已关闭: {args[0]}'

    def _write(self, args: List[str]) -> str:
        if len(args) < 2:
            return '用法: write <filename> <content>'
        name = args[0]
        content = ' '.join(args[1:])
        n = self.fs.write_file(name, content.encode('utf-8'))
        return f'✅ 已写入 {n} 字节 → {name}'

    def _read(self, args: List[str]) -> str:
        if not args:
            return '用法: read <filename> [offset] [length]'
        name = args[0]
        offset = int(args[1]) if len(args) > 1 else 0
        length = int(args[2]) if len(args) > 2 else None
        data = self.fs.read_file(name, offset, length)
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            text = repr(data)
        size = self.fs._fmt_size(len(data))
        return f'--- {name} ({size}) ---\n{text}\n---  EOF ---'

    def _stat(self, args: List[str]) -> str:
        if not args:
            return '用法: stat <filename>'
        e = self.fs.stat_file(args[0])
        lines = [
            f'名称:     {e.name}',
            f'类型:     {"目录" if e.is_dir else "文件"}',
            f'起始块:   {e.first_block if e.first_block != FAT_EOF else "N/A"}',
            f'大小:     {self.fs._fmt_size(e.size)} ({e.size} 字节)',
            f'创建时间: {datetime.fromtimestamp(e.create_time).strftime("%Y-%m-%d %H:%M:%S")}',
            f'修改时间: {datetime.fromtimestamp(e.modify_time).strftime("%Y-%m-%d %H:%M:%S")}',
        ]
        return '\n'.join(lines)

    def _cp(self, args: List[str]) -> str:
        if len(args) < 2:
            return '用法: cp <source> <dest>'
        self.fs.copy_file(args[0], args[1])
        return f'✅ 已复制: {args[0]} → {args[1]}'

    def _mv(self, args: List[str]) -> str:
        if len(args) < 2:
            return '用法: mv <old> <new>'
        self.fs.move_file(args[0], args[1])
        return f'✅ 已移动: {args[0]} → {args[1]}'

    def _find(self, args: List[str]) -> str:
        if not args:
            return '用法: find <pattern>'
        results = self.fs.search_files(args[0])
        if not results:
            return f'未找到匹配 "{args[0]}" 的文件。'
        return '\n'.join(results)

    def _tree(self, _: List[str]) -> str:
        def _render(node: dict, prefix: str = '', is_last: bool = True) -> List[str]:
            lines: List[str] = []
            connector = '└── ' if is_last else '├── '
            # 目录用结尾斜杠区分，不依赖 emoji 字体（部分终端字体缺 emoji 会显示成方块）
            suffix = '/' if node['type'] == 'dir' else ''
            lines.append(f"{prefix}{connector}{node['name']}{suffix}")
            if node['type'] == 'dir' and node.get('children'):
                child_prefix = prefix + ('    ' if is_last else '│   ')
                children = node['children']
                for i, child in enumerate(children):
                    lines.extend(_render(child, child_prefix, i == len(children) - 1))
            return lines

        tree = self.fs.get_tree()
        lines = ['/']
        children = tree.get('children', [])
        for i, child in enumerate(children):
            lines.extend(_render(child, '', i == len(children) - 1))
        return '\n'.join(lines)

    def _df(self, _: List[str]) -> str:
        total, used, free = self.fs.disk_usage()
        pct = used / total * 100 if total > 0 else 0
        bar_len = 40
        filled = int(bar_len * used / total) if total > 0 else 0
        bar = '█' * filled + '░' * (bar_len - filled)
        lines = [
            f'文件系统:   FAT-SIM',
            f'总容量:     {self.fs._fmt_size(total)}',
            f'已使用:     {self.fs._fmt_size(used)}  ({pct:.1f}%)',
            f'可用:       {self.fs._fmt_size(free)}',
            f'[{bar}]',
        ]
        return '\n'.join(lines)

    def _format(self, _: List[str]) -> str:
        self.fs.format()
        return '✅ 文件系统已格式化。'

    def _save(self, args: List[str]) -> str:
        filename = args[0] if args else 'filesystem.img'
        self.fs.save(filename)
        return f'✅ 已保存到 {filename}'

    def _load(self, args: List[str]) -> str:
        filename = args[0] if args else 'filesystem.img'
        if self.fs.load(filename):
            return f'✅ 已从 {filename} 加载。'
        return f'❌ 文件不存在: {filename}'

    def _help(self, _: List[str]) -> str:
        return self.HELP

    def _clear(self, _: List[str]) -> str:
        return '__CLEAR__'  # 特殊信号
